import ast
import time

from XiaoeCar.same.Same import get_hit_probability, get_upload_appId_system_statu, get_whole_network_statu, back
from XiaoeCar.self.test_SelfRun_API_UI import run_automation
from XiaoeCar.same.at_person  import at_tester, at_driver
from XiaoeCar.small.test_g_uploadAppId import getTaskId, HadAppId
import hashlib
import random
import requests
from common.Small_Car_BaseInfo import smallConfig
from common.robot_api import get_plan_detail, in_plan, ready_line, robot_smallCar, GetUserId
from common.RedisConfig import r
from datetime import datetime
from common.Log import Logger

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


def call_phone():
    Logger.debug(f'今日计划id与昨日计划id   {r.get(smallConfig.department_config[4])} {r.get(smallConfig.department_config[7])}')
    if r.get(smallConfig.department_config[7]):

        link = f"https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{r.get(smallConfig.department_config[7])}"
        taskId = getTaskId(r.get(smallConfig.department_config[7]))

        if taskId.get('国内-现网'):
            system_info = get_whole_network_statu(r.get(smallConfig.department_config[7]), taskId.get('国内-现网'),
                                                  "昨日小车【国内-现网】全网系统发布失败 , 请检查！",
                                                  ast.literal_eval(r.get(smallConfig.department_config[22]))[1],
                                                  ast.literal_eval(r.get(smallConfig.department_config[22]))[2], smallConfig.robotWebHook, '昨日小车计划')
            Logger.debug(f'{system_info}   {type(system_info)}')

            if system_info and r.get(smallConfig.department_config[17]) == '0':
                now = datetime.now()
                last_time_str = r.get(smallConfig.department_config[26])
                if not last_time_str:
                    # 首次记录时间
                    r.set(smallConfig.department_config[26], now.strftime('%Y-%m-%d %H:%M:%S'))
                    Logger.debug('首次记录归档时间，等待1小时后归档')
                else:
                    last_time = datetime.strptime(last_time_str, '%Y-%m-%d %H:%M:%S')
                    if (now - last_time).total_seconds() >= 3600:
                        Logger.debug('已归档并发送现网报告了')
                        back(r.get(smallConfig.department_config[7]))  
                        time.sleep(120)
                        Logger.debug(f'现网报告内容： {send_the_end_msg(r.get(smallConfig.department_config[7]))}')
                        robot_smallCar(send_the_end_msg(r.get(smallConfig.department_config[7])), smallConfig.robotWebHook)
                        r.set(smallConfig.department_config[17], '1')
                        r.delete(smallConfig.department_config[26])
                    else:
                        Logger.debug('距离上次记录时间未满1小时，暂不归档')

            elif not system_info and datetime.now() >= time_config['tomorrow'] and r.get(smallConfig.department_config[11]) == '0':
                robot_smallCar({"msgtype": "markdown",
                                "markdown": {
                                    "content": f'昨天的小车【国内-现网】请全网 {ast.literal_eval(r.get(smallConfig.department_config[22]))[2]} \n'
                                               f"[{link}]({link})"
                                }}, smallConfig.robotWebHook)
                r.set(smallConfig.department_config[11], '0.5')

        elif r.get(smallConfig.department_config[11]) == '0' and datetime.now() >= time_config['tomorrow']:
            robot_smallCar({"msgtype": "markdown",
                            "markdown": {
                                "content": f'昨天的小车【国内-现网】请全网 {ast.literal_eval(r.get(smallConfig.department_config[22]))[2]} \n'
                                           f"[{link}]({link})"
                            }}, smallConfig.robotWebHook)
            r.set(smallConfig.department_config[11], '0.5')
        else:
            pass


def test_remind_environment():
    call_phone()


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


def send_the_end_msg(planId):
    """全网后发送的总结报告"""
    response = in_plan(planId)
    plan_detail = get_plan_detail(planId)
    baseInfo = get_plan_detail(r.get(smallConfig.department_config[7])).json()
    project_hit_rate, hit_content = get_hit_probability(planId)
    num_dan = len(response.json()['data']['list'])
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"<font color='red'>**{'昨日小车已全网  已自动归档' if baseInfo['data']['is_finished'] == 3 else '昨日小车已全网  自动归档失败'}**</font>\n"
                       f"**【{plan_detail.json()['data']['plan_name']}全网报告】** {ast.literal_eval(r.get(smallConfig.department_config[22]))[1]}\n"
                       f"**【发布内容】：** {num_dan}单\n"
                       f"**【发布结果】：** PASS\n"
                       f"**【命中率】：**  后端系统平均命中率为  {project_hit_rate}\n{hit_content}\n"
        }
    }
