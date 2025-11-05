import ast
from datetime import datetime, timedelta
import logging
import os
import time
from common import robot_api
from common.Log import Logger
from common.robot_api import connect
from common.RedisConfig import r

sql_list = [
    """select id, title, current_owner, custom_field_10, reporter, custom_field_four, bugtype
    from db_ex_tapd.t_tapd_bug_order where 
    custom_field_8 = '教培产品中心' AND custom_field_10 = '紧急'
     AND (STATUS = '待处理' OR STATUS = '处理中' OR STATUS = '重新打开') AND custom_field_two LIKE '%课程%'""",

    """select id, title, current_owner, custom_field_10, custom_field_9, custom_field_four, bugtype 
    from db_ex_tapd.t_tapd_bug_order where 
    custom_field_8 = '教培产品中心' AND (STATUS = '待处理' OR STATUS = '处理中' OR STATUS = '重新打开') and custom_field_10 = '加急'"""
]

department_map = {
    '813444': '紧急', '813443': '加急', '813445': '普通'
}


def test_Mysql():
    try:
        with connect.cursor() as cursor:
            data = []
            for sql in sql_list:
                cursor.execute(sql)  # 先执行SQL语句
                rows = cursor.fetchall()  # 再获取查询结果
                data.extend(rows)

            unique_data = list(set(data))

            for idx, a in enumerate(unique_data):
                unique_data[idx] = tuple(list(a) + [''])

            # 如果非项目助手调用
            if os.getenv("ISSUE_ID") != "00000":
                unique_data.append(justNow(os.getenv("ISSUE_ID")))

            # 计算近30天该店铺提出过的所有工单数量
            for idx, i in enumerate(unique_data):
                cursor.execute(
                    f"""select Count(*) from db_ex_tapd.t_tapd_bug_order 
                    where DATE_SUB(CURDATE(), INTERVAL 30 DAY) <= date(created) AND custom_field_four = %s""",
                    (i[5],)
                )
                count = str(cursor.fetchone()[0])
                unique_data[idx] = tuple(list(i) + [count])

            Logger.debug(f"查出来所有单：{unique_data}")

            # 查找出目前查出的单和原本redis中的单有不同的工单
            current_issues = set([str(item) for item in unique_data])
            stored_issues = set(r.lrange('allDan', 0, -1))
            
            diff_time()

            r.set('diff', str(list(current_issues - stored_issues)))
            Logger.debug(f"不同的单为：{current_issues - stored_issues}")

            # 将目前所有的工单都存入redis 以便后续查出diff
            if unique_data:
                with r.pipeline() as pipe:
                    pipe.delete('allDan')
                    [r.rpush('allDan', str(item)) for item in unique_data]
                    r.expire('allDan', 129600)
            else:
                r.delete('allDan')
                r.rpush('allDan', 1)

    except Exception as e:
        Logger.error(f"异常：{e}")


# 将项目助手中的工单信息查询出来，并存入列表
def justNow(Id):
    # 秒拉群单
    res = robot_api.Second_kill(Id)['data']['Issue']
    Logger.debug(f"秒拉单接口请求返回：{res}")

    custom_fields = {field['Name']: field['ValueString'] for field in res['CustomFields']}

    return  (
        Id,
        res['Name'],
        res['Assignee']['Name'],
        department_map.get(custom_fields.get('紧急程度'), ''),
        res['Creator']['Name'],
        custom_fields.get('店铺appid', ''),
        res['DefectType']['Name'],
        ast.literal_eval(custom_fields.get('提单人', '')).get('Name')
    )


def diff_time():
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    Logger.debug(f'diff_time：{r.get("diff_time")}')
    if r.get('diff_time') is None:
        r.set('diff_time', current_time_str)
    else:
        last_time = datetime.strptime(r.get('diff_time'), '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - last_time
        Logger.debug(f'time_diff：{time_diff}')
        if time_diff >= timedelta(seconds=30):
            r.set('diff_time', current_time_str)
        else:
            time.sleep(30 - time_diff.total_seconds())
            r.set('diff_time', current_time_str)


