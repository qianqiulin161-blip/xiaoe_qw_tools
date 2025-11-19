import ast
import os
from datetime import datetime
from XiaoeCar.same.at_person import at, at_tester, at_driver
from XiaoeCar.same.test_SelfRun_API_UI import run_automation
from XiaoeCar.same.Same import build_plan, get_upload_appId_system_statu, up_appId, HadAppId
from common.Exception import catch_exception
from common.RedisKey import RedisKeyManager
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from common.robot_api import batch_merge, find_api, get_in_plan_one_detail, in_plan, ready_line, robot_smallCar, \
    get_plan_detail, GetUserId
from XiaoeCar.same.SelfRun_API_UI_Enum import MessageTemplate
from common.RedisConfig import r
from tenacity import retry, stop_after_attempt, wait_fixed

# 设置最大重试次数，这里设置为3次，你可以根据实际情况调整
MAX_ATTEMPTS = 3
# 设置重试间隔时间（单位：秒），这里设置为5秒，同样可按需调整
RETRY_INTERVAL = 3

# 准现网验证报告生成
def _generate_alert_message(plan_name, total_dan, down_count, final, ui_final, pid):
    if r.get(RedisKeyManager().get_key('PlanContent')):
        res_plan_content = in_plan(pid).json()['data']['list']
        now_names = []
        for i in res_plan_content:
            now_names.append(i['iteration_id'])
        last_names = ast.literal_eval(r.get(RedisKeyManager().get_key('PlanContent')))
        if total_dan > down_count:
            down_content = ''
            real_names = list(set(last_names) - set(now_names))
            # 循环获取以下车小车的信息
            for i in real_names:
                real_info = get_in_plan_one_detail(i).json()['data']
                down_content += f"【{real_info['iteration_name']}】  请确认是否合并代码，合并代码是否回退   {GetUserId([real_info['creator']], [])[0]}\n\t\t\t"
        else:
            down_content = '无下车小车'
    else:
        down_content = '无下车小车'

    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"**【{plan_name}准现网报告】** {at_tester}\n"
                       f"**【计划内容】：** \n"
                       f"      已发布： {down_count}\n"
                       f"      已下车： {total_dan - down_count if total_dan > down_count else 0}\n"
                       f"\t\t\t{down_content}\n"
                       f"**【人工验证结果】：** PASS\n"
                       f"**【接口自动化执行结果】** \n{final}\n"
                       f"**【UI自动化执行结果】** \n{ui_final}"
        }
    }


# 发布准现网报告逻辑、 自动添加外灰名单逻辑
@retry(stop=stop_after_attempt(MAX_ATTEMPTS), wait=wait_fixed(RETRY_INTERVAL),
       reraise=True)
def _process_plan(plan_id, redis_key, plan_type_str, taskId):
    response = in_plan(plan_id)
    plan_detail = get_plan_detail(plan_id)
    if response.status_code != 200 or response.json()["code"] != 0:
        Logger.debug("获取计划中迭代信息失败")
        return

    result = response.json()
    target_list = [item["iteration_id"] for item in result["data"]["list"]]
    valid_count = sum(1 for item in result["data"]["list"] if item["coding_order_stage_text"] in
                      ["允许全网", "版本已全网", "允许进行外灰"])
    if r.get(redis_key) is None:
        r.set(redis_key, "['1']")
        return

    content = ast.literal_eval(r.get(redis_key))
    if "1" in content:
        content.remove("1")
    
    Logger.debug(f"计划总车数{len(result['data']['list'])}, 有效车数{valid_count}, redis内容{content}, 目标内容{target_list}")
    if not (set(content) == set(target_list) or len(result["data"]["list"]) != valid_count):
        from XiaoeCar.same.test_SelfRun_API_UI import SelfRunAPIUI
        runner = SelfRunAPIUI(plan_id)

        # 接口自动化结果
        final_content = runner._get_api_results()['content']

        # UI自动化结果
        ui_final = [runner._get_ui_status(ui) for ui in runner.Self['ui']]
        ui_final_content = '\n'.join(f"{j['department']}UI自动化: {j['status']}  报告：[{j['report']}]({j['report']})" for j in ui_final)

        alert_data = _generate_alert_message(plan_detail.json()['data']['plan_name'], int(r.get(RedisKeyManager().get_key('DanNum'))),
                                             len(response.json()['data']['list']), final_content, ui_final_content, plan_id)
        robot_smallCar(alert_data, smallConfig.robotWebHook)
        r.set(redis_key, str(target_list))
        
    # 国内准现网自动添加外灰名单
    add_outside_gray(plan_id, valid_count, result, "国内-准现网", smallConfig.AddAppIdList, [131], "xiaoetong-pro", RedisKeyManager().get_key('OutsideGrayIndex'), taskId)
        
    # 国外准现网自动添加外灰名单
    if taskId.get('海外-准现网'):
        if build_plan(plan_id, taskId['海外-准现网']):
            add_outside_gray(plan_id, valid_count, result, "海外-准现网", smallConfig.OverseasAddAppIdList, [130], "elink-pro", RedisKeyManager().get_key('OverseaGrayIndex'), taskId)
    Logger.debug(f"{plan_type_str}: {target_list}, {valid_count}")



    # 自动添加外灰名单
def add_outside_gray(plan_id, valid_count, result, environment, appId_list, label_id, culster_id, redis_index, taskId):
    now = datetime.now()
    PM_start = now.replace(hour=16, minute=30, second=0, microsecond=0)
    PM_end = now.replace(hour=17, minute=30, second=0, microsecond=0)
    Night_start = now.replace(hour=22, minute=0, second=0, microsecond=0)
    index = int(r.get(redis_index))
    Logger.debug(f'当前外灰名单添加index为:{index}')

    if taskId.get(environment) and len(appId_list) != 0 and (PM_start < now < PM_end or now > Night_start) and index+1 <= len(appId_list):
        is_success = get_upload_appId_system_statu(plan_id, taskId[environment], "有系统发布失败  请检测！！",
                                                at_tester, at_driver, smallConfig.robotWebHook, '小车计划')
        if len(result["data"]["list"]) == valid_count and index < 4 and is_success is True and PM_start < now < PM_end:
            if _control_add_appid():
                up_appId(taskId[environment], appId_list[index], [], plan_id, label_id, culster_id, environment)
                r.set(redis_index, str(index + 1))
        elif len(result["data"]["list"]) == valid_count and index < 6 and is_success is True and now > Night_start:
            if _control_add_appid():
                up_appId(taskId[environment], appId_list[index], [], plan_id, label_id, culster_id, environment)
                r.set(redis_index, str(index + 1))
    elif len(appId_list) == 0:
        Logger.debug(f'暂不添加外灰名单')


def _control_add_appid():
    """控制自动添加外灰名单"""
    self_content = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"<font color=\"warning\">**接口自动化未执行通过不予加外部名单, 请及时解决！！**</font>  {at_tester}\n"
                }
            }
    
    # 今日接口自动化执行成功
    today_api, pass_today_api = [], []
    for api in smallConfig.Self['准现网']['api']:
            for k, v in api.items():
                today_api.append(find_api(v).json()['results'])
    for i in today_api:
        for j in i:
            if datetime.strptime(j['create_time'], "%Y-%m-%d %H:%M:%S").date() == datetime.now().date():
                pass_today_api.append(j['execute_status'])
    if any(i==1 for i in pass_today_api):
        return True
    elif r.get("remind_self") == '0':
            robot_smallCar(self_content, smallConfig.robotWebHook)
            r.set("remind_self", '1')
            return False
    return False


@catch_exception(Logger)
def test_outSideGray(pid, taskid):
    # 提醒测试
    Remind_TesterToTest(pid, taskid)

    _process_plan(pid, RedisKeyManager().get_key('AllDanId'), "今日", taskid)


def getAllTester(planId, taskId, env_name):
    """构造提醒测试小车单的消息"""
    testers = [i['creator'] for i in in_plan(planId).json()['data']['list']]
    
    plan_content = ready_line(
        taskId,
        r.get(RedisKeyManager().get_key('PlanId'))
    )
    app_list = [app['name'] for app in plan_content['data']['plan_content']]

    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"{GetUserId(list(set(testers)), [])[0]} 可以开始验证小车啦！\n\n"
                       f"[点击进入计划<---](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{planId})"
                       f"已加入【{env_name}】的名单有： {'  '.join(appId for appId in app_list)}"
        }
    }


def Remind_TesterToTest(pid, taskid):
    """提醒主控制逻辑"""
    for k, v in MessageTemplate.env_dict.items():
        if taskid.get(k):
            send_msg = getAllTester(pid, taskid.get(k), k)
            success_count = HadAppId(pid, taskid, k)
            Check_system = get_upload_appId_system_statu(pid, taskid.get(k),
                                                    f'【{k}】有系统发布失败 请检查 !!!',
                                                    at_tester, at_driver, smallConfig.robotWebHook, '小车计划')
            Logger.debug(f"获取到的taskId {taskid.get(k)}, success_count {success_count}, Check_system {Check_system}, {r.get(f'RemindTest_{k}_{smallConfig.PartPlanName}')} ")
            if r.get(f'RemindTest_{k}_{smallConfig.PartPlanName}') == "0" and success_count >= 1 and Check_system is True:
                robot_smallCar(send_msg, smallConfig.robotWebHook)
                r.set(f'RemindTest_{k}_{smallConfig.PartPlanName}', "1")
                Logger.debug(f"{k}  已提醒测试人员测试")
            elif r.get(f'RemindTest_{k}_{smallConfig.PartPlanName}') == "1":
                run_automation(pid)
