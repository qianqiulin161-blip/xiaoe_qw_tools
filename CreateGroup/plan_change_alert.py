import argparse
import os


parser = argparse.ArgumentParser(description="学习外灰现网变更提醒")
parser.add_argument("--Config", type=str, help="对应的配置")

args = parser.parse_args()

os.environ["Config"] = args.Config


import pymysql
import requests
from pymysql.cursors import DictCursor
from common.Exception import catch_exception
from common.Log import Logger
from common.YamlUtil import read_yaml_special
from common import robot_api


webHook_list = [{"教培": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fa2ed43c-a184-4557-a02d-860bff372c37"}, {"企服": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=07624e68-023a-45d1-835c-0d1430d3ad0f"}]

# 数据库配置常量
DB_CONFIG = {
    'host': 'jumpserver.xiaoe-tools.com',
    'user': '483e4d2b-02c1-4570-942f-33f05c569fd8',
    'password': 'WP9u6docxMVg2OjG',
    'database': 'change_instance',
    'port': 33061,
    'cursorclass': DictCursor
}


def get_db_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color=\"warning\">mysql登录认证有误请更改登录信息<@qiulinqian></font>\n\n"
            }
        }
        robot_api.robot_app(data)
        Logger.error(f"数据库连接失败: {str(e)}")
        raise

# 拿计划下的工单标题、url、创建人、测试
def search_plan_detail(plan_url):
    try:
        # 使用 rsplit 方法，按照 '/' 进行分割，并取最后一个元素
        plan_id = plan_url.rsplit('/', 1)[-1]
        response = robot_api.in_plan(plan_id)
        # 计划下的工单信息
        Logger.info(response.json())
        # 取工单标题、url、创建人
        return [{
            'iteration_name': item['iteration_name'],
            'coding_order_url': item['coding_order_url'],
            'creator': item['creator'],
            'tester': item['tester']
        } for item in response.json().get('data', {}).get('list', [])]
    except requests.exceptions.RequestException as e:
        Logger.error(f"获取计划详情失败: {e}")


# 查当前变更计划涉及的教培产品中心的系统
def search_plan_systems(plan_url, department):
    sql_list = [{"教培": f"select DISTINCT update_system from change_record where (update_env = '现网环境-all' OR update_env LIKE '%gray%') AND (update_center = '学习产品中心' or update_center = '教培产品中心') AND update_time >= NOW() - INTERVAL 5 minute AND update_url = '{plan_url}'"}, {"企服": f"select DISTINCT update_system from change_record where (update_env = '现网环境-all' OR update_env LIKE '%gray%') AND (update_center = '企服产品中心') AND update_time >= NOW() - INTERVAL 5 minute AND update_url = '{plan_url}'"}]
    for sql in sql_list:
            for k, v in sql.items():
                if k == department:
                    real_sql = v
                    break
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(real_sql)
            return '   '.join([row['update_system'] for row in cursor.fetchall()])


def process_iteration_info(iterations, department):
    """处理迭代信息生成消息内容"""
    user_mapping = read_yaml_special('/allUserId.yaml')
    plan_info = []

    for idx, info in enumerate(iterations, 1):
        if department == '教培':
            tester_id = next((f"<@{user[info['tester']]}>" for user in user_mapping if info['tester'] in user),
                            "<@qiulinqian>")
            creator_id = next((f"<@{user[info['creator']]}>" for user in user_mapping if info['creator'] in user),
                            "<@qiulinqian>")
        elif department == '企服':
            tester_id = next((f"<@{user[info['tester']]}>" for user in user_mapping if info['tester'] in user),
                            "<@kazikeyin>")
            creator_id = next((f"<@{user[info['creator']]}>" for user in user_mapping if info['creator'] in user),
                            "<@kazikeyin>")

        plan_info.append(
            f"{idx}、[{info['iteration_name']}]({info['coding_order_url']}) {creator_id}{tester_id}"
        )
    Logger.info(f"{plan_info}")
    return '\n'.join(plan_info)


def build_message_content(record, plan_info, systems, department):
    """构建消息内容"""
    env_display = '外灰环境' if 'gray' in record['update_env'] else record['update_env']
    operation_display = '发布系统' if record['update_operation'] == '发布' else record['update_operation']
    depart = '教培产品' if department == '教培' else '企服产品'
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"""<font color='warning'>*{depart}系统变更通知 😲 请关注客户反馈*</font>
时间： {record['update_time']}
操作： {operation_display}
环境： {env_display}
变更人： {record['update_people']}
**计划链接：** [{record['update_plan']}]({record['update_url']})
计划内容： 
{plan_info}
涉及系统： 
{systems}"""
        }
    }


@catch_exception(Logger)
def main():
    """ 主逻辑"""
    sql_list = [{"教培": """
                SELECT update_time,update_env,update_operation,
                        update_people,update_plan,update_url 
                FROM change_record
                WHERE (update_env = "现网环境-all" OR update_env LIKE "%gray%")
                AND update_center IN ('学习产品中心', '教培产品中心')
                AND update_time >= NOW() - INTERVAL 5 minute"""}, 
                {"企服": """
                SELECT update_time,update_env,update_operation,
                        update_people,update_plan,update_url 
                FROM change_record
                WHERE (update_env = "现网环境-all" OR update_env LIKE "%gray%")
                AND update_center IN ('企服产品中心')
                AND update_time >= NOW() - INTERVAL 5 minute"""}]
    for sql in sql_list:
        for k, v in sql.items():
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(v)
                    result = cursor.fetchall()
                    Logger.info(f"所有符合要求的数据   {result}")
                    seen_records = set()
                    for record in result:
                        record_key = (record['update_env'], record['update_operation'],
                                    record['update_people'], record['update_url'])

                        if record_key not in seen_records:
                            iterations = search_plan_detail(record['update_url'])
                            if iterations:
                                plan_info = process_iteration_info(iterations, k)
                                systems = search_plan_systems(record['update_url'], k)
                                Logger.info(f"更改的系统为   {systems}")
                                message = build_message_content(record, plan_info, systems, k)
                                Logger.info(f"发送的信息为   {message}")

                                for item in webHook_list:
                                    for a, b in item.items():
                                        if a == k:
                                            webHook = b  

                                res = robot_api.other_group(message, webHook)
                                Logger.info(f"发生消息的日志：   {res}")
                            seen_records.add(record_key)



if __name__ == "__main__":
    main()
