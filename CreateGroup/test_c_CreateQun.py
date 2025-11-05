import ast
import datetime
import logging
import os
from common import robot_api
from common.Log import Logger
from common.robot_api import GetUserId, get_all_no_guiDang, get_current_owner, other_group
from common.YamlUtil import read_yaml_special
from common.RedisConfig import r


def generate_group_name(time, group, type_dan, gary, all_gary, group_name, belong_bu):
    """生成群组名称逻辑"""
    base_name = f"【{time}】{group_name}"

    if type_dan == "加急" and gary in all_gary:
        prefix = f"[S-灰度-{belong_bu}]" if gary in all_gary else f"[S-{belong_bu}]"

    elif gary in all_gary:
        prefix = f"[灰度-{belong_bu}]"
    
    elif type_dan == "加急":
        prefix = f"[S-{belong_bu}]"
    
    elif type_dan == "紧急" and "公域业务组" in group:
        prefix = f"[公域-{belong_bu}]"

    else:
        prefix = f"[A-{belong_bu}]"

    return f"{prefix} {base_name}" if prefix else f" {base_name}"


def part_gary(code, app_id, groupName, link):
    """代码级灰度、评论逻辑"""
    compare_gary = []
    send_url = []
    judge_comment = r.lrange('is_comment_codeGary', 0, -1)
    code_gary = ''
    res_code_gary = robot_api.app_id_CodeGary(app_id)
    e_all = res_code_gary['data']['e_list']
    if e_all:
        # 评论代码级灰度
        for idx, cd in enumerate(e_all):
            code_gary = code_gary + f"{idx}、{cd['e_name']}\n"
        try:
            if code not in judge_comment:
                robot_api.comment_dan(code, f'该商家在以下代码级灰度中：\n{code_gary}')
                r.rpush('is_comment_codeGary', code)
            else:
                Logger.debug(f"{groupName}   的代码级灰度已评论过了")
        except Exception:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"<font color=\"warning\">重新配置coding单评论接口<@qiulinqian></font>\n\n"
                }
            }
            robot_api.robot_app(data)

            # 监控代码级灰度
        for dh in e_all:
            if code not in judge_comment:
                for idx, gary_name in enumerate(compare_gary):
                    Logger.debug(f"e_name和gary_name分别为 {dh['e_name']}   {gary_name}")
                    if dh['e_name'] == gary_name:
                        data = {
                            "msgtype": "markdown",
                            "markdown": {
                                "content": f"<font color=\"warning\">**有新的代码级灰度工单啦**</font>\n\n"
                                           + f"\n**工单：**\n[{groupName}]({link})\n"
                            }
                        }
                        other_group(data, send_url[idx])
                    else:
                        pass
            else:
                pass
    else:
        code_gary = '这个商家没有在任何代码级灰度中'
    Logger.debug(f'{groupName}的代码级灰度为：{code_gary}')
    return code_gary


def get_gary(code, dan_id, gary1, groupName, link):
    if code == dan_id:
        if gary1:
            gary_one = gary1
            if '灰度客户' in gary1:    
                gary = gary_one.replace("灰度客户-", "") if "灰度客户-" in gary_one else gary_one
            else:
                gary = gary_one
        else:
            gary = "无灰度信息"
    else:
        gary = "本单灰度信息请前往工单查看"
    Logger.debug(f"{groupName}的灰度信息为   {gary}")
    return gary


def get_creator_UserProcess_doPerson(app_id, groupName, tiDan, service_people, do_people_list, submit_person):
    """获取创建人、客户经理、处理人"""
    # 客户经理
    res = robot_api.get_project_master(app_id)
    if res:
        service_people.append(res)
        Logger.debug(f"{groupName}的客户经理为：   {res}")
    else:
        res = "无客户经理"
        Logger.debug(f"{groupName}   无客户经理")

    # 创建人
    if tiDan not in ["None","API调用"] and tiDan in service_people:
        creator = tiDan
        Logger.debug(f"{groupName}    提单人已入群")
    elif tiDan not in ["None","API调用"] and tiDan not in service_people:
        creator = tiDan
        service_people.append(tiDan)
    else:
        creator = submit_person  
        if creator not in service_people and creator != '':
            service_people.append(creator)
        else:
            pass

    # 处理人
    if ";" in do_people_list:
        name = do_people_list.split(";")
        for n in name:
            if n not in service_people and n != '':
                service_people.append(n)
    elif do_people_list == '':
        name = ["无处理人"]
    else:
        if do_people_list not in service_people:
            service_people.append(do_people_list)
        name = [do_people_list]
    
    Logger.debug(f'{groupName}的处理人为： {name}')
    return res, creator, name, service_people


def first_message(name, groupName, link, typeDan, create_people, res, gary, code_gary, number, belong_bu):
    """构建新建群聊后的第一句话"""
    if 'KA' in belong_bu:
        belong_bu_info = f"该工单所属BU为：{belong_bu}    请1小时内处理完毕"
    else:
        belong_bu_info = f"该工单所属BU为：{belong_bu}    请24小时内处理完毕"
    first_msg = groupName + "\n\n" + f"工单链接: {link}" + "\n\n" + f"紧急程度: {typeDan}" + "\n\n" + f"创建人: @{create_people}\n\n" + f"处理人: @{name[0]}\n\n" + f"客户经理：@{res}\n\n" + f"灰度信息：{gary}\n\n" + f"代码级灰度：{code_gary}\n\n" + f"👉{belong_bu_info}👈"
    return first_msg


def send_inter_msg(bugType, typeDan, gary, all_gary, group, Name, number, name):
    # 获取已通知的群id
    remind = r.lrange('remind', 0, -1)
    Logger.debug(f"已经发送提醒到内部群的有:   {remind}")

    # 判断那些群聊没有通知
    all_dan1 = r.lrange('is_create', 0, -1)
    Logger.debug(f"已经拉群的单有:    {all_dan1}")

    if typeDan == "加急":
        send_name = "有新的加急工单,已拉群！"
    elif typeDan == "紧急" and "课程" in group:
        send_name = "课程有新工单,已拉群！"
    elif gary in all_gary:
        send_name = "有新灰度工单,已拉群！"
    else:
        send_name = "有新工单，已拉群！"

    for i in all_dan1:
        if i == '1':
            continue
        for rid in remind:
            if rid == i:
                cc = 1
                break
        if cc == 1:
            Logger.debug(f"{Name}   群聊已通知")
            cc = 0
        else:
            send_notification(send_name, Name, number, name)
            Logger.debug("新建群聊已通知")
            r.rpush("remind", i)


def send_notification(send_name, Name,number, name):
    """统一发送通知逻辑"""
    content = GetUserId(name, [])[0]
    markdown = {
        "content": f"<font color=\"warning\">{send_name}</font>\n\n"
                   f"**工单名称：**{Name}\n\n"
                   f"**相关处理人：**{content}\n\n"
                   f"**近30天累计提单：**{number}次"
    }
    robot_api.robot_app({"msgtype": "markdown", "markdown": markdown})


def test_getAllDan():
    try:
        # 查询所有计划灰度
        plans = get_all_no_guiDang(0, "", "", "教培产品", "")
        all_gary = plans[1]
        Logger.debug(f"所有教培的项目灰度为：  {all_gary}")

        # 项目助手中的工单id
        dan_id = os.getenv("ISSUE_ID")
        Logger.debug(f"新建工单id为：  {dan_id}\n")

        # 项目助手中的灰度信息
        gary1 = os.getenv("GRAY_FROM")
        Logger.debug(f"工单灰度：  {gary1}\n")

        # 获取标签
        tag = os.getenv("ISSUE_TAG")
        Logger.debug(f"工单标签：  {tag}\n")

        # 获取问题处理所属中心
        group = os.getenv("ISSUE_OWNER_GROUP")
        Logger.debug(f"工单处理人所属小组：  {group}\n")

        # 查询出redis中的差异单的数据，类型为string
        dan = ast.literal_eval(r.get('diff'))

        if len(dan or []) != 0:

            # 循环查询出每一个工单信息
            for item in dan:

                if item == '1':
                    continue

                # 将string类型转换为list类型
                real_dan = ast.literal_eval(item)
                Logger.debug(f"正在进行判断拉群的工单：   {real_dan}")

                # 工单id
                code = str(real_dan[0])
                Logger.debug(f"正在进行判断拉群工单code为：{code}")

                # 工单名称
                groupName = real_dan[1]

                # 创建人
                tiDan = str(real_dan[4])

                # 店铺提单数
                number = real_dan[8]

                # 工单紧急状态
                typeDan = str(real_dan[3])

                # 缺陷类型
                bugType = real_dan[6]

                app_id = real_dan[5]

                # 工单提单人
                submit_person = real_dan[7]

                # 工单处理人
                do_people_list = str(real_dan[2])

                # 拼接工单链接
                link = "https://xiaoe.coding.net/p/xianwangjishugongdan/bug-tracking/issues/" + code + "/detail"

                send_msg_to_other_group(gary1, link, groupName)

                # 获取service_people
                if group is None or group == '':
                    service_people = read_yaml_special("/scrm_service_people.yaml")
                    group = "AIO平台中心"
                elif '教培产品中心' in group:
                    service_people = read_yaml_special("/service_people.yaml")
                elif 'AIO平台中心' in group:
                    service_people = read_yaml_special("/scrm_service_people.yaml")
                

                if tag:
                    if tag == "出海":
                        service_people += ['phoebefang(方静丽)', 'jacobli(李杨)', 'reesezhang(张继章)', 'ryankuang(邝锐聪)', 'alicehu(胡思婷)', 'cicizeng(曾清明)', 'tracyliu(刘敏珊)', 'xiaoyujiang(江小鱼)', 'wadezhang(张伟)', 'rongzhuangwu(吴荣壮)', 'zeecoli(李显鹏)', 'veegeehong(洪丽丽)', 'larakichen(陈嘉琪)', 'caciquefeng(冯玥茜)', 'bettychen(陈可璇)', 'vinceyu(喻千里)', 'cclin(林丹红)', 'serenaxiang(向云霞)']
                    else:
                        pass    
                Logger.debug(f"service_people_first为{service_people}")


                # 查询代码级灰度
                codeGary = part_gary(code, app_id, groupName, link)

                # 创建人、客户经理、处理人
                res, creator, name, service_people = get_creator_UserProcess_doPerson(app_id, groupName, tiDan,
                                                                                      service_people,
                                                                                      do_people_list, submit_person)
                # 需要@的人
                mentionPerson = []
                if res != "无客户经理":
                    mentionPerson.append(res)
                if creator != "Api创建":
                    mentionPerson.append(creator)
                if name != ["无处理人"]:
                    mentionPerson.extend(name)                
                Logger.debug(f'需要@的人有： {mentionPerson}')

                # 计划灰度
                gary = get_gary(code, dan_id, gary1, groupName, link)

                time = datetime.datetime.now().date().strftime("%m-%d")
                
                # 获取工单BU
                belong_bu = get_current_owner(groupName)

                # 群名
                Name = generate_group_name(time, group, typeDan, gary, all_gary, groupName, belong_bu)

                # 发送的第一条消息
                first_msg = first_message(name, groupName, link, typeDan, creator, res, gary, codeGary,
                                          number, belong_bu)

                # 查redis中已经拉群数据
                all_dan = r.lrange('is_create', 0, -1)
                r.ttl("is_create")

                # 判断该单是否已拉群
                if code in all_dan:
                    dd = 1
                else:
                    dd = 0
                Logger.debug(f"dd={dd}   判断是否已拉群  dd=1为已拉群，dd=0为未拉群")

                if dd == 0 and (gary in all_gary or typeDan == "加急" or ("公域" in group and typeDan == "紧急")):
                    res = robot_api.new_create_group(int(code), Name, first_msg, service_people, mentionPerson)
                    Logger.debug(res.json())
                    r.rpush("is_create", code)
                elif dd == 0 and 'AIO平台中心' in group:
                    res = robot_api.new_create_group(int(code), Name, first_msg, service_people, mentionPerson)
                    Logger.debug(res.json())
                    r.rpush("is_create", code)
                elif dd == 0 and tag == "出海":
                    res = robot_api.new_create_group(int(code), Name, first_msg, service_people, mentionPerson)
                    Logger.debug(res.json())
                    r.rpush("is_create", code)
                else:
                    Logger.debug(f"{groupName}   已经拉群了")
                send_inter_msg(bugType, typeDan, gary, all_gary, group, Name, number, name)
    except Exception as e:
        Logger.error(f"异常：{e}")


# 发送消息到其它的群聊
def send_msg_to_other_group(gary, link, name):
    # 发送消息到其它群聊的信息
    compare_gary = ast.literal_eval(os.getenv("COMPARE_GRAY"))
    worker = ast.literal_eval(os.getenv("WORKER"))
    Logger.debug(f"获取发送到其它群的配置信息：  {compare_gary}")
    if len(compare_gary) == 1 and compare_gary[0] == '':
        pass
    else:
        for index, i in enumerate(compare_gary):
            workers = " ".join(one_worker for one_worker in worker[index])

            if i in gary:
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"<font color=\"warning\">**有新的灰度工单啦**</font>\n\n"
                                   + f"\n**工单：**\n[{name}]({link})\n"
                                   + f"\n{workers}"
                    }
                }
                robot_api.robot_send_to_other_group(data, index)
            else:
                pass
