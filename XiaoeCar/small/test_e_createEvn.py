import ast
import os
from datetime import datetime
from XiaoeCar.same.at_person import at, at_tester, at_driver
from XiaoeCar.same.SelfRun_API_UI_Enum import MessageTemplate
from XiaoeCar.same.Same import build_plan, HadAppId
from common.Exception import catch_exception
from common.RedisKey import RedisKeyManager
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from common.robot_api import batch_merge, get_in_plan_one_detail, in_plan, ready_line, robot_smallCar, \
    environment, GetUserId, batch_create, \
    get_is_marge, set_tag
from common.RedisConfig import r
from tenacity import retry, stop_after_attempt, wait_fixed

# 设置最大重试次数，这里设置为3次，你可以根据实际情况调整
MAX_ATTEMPTS = 3
# 设置重试间隔时间（单位：秒），这里设置为5秒，同样可按需调整
RETRY_INTERVAL = 3

part_link = 'https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/'


def child_evnOfReady(name, plan_id, creator, taskid, env_name):
    is_true = batch_marge(plan_id, taskid[env_name])
    if is_true is True :
        r.set(RedisKeyManager().get_key('EvnTag'), '1')
        return robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">**【{env_name}】环境已部署成功，已发起代码合并请求，请合并代码！！**</font>\n"
                        f"计划: [{name}]({part_link}{plan_id}) \n {creator}"
            }
        }, smallConfig.robotWebHook)
    else:
        r.set(RedisKeyManager().get_key('EvnTag'), '1')
        return robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">**【{env_name}】已部署成功，发起代码合并请求失败，请手动发起！！**</font> {at_driver}"
            }
        }, smallConfig.robotWebHook)


@retry(stop=stop_after_attempt(MAX_ATTEMPTS), wait=wait_fixed(RETRY_INTERVAL),
       reraise=True)
def evnOfReady(plan_id, env_id):
    """部署准现网环境"""
    res_data = environment(plan_id, env_id)
    if res_data['code'] == 0:
        return True

    elif res_data['code'] != 0 and r.get(RedisKeyManager().get_key('EvnTag')) == '0':
        content = '\n'.join(f"系统{i['system_name']} 与计划 [{i['plan_name']}]({part_link}{str(i['plan_id'])})" for i in
                            res_data['data'])
        return content
    

def judge_all_env(creator, name, plan_id, taskid):
    env_res_list = {}
    for k, v in MessageTemplate().env_dict_id.items():
        env_res = evnOfReady(plan_id, v)
        env_res_list[k] = env_res

    if any(type(v) == str for k, v in env_res_list.items()) and r.get(RedisKeyManager().get_key('EvnTag')) == '0': 
        content = '\n'.join(f'<font color=\"warning\">**{k}部署失败**</font>\n{v}' for k, v in env_res_list.items() if type(v) == str)
        final_content = content + f'\n{at_driver}'
        robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": final_content
            }
        }, smallConfig.robotWebHook)
        r.set(RedisKeyManager().get_key('EvnTag'), '0.5')
        
    if any(type(v) == bool for k, v in env_res_list.items()):
        for k, v in env_res_list.items():
            if type(v) == bool:
                child_evnOfReady(name, plan_id, creator, taskid, k)


# 通用判断逻辑封装
def _check_redis_content(redis_key, target_list, result, count, name, plan_id, creator, res, taskid):
    if r.get(redis_key) is None:
        r.set(redis_key, "['1']")
        return
    start = datetime.strptime(smallConfig.ReviewTime[0], "%H:%M").time()
    content = ast.literal_eval(r.get(redis_key))
    if "1" in content:
        content.remove("1")

    if (not (set(content) == set(target_list) or len(result["data"]["list"]) != count)) and datetime.now().time() > start and r.get(RedisKeyManager().get_key('EvnTag')) == '0':
        r.set(redis_key, str(target_list))
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"**🔔已评审通过, 正在自动部署准现网环境**\n"
            }
        }
        robot_smallCar(data, smallConfig.robotWebHook)

        judge_all_env(creator, name, plan_id, taskid)

        # 以下用于在小车允许全网后发报告使用
        r.set(RedisKeyManager().get_key('DanNum'), str(len(res.json()['data']['list'])))
        # 存入今日计划内容工单id
        names = []
        for i in res.json()['data']['list']:
            names.append(i['iteration_id'])
        r.set(RedisKeyManager().get_key('PlanContent'), str(names))
        
    elif r.get(RedisKeyManager().get_key('EvnTag')) == '0.5':
        judge_all_env(creator, name, plan_id, taskid)
    
    Logger.debug(f"{name}: {target_list}, {count}")


# 主业务逻辑
@catch_exception(Logger)
def test_selfRunJieKou(all_plan, taskid):
    # 执行合并检查
    response = in_plan(all_plan)
    if response.status_code == 200 and response.json()["code"] == 0:
        result = response.json()
        dan_list = [item["iteration_id"] for item in result["data"]["list"]]
        creator = [item["creator"] for item in result["data"]["list"]]
        at_data_end = GetUserId(list(set(creator)), [])[0]
        start = datetime.strptime(smallConfig.ReviewTime[0], "%H:%M").time()
        end = datetime.strptime(smallConfig.ReviewTime[1], "%H:%M").time()

        if start <= datetime.now().time() <= end:
            msg_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f" [今日计划]({part_link}{all_plan}) <font color=\"warning\"><<--- 点击进入计划</font>\n"
                                f" 测试：{at_tester}\n "
                                f"评委：{at}\n "
                                f"开发司机：{at_driver}\n "
                                f"开发：{at_data_end}\n "
                                f"请评审今日小车单！"
                }
            }
            robot_smallCar(msg_data, smallConfig.robotWebHook)

        count = sum(1 for item in result["data"]["list"] if item["coding_order_stage_text"] in
                    ["评审通过", "测试验证中", "允许全网"])
        
        _check_redis_content(RedisKeyManager().get_key('ReviewPassId'), dan_list, result, count,
                                smallConfig.PartPlanName + "中心小车", all_plan, at_data_end, response, taskid)
        
        success_count = HadAppId(all_plan, taskid, "国内准现网")
        if success_count < 1 and r.get(RedisKeyManager().get_key('EvnTag')) != '2':
            is_all_marge(all_plan, taskid)


@retry(stop=stop_after_attempt(MAX_ATTEMPTS), wait=wait_fixed(RETRY_INTERVAL),
       reraise=True)
def batch_marge(plan_id, taskId):
    """发起代码合并请求"""
    systems_id = []
    res = in_plan(plan_id).json()
    for i in res['data']['list']:
        if len(i['system_list']) != 0 or i['system_list'] is not None:
            for j in i['system_list']:
                systems_id.append(j['system_id'])
        else:
            continue
    res_create = batch_create(plan_id, taskId, systems_id)
    res_merge = batch_merge(plan_id, taskId, systems_id)
    Logger.info(f'代码合并请求返回  {res_create}')
    if res_create['code'] == 0:
        Logger.debug(f'发起代码合并请求成功！！')
        return True
    else:
        Logger.debug(f'发起代码合并请求失败！！')
        return False


def is_all_marge(pid, taskId):
    """查询是否所有系统都合并了代码，并打tag"""
    if taskId.get('国内-准现网'):
        systems_id = []
        res = in_plan(pid).json()
        for i in res['data']['list']:
            if len(i['system_list']) != 0 or i['system_list'] is not None:
                for j in i['system_list']:
                    systems_id.append(j['system_id'])
            else:
                continue

        total = []
        systems_id = list(set(systems_id))
        for s in systems_id:
            system_dict = {'system_id': s, 'tag_name': '', 'tag_desc': ''}
            total.append(system_dict)
        Logger.debug(f'打tag系统传参  {total}')

        is_marge = get_is_marge(pid, taskId['国内-准现网'])
        success_count = 0
        for i in is_marge['data']:
            if len(i['merge_data']) == 0:
                return Logger.debug(f'还没有发起代码合并请求')
            else:
                for j in i['merge_data']:
                    if j['merge_request_status'] != 'closed' and j['merge_request_status'] != 'merged':
                        return Logger.debug(f"系统 {i['sys_en_name']} 没有合并代码哦！！")
                success_count += 1
        Logger.debug(f'已合并代码的系统数为   {success_count},   系统数为： {systems_id}')
        
        buile_statue = build_plan(pid, taskId['国内-准现网'])

        if buile_statue:
            r.set(RedisKeyManager().get_key('EvnTag'), '2')

        if len(systems_id) == success_count and buile_statue is False:
            Logger.debug(f'开始打tag！！')
            res_tag = set_tag(pid, taskId['国内-准现网'], total)
            if res_tag['code'] == 0 and '创建tag成功' in res_tag['msg']:
                r.set(RedisKeyManager().get_key('EvnTag'), '2')
                return robot_smallCar({
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"今日小车已打【国内-准现网】系统tag，请司机发布代码！{at_driver}"
                    }
                }, smallConfig.robotWebHook)
            else:
                r.set(RedisKeyManager().get_key('EvnTag'), '2')
                return robot_smallCar({
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"今日小车打系统tag出错，请手动操作！{at_driver}"
                    }
                }, smallConfig.robotWebHook)
        elif buile_statue is True:
            r.set(RedisKeyManager().get_key('EvnTag'), '2')
