import ast
import re
from common.Log import Logger
from common.robot_api import find_gray_connect, get_gray_info, robot_smallCar, user_connect
from datetime import datetime, timedelta
from common.RedisConfig import r


def lower_words(app_ids):
    lower_appids = [i.lower() for i in app_ids]
    return lower_appids


def find_session():
    try:
        last_check_str = r.get("last_session_check_time")
        if last_check_str:
            last_check_time = datetime.strptime(last_check_str, "%Y-%m-%d %H:%M:%S")
        else:
            last_check_time = datetime.now() - timedelta(minutes=3)
        
        current_year_month = datetime.now().strftime("%y%m")
        current_date = datetime.now()
        
        if not current_year_month.isalnum() or len(current_year_month) != 4:
            raise ValueError(f"无效的表名后缀：{current_year_month}")
        
        table_name = f"t_chat_history_{current_year_month}"
        chat_id = "wrtJxhBgAAcw3n7JRXxp8ylskbQ96-Vg"
        
        # SQL语句使用占位符（不同数据库占位符可能不同，如%s、?等，根据实际数据库调整）
        sql = f"""
            SELECT from_user_name, msg_action, is_revoke, msg_show FROM {table_name} 
            WHERE chat_id = %s 
              AND created_at BETWEEN %s AND %s 
            ORDER BY created_at DESC;
        """
        
        # 4. 用with管理数据库连接，确保自动关闭
        with find_gray_connect as conn:
            with conn.cursor() as cursor:
                # 执行参数化查询（将时间转换为数据库支持的字符串格式）
                cursor.execute(
                    sql,
                    (chat_id, 
                     last_check_time.strftime("%Y-%m-%d %H:%M:%S"),
                     current_date.strftime("%Y-%m-%d %H:%M:%S"))
                )
                results = cursor.fetchall()
                Logger.info(f"查询到的会话记录数：{results}")
        
        # 5. 更新Redis中的上次检查时间（存储为str）
        r.set("last_session_check_time", current_date.strftime("%Y-%m-%d %H:%M:%S"))
        return list(results)
    
    except Exception as e:
        Logger.error(f"答疑群查询会话错误：{e}")
        return []
    

# 确定需要查询的appid
def process_sessions():
    # 取出字符串中appID的正则表达式
    pattern = r'app[a-zA-Z0-9]{10,20}'
    sessions = find_session()
    all_informations = []
    one_app_ids = {}
    error_ids = []
    if sessions is None:
        Logger.error("答疑群查询会话失败")
        return
    
    for idx, session in enumerate(sessions):
        Logger.info(f"处理会话记录：{session}")
        if session[3] != '' and session[2] ==  0 and session[1] == "send":
            appids = re.findall(pattern, session[3])
            lower_appids = list(set(lower_words(appids)))

            if appids:
                one_app_ids[session[0]] = lower_appids
                all_informations.append(one_app_ids)
                one_app_ids = {}
            else:
                error_ids.append(idx)
        else:
            Logger.info("发送消息被撤回或为空,跳过")
            error_ids.append(idx)
            continue
    for error_id in sorted(error_ids, reverse=True):
        del sessions[error_id]

    Logger.info(f"所有含有appid的会话记录：{all_informations}  {sessions}")
    return all_informations, sessions


# 查询用户职位
def position_session():
    all_informations, sessions = process_sessions()
    all_user_result = []
    error_ids = []
    if sessions is None:
        Logger.error("答疑群查询会话失败")
        return
    for idx, session in enumerate(sessions):
        Logger.info(f"处理会话记录职位：{session}")
        if session[0] != '':
            user_sql = "SELECT position FROM t_admin_user WHERE username like %s and state = 0"
            with user_connect.cursor() as cursor:
                    cursor.execute(user_sql, (f'%{session[0]}%',))
                    user_result = cursor.fetchall()
            all_user_result.append(user_result)
        else:
            error_ids.append(idx)

    for idx, user in enumerate(all_user_result):
        Logger.info(f"处理用户职位：{user}")
        all_informations[idx]['position'] = user[0][0]

        if all_informations[idx]['position'] not in ['服务管家', '客服专员', '客户经理', '大客户经理']:
            error_ids.append(idx)
    
    for error_id in sorted(error_ids, reverse=True):
        del all_informations[error_id]
        del sessions[error_id]
    Logger.info(f"所有用户职位查询结果：{all_user_result}  {all_informations}  {sessions}")
    return all_informations, sessions


# 获取appid对应的灰度
def get_appid_gray():
    all_informations, sessions = position_session()
    if len(all_informations) == 0:
        Logger.info("没有符合职位的会话记录")
        return
    
    all_person = [i[0] for i in sessions]
    Logger.info(f"所有符合职位的会话记录用户：{all_person}")
    all_msg, all_gray_info, is_recorded = [], {}, False
    
    # 近两天记录的所有灰度对应的app_id
    if r.get("all_gray_dict"):
        all_gray_dict = ast.literal_eval(r.get("all_gray_dict"))
    else:
        all_gray_dict = []

    for idx, info in enumerate(all_informations):
        for p in all_person:
            appids = info.get(p)
            Logger.info(f"处理会话记录灰度：{info},   {appids}")
            if appids:
                for appid in appids:
                    res = get_gray_info(appid)
                    Logger.info(f"查询到的appid灰度信息：{res}")
                    if '名单未被占用' in res['msg']:
                        Logger.info(f"{appid}没有被添加到其他计划中")
                    else:
                        plan_id = res['data']['bus_plan_id'] 
                        link = f'https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{plan_id}'
                        plan_name = res['data']['bus_plan_name']
                        msg = f"{appid}的灰度为：[{plan_name}]({link})"
                        all_msg.append(msg)
                        
                        if all_gray_dict:
                            for item in all_gray_dict:
                                if plan_name == item['plan_name'] and appid not in item['app_ids']:
                                    item['plan_id'] = plan_id
                                    item['plan_name'] = plan_name
                                    item['app_ids'].append(appid)
                                    item['is_send'] = '0'
                                    item['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    Logger.info(f"更新灰度记录：{all_gray_dict}")
                                    is_recorded = True
                                    break
                                elif plan_name == item['plan_name'] and appid in item['app_ids']:
                                    is_recorded = True
                                    Logger.info(f"{appid}在灰度记录中已存在，无需新增")
                                    break
                            if not is_recorded:
                                all_gray_info['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                all_gray_info['is_send'] = '0'
                                all_gray_info['plan_id'] = plan_id
                                all_gray_info['plan_name'] = plan_name
                                all_gray_info['app_ids'] = [appid]
                                all_gray_dict.append(all_gray_info)
                                all_gray_info = {}
                                Logger.info(f"新增灰度记录：{all_gray_dict}")  
                        else:     
                            all_gray_info['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            all_gray_info['is_send'] = '0'
                            all_gray_info['plan_id'] = plan_id
                            all_gray_info['plan_name'] = plan_name
                            all_gray_info['app_ids'] = [appid]
                            all_gray_dict.append(all_gray_info)
                            all_gray_info = {}
                            Logger.info(f"新增灰度记录：{all_gray_dict}")                            
                                
                break
            else:
                continue

    r.set("all_gray_dict", str(all_gray_dict))
    if len(all_msg)>0:
        total_msg = "\n".join(i for i in all_msg)
        Logger.info(f"将要发送到群里的消息为：{total_msg}")
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"{total_msg}"
            }
        }
        robot_smallCar(data, "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=78d70e72-2de0-4dfe-bf36-8d2e42df65b0")
        gray_num()
    else:
        pass
        
    
def gray_num():
    all_gray_msg = []
    if r.get("all_gray_dict"):
        all_gray_dict = ast.literal_eval(r.get("all_gray_dict"))
        Logger.info(f"所有灰度记录：{all_gray_dict}")
        for item in all_gray_dict:
            if item['is_send'] == '0' and len(item['app_ids']) >=2:
                msg = f"管家反馈的问题中，店铺<font color='red'>**{','.join(i for i in item['app_ids'])}**</font>  在灰度-[{item['plan_name']}](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{item['plan_id']})中, 请关注"
                all_gray_msg.append(msg)
                item['is_send'] = '1'
        r.set("all_gray_dict", str(all_gray_dict))
        
        if len(all_gray_msg)>0:
            total_msg = '\n'.join(i for i in all_gray_msg)
            data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"{total_msg}"
                    }
                }
            robot_smallCar(data, "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=78d70e72-2de0-4dfe-bf36-8d2e42df65b0")

        else:
            pass
                
    else:
        pass


def test_session():
    get_appid_gray()
