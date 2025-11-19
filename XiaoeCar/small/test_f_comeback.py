import ast
import time

from XiaoeCar.same.Same import get_hit_probability, get_upload_appId_system_statu, get_whole_network_statu, back
from XiaoeCar.same.test_SelfRun_API_UI import run_automation
from XiaoeCar.same.at_person  import at_tester, at_driver
import hashlib
import random
import requests
from common.Exception import catch_exception
from common.RedisKey import RedisKeyManager
from common.Small_Car_BaseInfo import smallConfig
from common.robot_api import get_plan_detail, in_plan, robot_smallCar, GetUserId
from common.RedisConfig import r
from datetime import datetime
from common.Log import Logger
from XiaoeCar.same.SelfRun_API_UI_Enum import MessageTemplate

VOICE_CONFIG = {
    'url': 'https://yun.tim.qq.com/v3/tlsvoicesvr/sendvoiceprompt',
    'app_id': '1400014102',
    'app_key': '878d0c777c06a29eff31a6302d4140f7'
}


# 时间处理函数
def get_time(time_str):
    return datetime.strptime(f"{datetime.now().date()} {time_str}", "%Y-%m-%d %H:%M:%S")

time_config = {
    'current': get_time(smallConfig.AttentionNetWorkTime[0]),
    'tomorrow': get_time(smallConfig.AttentionNetWorkTime[1])
}


def call_phone(ypid, taskId, tester, driver, env):
    link = f"https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{ypid}"

    if taskId.get(env):
        system_info = get_whole_network_statu(ypid, taskId.get(env), f"昨日小车【{env}】全网系统发布失败 , 请检查！", tester, driver, smallConfig.robotWebHook, '昨日小车计划')
        Logger.debug(f'昨日小车系统发布结果  {system_info}')

        if system_info and r.get(RedisKeyManager().get_key('WholeNetworkReport')) == '0':
            return True

        elif not system_info and datetime.now() >= time_config['tomorrow'] and r.get(RedisKeyManager().get_key('RemindTest')) == '0':
            robot_smallCar({"msgtype": "markdown",
                            "markdown": {
                                "content": f"昨天的小车请全网 {driver} \n"
                                            f"[{link}]({link})"
                            }}, smallConfig.robotWebHook)
            r.set(RedisKeyManager().get_key('RemindTest'), '0.5')
            return False

    elif r.get(RedisKeyManager().get_key('RemindTest')) == '0' and datetime.now() >= time_config['tomorrow']:
        robot_smallCar({"msgtype": "markdown",
                        "markdown": {
                            "content": f"昨天的小车请全网 {driver} \n"
                                        f"[{link}]({link})"
                        }}, smallConfig.robotWebHook)
        r.set(RedisKeyManager().get_key('RemindTest'), '0.5')
        return False
    return False


def call(phone, message):
    if smallConfig.PhoneNum != "None":
        sig_str = f"{VOICE_CONFIG['app_key']}{phone}".encode('utf-8')
        sig = hashlib.md5(sig_str).hexdigest()
        random_num = random.randint(100000, 999999)
        json_body = {
            "tel": {
                "nationcode": '86',
                "phone": phone
            },
            "prompttype": 2,
            "promptfile": f'{message}',
            "sig": sig,
            "ext": "123"
        }
        response_data = requests.post(
            f"{VOICE_CONFIG['url']}?sdkappid={VOICE_CONFIG['app_id']}&random={random_num}", json=json_body)
        Logger.debug(response_data.text)
        assert response_data.json()['result'] == '0'
        assert response_data.json()['errmsg'] == 'OK'
        Logger.debug(f'拨打电话成功:{phone}')


def send_the_end_msg(planId, tester):
    """全网后发送的总结报告"""
    response = in_plan(planId)
    plan_detail = get_plan_detail(planId)
    baseInfo = get_plan_detail(planId).json()
    project_hit_rate, hit_content = get_hit_probability(planId)
    num_dan = len(response.json()['data']['list'])
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"<font color='red'>**{'昨日小车已全网  已自动归档' if baseInfo['data']['is_finished'] == 3 else '昨日小车已全网  自动归档失败'}**</font>\n"
                       f"**【{plan_detail.json()['data']['plan_name']}全网报告】** {tester}\n"
                       f"**【发布内容】：** {num_dan}单\n"
                       f"**【发布结果】：** PASS\n"
                       f"**【命中率】：**  后端系统平均命中率为  {project_hit_rate}\n{hit_content}\n"
        }
    }


@catch_exception(Logger)
def test_comeback(ypid, taskId, tester, driver):
    need_whole_internet, is_allowed  = [], []
    for k, v in MessageTemplate().env_dict.items():
        if taskId.get(k):
            system_info = get_whole_network_statu(ypid, taskId.get(k), f"昨日小车【{k}】系统发布失败 , 请检查！", tester, driver, smallConfig.robotWebHook, '昨日小车计划')
            if system_info:
                need_whole_internet.append(v)
    if need_whole_internet:
        for env in need_whole_internet:
            Logger.debug(f'需要全网的环境有  {env}')
            is_true = call_phone(ypid, taskId, tester, driver, env)
            is_allowed.append(is_true)
    else:
        return 

    if all(i is True for i in is_allowed) and is_allowed and len(need_whole_internet) == len(is_allowed):
        back(ypid)  
        time.sleep(120)
        Logger.debug(f"现网报告内容： {send_the_end_msg(ypid, tester)}")
        robot_smallCar(send_the_end_msg(ypid, tester), smallConfig.robotWebHook)
        r.set(RedisKeyManager().get_key('WholeNetworkReport'), '1')
    else:
        Logger.debug('有环境未全网，暂不归档')