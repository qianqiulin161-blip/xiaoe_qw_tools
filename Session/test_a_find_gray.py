import ast
import re
from common.Exception import catch_exception
from common.Log import Logger
from common.robot_api import find_gray_connect, get_gray_info, robot_smallCar, user_connect
from datetime import datetime, timedelta
from common.RedisConfig import r


def lower_words(app_ids):
    lower_appids = [i.lower() for i in app_ids]
    return lower_appids


def find_session(chat_id):
    try:
        last_check_str = r.get("last_session_check_time")
        if last_check_str:
            last_check_time = datetime.strptime(last_check_str, "%Y-%m-%d %H:%M:%S")
        else:
            last_check_time = datetime.now() - timedelta(minutes=3)
        
        current_year_month = datetime.now().strftime("%y%m")
        current_date = datetime.now()
        Logger.debug(f'查找的时间范围为：{last_check_time}---{current_date}')
        
        if not current_year_month.isalnum() or len(current_year_month) != 4:
            raise ValueError(f"无效的表名后缀：{current_year_month}")
        
        table_name = f"t_chat_history_{current_year_month}"
        
        # SQL语句使用占位符（不同数据库占位符可能不同，如%s、?等，根据实际数据库调整）
        sql = f"""
            SELECT from_user_name, msg_action, is_revoke, msg_show, created_at FROM {table_name} 
            WHERE chat_id = %s 
              AND created_at BETWEEN %s AND %s 
            ORDER BY created_at DESC;
        """
        
        # 4. 用with管理数据库连接，确保自动关闭
        with find_gray_connect() as conn:
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
        
        # (('刘金铎', 'send', 0, ''), ('刘金铎', 'send', 0, '老师，辛苦看下这个可以达成吗@阳花平 ', '2025-11-13 00:00:00'), ('刘金铎', 'send', 0, 'DORA Lab+apphqhtivg25573  ', '2025-11-13 00:00:00'), ('干紫维', 'send', 0, '小鹅通C群&白文涛医考课堂+appl2dizpfj6908 麻烦问一下这个评论是默认评论吗？这个评论可以隐藏吗？@floweryang(阳花平)  ', '2025-11-13 00:00:00'))
        return list(results)
        
    
    except Exception as e:
        Logger.error(f"答疑群查询会话错误：{e}")
        return []
    

# 确定需要查询的appid
def process_sessions(chat_id):
    # 取出字符串中appID的正则表达式
    pattern = r'app[a-zA-Z0-9]{10,20}'
    sessions = find_session(chat_id)
    all_informations = []
    one_app_ids = {}
    error_ids = []
    if sessions is None:
        Logger.error("答疑群查询会话失败")
        return
    
    for idx, session in enumerate(sessions):
        Logger.info(f"处理会话记录：{session}")
        if "------" in session[3]:
            msg = session[3].split("------")[-1]
        else:
            msg = session[3]

        if msg != '' and session[2] ==  0 and session[1] == "send":
            appids = re.findall(pattern, msg)
            lower_appids = list(set(lower_words(appids)))

            if appids:
                one_app_ids[session[0]] = lower_appids
                one_app_ids['created_at'] = session[4]
                one_app_ids['msg'] = session[3]
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
    
    #[{'刘金铎': ['apphqhtivg25573'], 'created_at': time, 'msg': msg}, {'干紫维': ['appl2dizpfj6908'], 'created_at': time, 'msg': msg}]  [('刘金铎', 'send', 0, 'DORA Lab+apphqhtivg25573  ', time), ('干紫维', 'send', 0, '小鹅通C群&白文涛医考课堂+appl2dizpfj6908 麻烦问一下这个评论是默认评论吗？这个评论可以隐藏吗？@floweryang(阳花平)  ', time)]
    Logger.info(f"所有含有appid的会话记录：{all_informations}  {sessions}")
    return all_informations, sessions


# 查询用户职位
def position_session(chat_id):
    all_informations, sessions = process_sessions(chat_id)
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

    # [(('服务管家',),), (('服务管家',),)]  [{'刘金铎': ['apphqhtivg25573'], 'created_at': time, 'msg': msg, 'position': '服务管家'}, {'干紫维': ['appl2dizpfj6908'], 'created_at': time, 'msg': msg, 'position': '服务管家'}]  [('刘金铎', 'send', 0, 'DORA Lab+apphqhtivg25573  ', time), ('干紫维', 'send', 0, '小鹅通C群&白文涛医考课堂+appl2dizpfj6908 麻烦问一下这个评论是默认评论吗？这个评论可以隐藏吗？@floweryang(阳花平)  ', time)]
    Logger.info(f"所有用户职位查询结果：{all_user_result}  {all_informations}  {sessions}")
    return all_informations, sessions


# 获取appid对应的灰度
def get_appid_gray(chat_id, webhook):
    all_informations, sessions = position_session(chat_id)
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
            if appids:
                Logger.info(f"处理会话记录灰度：{info},   {appids}")
                for appid in appids:
                    res = get_gray_info(appid)
                    Logger.info(f"查询到的appid灰度信息：{res}")
                    if '名单未被占用' in res['msg']:
                        Logger.info(f"{appid}没有被添加到其他计划中")
                    else:
                        plan_id = res['data']['bus_plan_id'] 
                        link = f'https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{plan_id}'
                        plan_name = res['data']['bus_plan_name']
                        text = re.sub(r"[\n\r\t\x00-\x1F\x7F]", "", info.get("msg"))
                        msg = f"检测到<font color='red'>{appid}</font>在计划[{plan_name}]({link})中,请及时确认！\n" + f"咨询管家：<font color='green'>{p}</font>\n" + f"咨询时间：{info.get('created_at')}\n" + f"消息内容：<font color='gray'>{text}</font>\n"
                        
                        if all_gray_dict:
                            for item in all_gray_dict:
                                if plan_name == item['plan_name']:
                                    item['plan_id'] = plan_id
                                    item['plan_name'] = plan_name
                                    item['app_ids'].append(appid)
                                    item['is_send'] = '0'
                                    item['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    Logger.info(f"更新灰度记录：{item}")
                                    is_recorded = True
                                    final_msg = msg + f"近半小时反馈问题在该灰度的店铺有：<font color='red'>{','.join(f for f in list(set(item['app_ids'])))}</font>，请关注！"
                                    all_msg.append(final_msg)
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
                                final_msg = msg + f"近半小时无反馈问题在该灰度的店铺"
                                all_msg.append(final_msg)
                                break
                        else:     
                            all_gray_info['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            all_gray_info['is_send'] = '0'
                            all_gray_info['plan_id'] = plan_id
                            all_gray_info['plan_name'] = plan_name
                            all_gray_info['app_ids'] = [appid]
                            all_gray_dict.append(all_gray_info)
                            all_gray_info = {}
                            Logger.info(f"新增灰度记录：{all_gray_dict}")  
                            final_msg = msg + f"近半小时无反馈问题在该灰度的店铺\n"
                            all_msg.append(final_msg)     
                            break                     
                r.set("all_gray_dict", str(all_gray_dict))          
                break
            else:
                continue

    if len(all_msg)>0:
        for msg in all_msg:
            Logger.info(f"将要发送到群里的消息为：{msg}")
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"{msg}"
                }
            }
            robot_smallCar(data, webhook)
    else:
        pass


@catch_exception(Logger)
def test_session():
    chat_ids = ["wrtJxhBgAAcw3n7JRXxp8ylskbQ96-Vg", "wrtJxhBgAAtYVO7_iQvyRlOJPaofSb4w","wrtJxhBgAAfJO4qr8l5axfcgVSKbrwtQ"]
    webhook = ["https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=78d70e72-2de0-4dfe-bf36-8d2e42df65b0", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e456eff1-14f1-4e4c-bed4-57c074920833","https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c8a70524-ee55-420b-a28f-acbbd3dda242"]
   
    for i in range(len(chat_ids)):
        get_appid_gray(chat_ids[i], webhook[i])

    current_date = datetime.now()
    # 5. 更新Redis中的上次检查时间（存储为str）
    r.set("last_session_check_time", current_date.strftime("%Y-%m-%d %H:%M:%S"))
