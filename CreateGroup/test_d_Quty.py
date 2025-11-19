import ast
import logging
from datetime import datetime, timedelta
from common import robot_api
from common.Exception import catch_exception
from common.Log import Logger
from common.RedisConfig import r


weekday_map = {0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"}
students = ["sevenzhang(张鸿彬)", "nicholasfeng(酆益)", "kekejiang(蒋科)",
            "chschen(陈泽仕)", "junquanluo(罗君权)", "zepengzhang(张泽鹏)",
            "bowang(王博)", "zeruallin(林鑫鹏)", "linkslin(林沛)", 'sihaoli(李思豪)'
            "vitaszhuo(卓嘉宾)", "chilamli(李振朝)", "pennwang(王鹏)", "roundli(黎文涛)",
            "wenqiangfeng(冯文强)", "abelchen(陈洪升)", "whitonwang(王辉腾)", "cyruschang(常云骁)", "feiduan(段菲)","atunxu(徐皓扬)"]


@catch_exception(Logger)
def test_quty():
    sql = "SELECT * FROM t_admin_user WHERE username LIKE %s and state = 0"
    day, weekday = [], []

    # 获取当前日期
    current_date = datetime.now()
    am = current_date.replace(hour=8, minute=0, second=0, microsecond=0)
    end = current_date.replace(hour=18, minute=0, second=0, microsecond=0)

    # people = ['junquanluo(罗君权)', 'zepengzhang(张泽鹏)', 'bowang(王博)', 'zeruallin(林鑫鹏)', 'atunxu(徐皓扬)', 'sihaoli(李思豪)']
    # aa =  ['junquanluo', 'feiduan(段菲)', 'cyruschang(常云骁)', 'whitonwang(王辉腾)', 'abelchen', 'wenqiangfeng(冯文强)', 'roundli(黎文涛)', 'pennwang(王鹏)', 'chilamli(李振朝)', 'vitaszhuo(卓嘉宾)', 'linkslin(林沛)', 'sevenzhang(张鸿彬)', 'nicholasfeng(酆益)', 'kekejiang(蒋科)', 'chschen(陈泽仕)']
    # r.delete("use_people")
    # r.delete("no_use_people")
    # r.set("use_people", str(aa))
    # r.set("no_use_people", str(people))

    # 已在值班列表中的人
    use_people = ast.literal_eval(r.get("use_people"))
    # 未在值班列表中的人
    np_use_people = ast.literal_eval(r.get("no_use_people"))

    # 为空的话把students的值赋值给这个
    if len(np_use_people) == 0:
        np_use_people = [item for item in students if item not in use_people]
    Logger.debug(f"未值班的人有：  {np_use_people}, 正在值班列表的人有：   {use_people}")

    with robot_api.user_connect.cursor() as cursor:
        for i in use_people:
            cursor.execute(sql, (f'%{i}%',))
            results = cursor.fetchall()
            Logger.debug(f"查询到的符合状态的用户   {results}")
            if len(results) == 0:
                Logger.debug(f"查询不到符合状态的用户   {use_people[0]}")
                use_people.remove(use_people[0])
                index = np_use_people.index(np_use_people[-1])
                use_people.append(np_use_people[index])
                np_use_people.pop(index)
            else:
                break

    # 是否已发送标识
    judge = r.get("quty")
    Logger.debug(f"是否已发送值班列表标识： {judge}")

    for i in range(14):
        date = current_date + timedelta(days=i)
        formatted_date = date.strftime("%m-%d")
        day.append(formatted_date)
        day_of_week = weekday_map[date.weekday()]
        weekday.append(day_of_week)
        Logger.debug(f"日期：{day}\n\n   星期：{weekday}")

    if current_date > am and judge == "0":
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">**教培产品答疑日历**</font>\n\n"
            }
        }
        for j in range(len(day)):
            data["markdown"]["content"] += f"{day[j]} {weekday[j]}:  <font color=\"green\">**{use_people[j]}**</font>\n"
        robot_api.robot_Quty(data)
        data1 = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">今日份的值班大佬，就决定是你了：{use_people[0]}!!! <@{use_people[0]}></font>\n\n"
            }
        }
        robot_api.robot_Quty(data1)

        # 将每个人对应这次值班的日期和星期存入redis
        person_data = [day[0], weekday[0]]
        r.set(use_people[0], str(person_data))
        r.persist(use_people[0])

        use_people.pop(0)
        r.set("quty", "1")

        # 在人数足够的情况下  防止一部分密集答疑
        # for l in np_use_people:
        #     # 如果没有这个人的信息
        #     if r.get(l) is None:
        #         lucky = l
        #     else:
        #         lucky_data = ast.literal_eval(r.get(l))
        #
        #         time = datetime.strptime(f'{datetime.now().date()}', "%Y-%m-%d").date()
        #         this_lucky_time = datetime.strptime(f'{datetime.now().year}-{lucky_data[0]}', "%Y-%m-%d").date()
        #         today_time = datetime.strptime(f'{datetime.now().year}-{day[0]}', "%Y-%m-%d").date()
        #
        #         if time > this_lucky_time:
        #             lucky_time = datetime.strptime(f"{datetime.now().year}-{lucky_data[0]}", "%Y-%m-%d").date()
        #         elif time < this_lucky_time:
        #             lucky_time = datetime.strptime(f"{datetime.now().year - 1}-{lucky_data[0]}", "%Y-%m-%d").date()
        #
        #         # 时间大于7天， 如果上次是周日周天，这次也是周日周天的话则直接跳过，选择下一个
        #         if (today_time - lucky_time).days > 7:
        #             if (lucky_data[1] == "星期六" or lucky_data[1] == "星期日") and (
        #                     weekday[13] != "星期六" or weekday[13] != "星期日"):
        #                 lucky = l
        #                 Logger.debug(f"今日值班{l}  上一次值班是周六周日这次不是")
        #                 break
        #             elif lucky_data[1] != "星期六" or lucky_data[1] != "星期日":
        #                 Logger.debug(f"今日值班{l}  上一次值班不是周六周日这次随便排")
        #                 lucky = l
        #                 break
        #             else:
        #                 continue
        #         else:
        #             Logger.debug(f"{l}  值班太频繁了  换一个同学")
        #             continue

        lucky = np_use_people[-1]

        index = np_use_people.index(lucky)
        use_people.append(np_use_people[index])
        np_use_people.pop(index)
        r.delete("use_people")
        r.set("use_people", str(use_people))
        r.expire('use_people', 129600)
        r.delete("no_use_people")
        r.set("no_use_people", str(np_use_people))
        r.expire('no_use_people', 129600)

    elif current_date > end and judge == "1":
        data2 = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">明日值班大佬预告：{use_people[0]}!!!  <@{use_people[0]}></font>\n\n"
            }
        }
        robot_api.robot_Quty(data2)
        r.set("quty", "2")

    else:
        Logger.debug("未达到触发条件")
