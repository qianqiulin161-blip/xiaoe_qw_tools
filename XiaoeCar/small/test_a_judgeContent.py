import ast
import logging
import re
from typing import Dict, List
from common.RedisConfig import r
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from common.robot_api import smallCar_getDan, robot_smallCar, get_in_plan_one_detail,  GetUserId
import allure

# 判断的标题有哪些
title = ["1.项目影响范围（说明项目影响的功能/模块，涉及内容输入需接入内容审核组件【对接人：朱开发】）",
         "2.开发自测结果（必填：提供开发自测结果，最好可贴图）",
         "3.代码截图（必填）",
         "4.变更代码 AI review截图",
         "5.测试说明（例：代码逻辑中是否涉及缓存问题会影响测试结果）",
         "6.接口变更列表。(eolink 链接)",
         "7.系统依赖图",
         "7.是否需要接入业务监控字段。",
         "8.上线系统代码是否需要发布海外(是/否)。",
         "9.上线系统代码是否已回国/代码是否已合master（是/否）。"
         ]


def _get_cached_data(key: str) -> List[Dict]:
    """通用数据获取方法"""
    return ast.literal_eval(r.get(key)) if r.get(key) else []


def _create_message(name: str, url: str, title: str, creator: str, reason: str) -> Dict:
    """构建消息模板"""
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"{reason}\n"
                       f"**工单：**[{name}]({url})    {GetUserId([creator], [])[0]}\n\n"
                       f"**标题：**{title}"
        }
    }


def _check_self_test(content: str) -> bool:
    """检查自测结果合规性"""
    # 对原始字符串执行去两端空白符操作（strip），并将所有字符转为小写（lower）
    content = content.strip().lower()
    Logger.debug(f"自测结果内容长度：{len(content)}")
    return True if len(content) > 15 else False


@allure.title("判断工单填写的内容是否符合要求")
def test_judgeContent():
    # 移除之前符合要求的小车单，设置新的符合要求的小车单
    data = smallCar_getDan()
    raw_data = [item for item in data for department in smallConfig.OrderType if department in item['department_id']]
    r.set(smallConfig.department_config[0], str(raw_data))
    r.persist(smallConfig.department_config[0])
    Logger.debug(f"查询出的所有小车工单：{raw_data}")

    # 内容有问题需要发消息提醒的单id
    error_id = []
    # 记录已经提醒过的问题id
    new_error_done = []
    # 查出已发送问题提醒的单
    error_done = _get_cached_data(smallConfig.department_config[1])
    Logger.debug(f"判断小车工单又不符合捞单规定且提醒过的单：  {error_done}")

    if len(raw_data) == 0:
        Logger.info("没有数据展示不判断内容")
        return

    for item in raw_data:
        # 获取工单id、工单名称、工单链接、工单创建人
        titles, TestSelf = [], []
        item_id = str(item.get("iteration_id"))
        identifier = f"{item_id}judgeContent"
        name, url1, creator = item.get("iteration_name"), item.get("coding_order_url"), \
            item.get("creator")
        Logger.debug(f"工单创建人为： {creator}")

        res = get_in_plan_one_detail(item_id).json()
        # 每个单当中的内容
        content = res["data"].get("iteration_content", "")

        for i in range(9):  # 优化循环次数
            curr_title, next_title = title[i], title[i + 1]
            start = content.find(curr_title)
            end = content.find(next_title)

            if -1 in (start, end):
                continue

            section = content[start + len(curr_title):end].strip()
            Logger.debug(f"标题与标题之间的内容：  {section}   {len(section.strip().lower())}")
            image_urls = re.findall(r'!\[.*?\]\((.*?)\)', section)
            # 图片检查分支
            if image_urls:
                Logger.debug(f"{name} {curr_title} 包含图片通过！")
                continue
            # 自测结果特殊处理
            if i == 1:
                if _check_self_test(section) is False and identifier not in error_done:
                    titles.append(curr_title)
                    new_error_done.append(identifier)
                    error_id.append(raw_data.index(item))
                    TestSelf.append(1)
                elif _check_self_test(section) is False and identifier in error_done:
                    new_error_done.append(identifier)
                    error_id.append(raw_data.index(item))
            elif i == 8:
                if len(section.strip().lower()) == 8 and identifier not in error_done:
                    titles.append(curr_title)
                    new_error_done.append(identifier)
                    error_id.append(raw_data.index(item))
                    TestSelf.append(8)
                elif len(section.strip().lower()) == 8 and identifier in error_done:
                    new_error_done.append(identifier)
                    error_id.append(raw_data.index(item))
                
            # 常规内容检查
            elif len(section.strip().lower()) < 9 and identifier not in error_done:
                titles.append(curr_title)
                new_error_done.append(identifier)
            elif len(section.strip().lower()) < 9 and identifier in error_done:
                new_error_done.append(identifier)

        if len(titles) != 0 and 1 in TestSelf and 8 in TestSelf:
            robot_smallCar(_create_message(name, url1, '\n'.join(t for t in titles), creator,
                                           "<font color='red'>**自测无贴图/描述简单\n【上线系统代码是否需要发布海外(是/否)】未填写\n不予加计划，请解决上面两个问题！！**</font>  其余工单内容描述简单，请完善"), smallConfig.robotWebHook)
        elif len(titles) != 0 and 8 in TestSelf:
            robot_smallCar(_create_message(name, url1, '\n'.join(t for t in titles), creator,
                                           "<font color='red'>**【上线系统代码是否需要发布海外(是/否)】未填写,不予加计划！！**</font>  其余工单内容描述简单，请完善"), smallConfig.robotWebHook)
        elif len(titles) != 0 and 1 in TestSelf:
            robot_smallCar(_create_message(name, url1, '\n'.join(t for t in titles), creator,
                                           "<font color='red'>**自测无贴图/描述简单,不予加计划！！**</font>  其余工单内容描述简单，请完善"), smallConfig.robotWebHook)
        elif len(titles) != 0 and len(TestSelf) == 0:
            robot_smallCar(_create_message(name, url1, '\n'.join(t for t in titles), creator,
                                           "工单内容描述简单，请完善"), smallConfig.robotWebHook)
            
    r.set(smallConfig.department_config[1], str(new_error_done))
    r.set(smallConfig.department_config[2], str(error_id))
