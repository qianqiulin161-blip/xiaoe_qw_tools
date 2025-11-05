import ast
import base64
import os
import pymysql
from common.Log import Logger
from common.RedisConfig import r
from common.SendRequest import SendRequest
import json
from common.YamlUtil import read_yaml_special
from jsonpath import jsonpath
# 建立连接对象
connect = pymysql.connect(host='bj-cdb-h2jq1e4q.sql.tencentcdb.com', user='monitor_query',
                          password='6k13+j=#wyrk79ye', database='db_ex_tapd', port=61965)

user_connect = pymysql.connect(host='bj-cdb-h2jq1e4q.sql.tencentcdb.com', user='monitor_query',
                               password='6k13+j=#wyrk79ye', database='db_user_center', port=61965)

find_gray_connect = pymysql.connect(host='jumpserver.xiaoe-tools.com', user='706953de-b64b-4b1e-b5a1-9128914d02ec', 
                                    password='MrgP35u2F6p1ftah', database='db_ex_robots_service', port=33061)

AppId = os.getenv("AppId")
token = read_yaml_special('/token.yaml')

# 班车系统不过期接口
string = "ops_gateway:DVRRu7ytssydL4dYfR8TfdOxRaujCcoy"
encoded_string = base64.b64encode(string.encode('utf-8'))
headers = {'Authorization': 'Basic {}'.format(encoded_string.decode('utf-8')),
           }
if AppId is not None:
    headers['Cookie'] = f'app_id={AppId}'


def Header_allTheSame(planId):
    Header = {
        "Cookie": f"sidebarStatus=0;ops_token={token[0]};",
        "content-type": f"application/json;charset=UTF-8",
        "origin": "https://ops.xiaoe-tools.com",
        "redirect": f"/xiaoe_bus/workplan/plan_details/{planId}",
        "referer": "https://ops.xiaoe-tools.com/"
    }
    if AppId is not None:
        Header['Cookie'] += f'app_id={AppId}'
    return Header


Logger.debug(f'请求头数据：{headers},    {Header_allTheSame(1)}')


def robot_similarity(data):
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=300ba301-5615-4924-981b-ed502a8ec9b4"
    method = "POST"
    headers = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=url, method=method, headers=headers, json=data,
                                 verify=False)


# 群里的app机器人
def robot_app(data):
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=41fe706f-61c3-4969-b013-7b9078f5bb0c"
    method = "POST"
    headers = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=url, method=method, headers=headers, json=data,
                                 verify=False)


# 通过工单id，查该单所有信息
def Second_kill(Id):
    url = "http://ops-api-master.ops-api.svc.cluster.local/xe.api.coding.issue.detail"
    method = "post"
    data = {
        "ProjectName": "xianwangjishugongdan",
        "IssueCode": Id
    }
    header = {
        "Content-Type": "application/json"
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=header, verify=False).json()
    return res


# 判断店铺 是否为KA接口
def find_is_KA(app_id):
    check_url = "https://super.xiaoe-tech.com/new/operation/tag_system/app_manage/list"
    check_method = "Get"
    check_headers = {
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://super.xiaoe-tech.com/new",
        "X-Requested-With": "XMLHttpRequest",
        "Menu-Path": "https://super.xiaoe-tech.com/new#/crm/tag_system/shop_list",
        "sec-ch-ua-platform": "macOS",
        "Cookie": "dataUpJssdkCookie={'wxver':'','net':'','sid':''}; laravel_session=b2e82cfb562e754499d5f3cb533d541c5494c58e; XIAOEID=f9a0aaf2ae21d19b3ab7d283ba927fb6"
    }
    check_data = {
        "uu_id": "tag_customer_deliver_v2",
        "area_search_content": "",
        "tag_search[0][tag_id]": "big_manager_id",
        "tag_search[0][tag_type]": "selection",
        "tag_search[0][tag_content][]": ['656', '672', '720', '959', '1172', '2702', '3303'],
        "tag_search[1][tag_id]": "app_id",
        "tag_search[1][tag_type]": "text",
        "tag_search[1][tag_content]": app_id,
        "page": "1",
        "page_size": "15"
    }
    res = SendRequest.all_send_request(method=check_method, url=check_url, headers=check_headers, params=check_data,
                                       verify=False)
    # 看返回是不是json格式，不是就是token过期了
    try:
        res.json()
        print(res.json())
        is_json = True
    except json.JSONDecodeError:
        is_json = False

    if is_json:
        print("检查成功")
    else:
        count = r.get("KA_api")
        if count != "1":
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"查询店铺是否为KA接口token过期了，请诚哥拿下新的laravel_session <@qy01114f0e7c0eddb29bab13134a>\n\n"
                }
            }
            robot_app(data)
            r.set("KA_api", "1")
    return res.json()


# 更改现网工单标题接口
def change_title(name, code):
    name_url = f"https://xiaoe.coding.net/api/project/10926144/issues/defects/{code}/fields"
    name_method = "PATCH"
    name_headers = {
        "content-type": "application/json;charset=UTF-8",
        "cookie": "teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; eid=da3ff0a8-4e76-4bc1-af71-9856a68f016f; enterprise_domain=xiaoe; clientId=646ba26d-cbd6-422d-8252-15bb7a103c18; XSRF-TOKEN=98fe69af-536e-4c88-9f17-39c72b5a73dd; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; cf=47f8e61c00009171a26b093036f1e21f",
        "origin": "https://xiaoe.coding.net",
        "referer": f"https://xiaoe.coding.net/p/xianwangjishugongdan/bug-tracking/issues/{code}/detail",
        "x-xsrf-token": "f6bbc40d-2cf3-48dc-bd34-e4d98f618a37"
    }
    name_data = {
        "name": "【KA】" + name
    }
    res = SendRequest.all_send_request(url=name_url, method=name_method, json=name_data, headers=name_headers,
                                       verify=False)
    if res.json()["code"] != 0 or "code" not in res.json():
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"修改KA工单名称接口失效<@qiulinqian>\n\n"
            }
        }
        robot_app(data)
    else:
        print("修改标题接口没过期")
    res.json()


# 自动拉群接口
def create_group(service_people, Name, first_msg):
    url = "https://alivereport.xiaoeknow.com/_panel/create_group_api"
    method = "post"
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "source": "学习产品中心",
        "group_arr": service_people,
        "group_name": Name,
        "group_first_msg": first_msg
    }
    SendRequest.all_send_request(url=url, method=method, headers=header, json=data, verify=False)


# 答疑日历机器人
def robot_Quty(data):
    works_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=942e3f9b-d033-44fa-9e8d-a251791fdd19"
    method1 = "POST"
    headers = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=works_url, method=method1, headers=headers, json=data, verify=False)


# 查询每个计划当中的小迭代信息接口
def in_plan(plan_id):
    url_back = "https://openapi.xiaoe-tools.com/ops/xe.bs.plan.get.iteration/1.0.0"
    method_back = "post"
    data_back = {
        "plan_id": str(plan_id)
    }
    res = SendRequest.all_send_request(url=url_back, method=method_back, headers=headers,
                                       json=data_back,
                                       verify=False)
    print(res.json())
    return res


# 查询小迭代对应的现网工单id
def in_plan_one(id):
    url_back = f"https://xiaoe.coding.net/api/project/10901644/issues/missions/{id}/activities"
    method_back = "get"
    header_back = {
        "cookie": "teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; _pk_id.4.c189=9aa57baedc5bb7e0.1749441082.; _ga=GA1.1.226655824.1749723636; _ga_FVWC4GKEYS=GS2.1.s1749780221$o2$g1$t1749783287$j59$l0$h0; united=276f6616-c22f-415e-9387-6406df280f19; eid=075a0580-56ea-4f2f-b0e8-c4e0eb7b0960; enterprise_domain=xiaoe; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; clientId=269a6ecf-ee6a-419e-8574-aa998bdb8fd2; XSRF-TOKEN=f6bbc40d-2cf3-48dc-bd34-e4d98f618a37; SameSite=Lax; cf=66ff89e5d0fe17ec799346bcc5377234; coding_demo_visited=1",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "referer": f"https://xiaoe.coding.net/p/xiaoereleaseorder/assignments/issues/{id}/detail",
    }
    res = SendRequest.all_send_request(url=url_back, method=method_back, headers=header_back,
                                       verify=False)
    # if res.json()['code'] != 0 or 'code' not in res.json():
    #     data = {
    #         "msgtype": "markdown",
    #         "markdown": {
    #             "content": f"查询现网id接口过期<@qiulinqian>\n\n"
    #         }
    #     }
    #     robot_app(data)
    # else:
    #     print("查询现网接口无事发生")
    return res


# 查询现网工单的详情信息
def now_environment(id):
    url_back = f"https://xiaoe.coding.net/api/project/10926144/issues/defects/{id}/activities"
    method_back = "get"
    header_back = {
        "cookie": "teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; _pk_id.4.c189=9aa57baedc5bb7e0.1749441082.; _ga=GA1.1.226655824.1749723636; _ga_FVWC4GKEYS=GS2.1.s1749780221$o2$g1$t1749783287$j59$l0$h0; united=276f6616-c22f-415e-9387-6406df280f19; eid=075a0580-56ea-4f2f-b0e8-c4e0eb7b0960; enterprise_domain=xiaoe; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; clientId=269a6ecf-ee6a-419e-8574-aa998bdb8fd2; XSRF-TOKEN=f6bbc40d-2cf3-48dc-bd34-e4d98f618a37; SameSite=Lax; cf=66ff89e5d0fe17ec799346bcc5377234; coding_demo_visited=1",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "referer": f"https://xiaoe.coding.net/p/xiaoereleaseorder/assignments/issues/{id}/detail",
    }
    res = SendRequest.all_send_request(url=url_back, method=method_back, headers=header_back,
                                       verify=False)
    return res


# 获取计划详情接口
def get_plan_detail(planId):
    url = "https://openapi.xiaoe-tools.com/ops/xe.bs.plan.get.detail/1.0.0"
    method = "post"
    data = {
        'plan_id': planId,
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=headers, verify=False)
    return res


# 查询小迭代详情的接口
def get_in_plan_one_detail(real_id):
    one_url = "https://openapi.xiaoe-tools.com/ops/xe.bs.iteration.get.detail/1.0.0"
    one_method = "post"
    one_data = {
        "iteration_id": real_id
    }
    res = SendRequest.all_send_request(url=one_url, method=one_method, json=one_data, headers=headers,
                                       verify=False)
    return res


# 小车群监测模块机器人
def robot_model(webhook_data):
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b55d91a9-79b0-4acc-bbf1-45aaf7890aff"
    webhook_method = "POST"
    webhook_headers = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=webhook_url, headers=webhook_headers, method=webhook_method,
                                 json=webhook_data, verify=False)


# 根据所有条件查询计划
def get_all_no_guiDang(is_finish, start_time, end_time, plan_name, creator):
    url = "https://openapi.xiaoe-tools.com/ops/xe.bs.plan.list/1.0.0"
    method = "post"
    data = {
        "is_finished": is_finish,
        "page_size": 100,
        "page_index": 1,
        "plan_name": plan_name,
        "start_date": start_time,
        "end_date": end_time,
        "creator": creator
    }
    res = SendRequest.all_send_request(url=url, method=method, headers=headers, json=data, verify=False)
    plan_ids = []
    plan_names = []
    plan_owner = []
    plan_auth = []
    plan_stage = []
    production_at = []
    p_type = []
    ops_id = []
    department_id = []
    devops_process_name = []
    for item in res.json()['data']['list']:
        plan_ids.append(item.get('plan_id'))
        plan_names.append(item.get('plan_name'))
        plan_owner.append(item.get('creator'))
        plan_auth.append(item.get('auth_ids'))
        plan_stage.append(item.get('plan_stage_txt'))
        production_at.append(item.get('production_at'))
        p_type.append(item.get('publish_type'))
        ops_id.append(item.get('ops_id'))
        department_id.append(item.get('department_id'))
        devops_process_name.append(item.get('devops_process_name'))
    return [plan_ids, plan_names, plan_owner, plan_auth, plan_stage, production_at, p_type, ops_id, department_id,
            devops_process_name]


# 组内计划未归档提醒机器人
def robot_no_back_plan(qiwei_data):
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=3b5bfbfa-f6be-4d6f-8863-1326b3b2b38a"
    qiwei_headers = {
        "Content-Type": "application/json"
    }
    qiwei_method = "post"
    SendRequest.all_send_request(url=webhook_url, method=qiwei_method, json=qiwei_data,
                                 headers=qiwei_headers,
                                 verify=False)


# 查询接口自动化跑的成功率接口
def find_api(name):
    url = f"https://testing-platform.test.xiaoe-tools.com/api/eolinker/test_plan_execute_history/?page=1&name__icontains={name}"
    method = "GET"
    header = {
        'authorization': 'Token 798b96b813917b67c485d617c5661a72e3593e08'
    }
    res = SendRequest.all_send_request(url=url, method=method, headers=header, verify=False)
    return res


# 开测群测试环境接口自动化成功率日报机器人
def robot_everyday(data):
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7557d155-5f56-430b-b4fa-fed4edbc9401"
    method = "post"
    header = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=url, method=method, headers=header, json=data, verify=False)


def smallCar_getDan():
    """环境变量中获取需要捞单的中心  并捞单"""
    try:
        de = ast.literal_eval(os.getenv('department'))
        iterationStage = ast.literal_eval(os.getenv('iterationStage'))
        CodingOrderStage = ast.literal_eval(os.getenv('CodingOrderStage'))
        filterConditions = ast.literal_eval(os.getenv("filterConditions"))
        end_res = []
        for one in de:
            url = "https://openapi.xiaoe-tools.com/ops/xe.bs.iteration.get.list/1.0.0"
            method = "post"
            datas = {
                "iteration_name": "",
                "creator": "",
                "iteration_leader": "",
                "iteration_stage": iterationStage,
                "relative_project": "",
                "production_at": "",
                "project_id": "",
                "department_id": one,
                "iteration_type": 4,
                "coding_order_stage": CodingOrderStage,
                "is_bind_plan": 0,
                "product_line": "xiaoetong",
                "page_index": 1,
                "page_size": 10
            }
            datas1 = {
                "iteration_name": "",
                "creator": "",
                "iteration_leader": "",
                "iteration_stage": iterationStage,
                "relative_project": "",
                "production_at": "",
                "project_id": "",
                "department_id": one,
                "iteration_type": 1,
                "coding_order_stage": CodingOrderStage,
                "is_bind_plan": 0,
                "product_line": "xiaoetong",
                "page_index": 1,
                "page_size": 10
            }
            res = SendRequest.all_send_request(method=method, url=url, json=datas, headers=headers, verify=False).json()
            res3 = SendRequest.all_send_request(method=method, url=url, json=datas1, headers=headers,
                                                verify=False).json()
            end_res = end_res + res['data']['list'] + res3['data']['list']

            if len(filterConditions) != 0:
                for idx, i in enumerate(end_res):
                    for j in filterConditions:
                        if j == i['creator']:
                            end_res.pop(idx)
                final = end_res
            else:
                final = end_res

            Logger.debug(f"{one}的小车单有  {final}")
        return final
    except Exception as e:
        Logger.debug(f"捞小车单异常{e}")


# 捞小车单机器人
def robot_smallCar(data, send_url):
    method = "post"
    url = send_url
    header = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=url, method=method, headers=header, json=data, verify=False)


# 设置迭代测试人员接口
def smallCar_setPerson(data):
    url = "https://openapi.xiaoe-tools.com/ops/xe.bs.order.tester_bind/1.0.0"
    method = "post"
    res = SendRequest.all_send_request(method=method, url=url, json=data, headers=headers, verify=False)
    return res


# 创建【国内+海外elink小车】计划接口
def smallCar_createPlan(plan_name, name, last_name, date, ids, department, auth):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.create.plan/1.0.0"
    method = "post"
    datas = {
        "plan_name": plan_name + name + last_name,
        "publish_type": 1,
        "production_at": date,
        "iteration_ids": ids,
        "department_id": department,
        "auth_ids": auth,
        "devops_process_id": 10
    }
    res = SendRequest.all_send_request(method=method, url=url, json=datas, headers=Header_allTheSame(""), verify=False)
    return res


# 添加迭代进计划的接口
def smallCar_addPlan(planId, ids):
    method = "post"
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.plan.add.iterations/1.0.0"
    data = {
        "plan_id": planId,
        "iteration_ids": ids
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res


# 查询计划授权列表接口
def smallCar_findApply(planId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.apply.auth.list/1.0.0"
    method = "get"
    params = {
        "auth_type": 2,
        "plan_id": planId,
        "page_index": 1,
        "page_size": 100
    }
    res = SendRequest.all_send_request(url=url, method=method, params=params, headers=Header_allTheSame(planId), verify=False)
    return res


# 计划授权接口
def smallCar_apply(planId, ids):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.apply.auth.status/1.0.0"
    method = "PUT"
    data = {
        "auth_ids": ids,
        "auth_status": 2
    }
    res = SendRequest.all_send_request(url=url, method=method, headers=Header_allTheSame(planId), json=data, verify=False)
    return res


# 跑小车接口自动化接口
def do_jieKou(sj):
    # 自动执行接口自动化
    url1 = "https://testing-platform.test.xiaoe-tools.com/api/celery/debug_periodic_task/"
    method1 = "post"
    header = {
        "authorization": "Token 798b96b813917b67c485d617c5661a72e3593e08"
    }
    data = {
        "name": sj
    }
    res = SendRequest.all_send_request(url=url1, method=method1, headers=header, json=data, verify=False)
    return res


# 通过auth_id获取对应员工身份信息
def get_auth_meaasge():
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.order.creator.list/1.0.0"
    method = "post"
    res = SendRequest.all_send_request(url=url, method=method, headers=Header_allTheSame(""), verify=False)
    return res.json()['data']


# 计划基础信息更改接口
def change_base_plan(plan_id, plan_name, production_at, publish_type, auth_ids, ops_id):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.plan.update/1.0.0"
    method = "post"
    data = {
        "plan_id": plan_id,
        "plan_name": plan_name,
        "ops_id": ops_id,
        "production_at": production_at,
        "publish_type": publish_type,
        "auth_ids": auth_ids
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(plan_id), verify=False)
    return res


# 获取客户经理
def get_project_master(app_id):
    url = "https://alivereport.xiaoeknow.com/_panel/get_ka_name_by_appid"
    method = "post"
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "app_id": app_id
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=header, verify=False)
    return res.json()['data']


# 获取某一个代码及灰度信息
def code_gary(app_id):
    url = "https://ops.xiaoe-tools.com/ops/codegray/xe.code.gray.item.detail/1.0.0"
    method = "post"
    data = {
        "id": app_id
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=headers, verify=False)
    return res.json()['data']['e_content']


# 读取配置信息发送到群聊
def robot_send_to_other_group(data, index):
    works_url = ast.literal_eval(os.getenv("GROUP_URL"))[index]
    method1 = "POST"
    headers = {
        "Content-Type": "application/json"
    }
    SendRequest.all_send_request(url=works_url, method=method1, headers=headers, json=data, verify=False)


# 信息发送到其它群聊
def other_group(data, url):
    method1 = "POST"
    headers = {
        "Content-Type": "application/json"
    }
    res = SendRequest.all_send_request(url=url, method=method1, headers=headers, json=data, verify=False)
    return res


# 查询准现网中是否有名单
def ready_line(task_id, planId):
    url = "https://ops.xiaoe-tools.com/ops/gray_setting/get_gray_content"
    method = "post"
    data = {
        "task_id": task_id,
        "page_index": 1,
        "page_size": 10,
        "search": "",
        "label_ids": [],
        "publish_state": 100
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 根据appid查询代码级灰度
def app_id_CodeGary(app_id):
    url = 'https://openapi.xiaoe-tools.com/ops/codegray/xe.code.gray.list.by.appid/1.0.0'
    method = 'post'
    data = {
        "app_id": app_id
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=headers, verify=False)
    return res.json()


# coding 工单评论
def comment_dan(coding_id, msg):
    url = f'https://xiaoe.coding.net/api/project/10926144/issues/defects/{coding_id}/comments'
    method = 'post'
    header = {
        "cookie": f"teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; _pk_id.4.c189=9aa57baedc5bb7e0.1749441082.; _ga=GA1.1.226655824.1749723636; _ga_FVWC4GKEYS=GS2.1.s1749780221$o2$g1$t1749783287$j59$l0$h0; united=276f6616-c22f-415e-9387-6406df280f19; eid=075a0580-56ea-4f2f-b0e8-c4e0eb7b0960; enterprise_domain=xiaoe; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; clientId=269a6ecf-ee6a-419e-8574-aa998bdb8fd2; XSRF-TOKEN=f6bbc40d-2cf3-48dc-bd34-e4d98f618a37; SameSite=Lax; cf=66ff89e5d0fe17ec799346bcc5377234; coding_demo_visited=1",
        "content-type": f"application/x-www-form-urlencoded;charset=UTF-8",
        "origin": "https://xiaoe.coding.net",
        "referer": f"https://xiaoe.coding.net/p/xianwangjishugongdan/bug-tracking/issues/{coding_id}/detail",
        "x-xsrf-token": "f6bbc40d-2cf3-48dc-bd34-e4d98f618a37"
    }
    text = {
        'content': f'{msg}'
    }
    res = SendRequest.all_send_request(url=url, method=method, data=text, headers=header, verify=False)
    return res.json()


# 发布准现网、现网环境
def environment(planId, devopsId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.plan.create.task/1.0.0"
    method = "POST"
    data = {
        "auto_test_report_link": "",
        "devops_stage_id": devopsId,
        "is_skip": False,
        "plan_id": planId
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 创建群聊新接口
def new_create_group(codingId, groupName, msg, groupPerson, mention_person):
    url = 'http://digitization-ops-go-master.digitization-ops-go.svc.cluster.local/xe.digitization.coding.group.create/1.0.0'
    method = "POST"
    Header = {
        "content-type": f"application/json"
    }
    data = {
        "coding_id": codingId,
        "coding_type": 1,
        "group_name": groupName,
        "group_first_msg": msg,
        "owner_id": "stephenxiao(肖诚)",
        "group_person": groupPerson,
        "mention_person": mention_person
    }
    res = SendRequest.all_send_request(url=url, method=method, data=json.dumps(data), headers=Header, verify=False)
    return res


# 获取准现网名单发布是否成功
def push_ready_appId(task_id):
    url = 'https://openapi.xiaoe-tools.com/ops/om_release_plan/xe.bs.gray.name.task.info.get/1.0.0'
    method = "POST"
    data = {
        "task_id": task_id
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=headers, verify=False)
    return res.json()


# 根据接口查询可用小车准现网名单
def find_use_appId_list(planId, count, systems):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/gray_pool/shop/search/by_api/1.0.0"
    method = "POST"

    data = {
        "shop_num": count,
        "plan_id": planId,
        "label_ids": [131],
        "filter_label_ids": [
            104,
            20
        ],
        "cluster_ids": ["xiaoetong-pro"],
        "env": "pro",
        "product_line": "xiaoetong",
        "reqs": systems
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res


# 推荐名单接口
def recommend_appId(planId, systems):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/system_manager/plan_systems_apis_add/1.0.0"
    method = "POST"

    data = {
        "plan_id": planId,
        "product_line": "xiaoetong",
        "systems": systems
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    Logger.debug(f'推荐名单接口返回   {res.json()}')
    return res.json()


# 设置三方名单类型
def gary_other_operation(planId, task_id):
    url = "https://ops.xiaoe-tools.com/ops/gray_setting/gray_other_operation"
    method = "POST"

    data = {
        "action": "set",
        "task_id": task_id,
        "list": []
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 添加appId
def add_appId(planId, task_id, gary_content):
    url = "https://ops.xiaoe-tools.com/ops/gray_setting/add_task_gray_list"
    method = "POST"

    data = {
        "task_id": task_id,
        "gray_content": gary_content,
        "gray_way": 2
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    Logger.debug(f'添加外部名单结果   {res.json()}')
    return res.json()


# 发布准现网
def upload_appId(planId, task_id, systems_list):
    url = "https://ops.xiaoe-tools.com/ops/om_release_plan/xe.bs.release.grayname/2.0.0"
    method = "POST"

    data = {
        "delay_time": 1,
        "system_ids": systems_list,
        "task_id": task_id,
        "handle_type": "release"
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    Logger.debug(f'发布准现网外部名单结果   {res.json()}')
    return res.json()


# 获取发布计划id——list
def get_system_list(planId, task_id):
    url = "https://ops.xiaoe-tools.com/ops/om_release_plan/xe.bs.gray.name.task.info.get/1.0.0"
    method = "POST"

    data = {
        "task_id": task_id
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    Logger.debug(f'计划系统列表   {res.json()}')
    return [i['english_name'] for i in res.json()['data']['list']], [i['system_id'] for i in res.json()['data']['list']]


# 获取后端系统命中率
def get_hit(planId):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/gray_pool/query_hit_rate/1.0.0"
    method = "POST"

    data = {
        "product_line": "xiaoetong",
        "plan_id": planId
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 获取全网系统信息
def get_the_whole_network_info(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/om_release_plan/xe.bs.code.task.info.get/1.0.0"
    method = "POST"

    data = {
        "task_id": taskId
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 将全部工单扭转为 版本已全网
def change_statue_end(planId, order_ids, completion_time):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.plan.update.coding.issue.status/1.0.0"
    method = "PUT"

    data = {
        "order_ids": order_ids,
        "coding_order_stage": 145,
        "plan_id": planId,
        "completion_time": completion_time
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 归档
def back_plan(planId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.resource.recover.all/1.0.0"
    method = "POST"
    data = {
        "plan_id": planId
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 归档的另一个必要接口
def back_plan_another(planId):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/system_manager/update_plan_status/1.0.0"
    method = "POST"

    data = {
        "product_line": "xiaoetong",
        "plan_status": "archived",
        "plan_id": planId
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 数据库查询用户userid
def GetUserId(userNames, emails):
    try:
        userIds = []
        Ids = []
        with user_connect.cursor() as cursor:
            if len(userNames) != 0:
                for user_name in userNames:
                    sql = f"SELECT id, userid FROM db_user_center.t_admin_user WHERE username = '{user_name}' and state = 0"
                    cursor.execute(sql)  # 先执行SQL语句
                    rows = cursor.fetchall()  # 再获取查询结果
                    for i in rows:
                        userIds.append(list(i)[1])
                        Ids.append(list(i)[0])
            if len(emails) != 0:
                for email in emails:
                    sql = f"SELECT id, userid FROM db_user_center.t_admin_user WHERE email = '{email}' and state = 0"
                    cursor.execute(sql)  # 先执行SQL语句
                    rows = cursor.fetchall()  # 再获取查询结果
                    for i in rows:
                        userIds.append(list(i)[1])
                        Ids.append(list(i)[0])
        content = '  '.join(f'<@{i}>' for i in userIds)
        Logger.debug(f'数据库查询的userid为: {userIds}, {content}')
        return [content, Ids]
    except Exception as e:
        Logger.error(f"异常：{e}")


# 发起代码合并请求拉取分支
def batch_create(planId, taskId, systemIds):
    url = "https://ops.xiaoe-tools.com/ops/xe.system.branch.batch.create/2.0.0"
    method = "POST"

    data = {
        "branch_name": "master",
        "task_id": taskId,
        "system_ids": systemIds,
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 发起合并请求通知
def batch_merge(planId, taskId, systemIds):
    url = "https://ops.xiaoe-tools.com/ops/xe.system.branch.batch.merge/2.0.0"
    method = "POST"

    data = {
        "task_id": taskId,
        "system_ids": systemIds
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 查询代码合并是否成功
def get_is_marge(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/xe.code.merge.system.list/1.0.0"
    method = "POST"

    data = {
        "task_id": taskId,
        "task_env": "bug"
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 自动打tag
def set_tag(planId, taskId, systemList):
    url = "https://ops.xiaoe-tools.com/ops/xe.system.tag.batch.create/2.0.0"
    method = "POST"

    data = {
        "task_id": taskId,
        "system_list": systemList,
        "all_sync": 1,
        "sync_task_ids": []
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 获取codingUI自动化报告接口
def getUIReport(UID, TaskNum):
    url = f"https://xiaoe.coding.net/api/user/xiaoe/project/zidonghuaxiangmu/ci/job/{UID}/build/{TaskNum}/reports"
    method = "Get"
    Header = {
        "Cookie": f"teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; _pk_id.4.c189=9aa57baedc5bb7e0.1749441082.; _ga=GA1.1.226655824.1749723636; _ga_FVWC4GKEYS=GS2.1.s1749780221$o2$g1$t1749783287$j59$l0$h0; united=276f6616-c22f-415e-9387-6406df280f19; eid=075a0580-56ea-4f2f-b0e8-c4e0eb7b0960; enterprise_domain=xiaoe; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; clientId=269a6ecf-ee6a-419e-8574-aa998bdb8fd2; XSRF-TOKEN=f6bbc40d-2cf3-48dc-bd34-e4d98f618a37; SameSite=Lax; cf=66ff89e5d0fe17ec799346bcc5377234; coding_demo_visited=1",
        "referer": f"https://xiaoe.coding.net/p/zidonghuaxiangmu/ci/job?id={UID}"
    }
    res = SendRequest.all_send_request(url=url, method=method, headers=Header, verify=False)
    return res.json()


# 获取UI自动化执行内容
def getUIDetail(UID):
    url = f"https://xiaoe.coding.net/api/user/xiaoe/project/zidonghuaxiangmu/ci/job/{UID}/builds"
    method = "Get"
    Header = {
        "Cookie": f"teamType=1_1_0; exp=89cd78c2; code=artifact-reforge%3Dfalse%2Casync-blocked%3Dtrue%2Cauth-by-wechat%3Dtrue%2Cci-qci%3Dfalse%2Cci-team-step%3Dfalse%2Cci-team-templates%3Dfalse%2Ccoding-flow%3Dfalse%2Ccoding-ocd-java%3Dfalse%2Ccoding-ocd-pages%3Dtrue%2Centerprise-permission-management%3Dtrue%2Cmobile-layout-test%3Dfalse%2Cproject-permission-management%3Dtrue%2Cservice-exception-tips%3Dfalse%2Ctencent-cloud-object-storage%3Dtrue%2C5b585a51; _pk_id.4.c189=9aa57baedc5bb7e0.1749441082.; _ga=GA1.1.226655824.1749723636; _ga_FVWC4GKEYS=GS2.1.s1749780221$o2$g1$t1749783287$j59$l0$h0; united=276f6616-c22f-415e-9387-6406df280f19; eid=075a0580-56ea-4f2f-b0e8-c4e0eb7b0960; enterprise_domain=xiaoe; c=auth-by-wechat%3Dtrue%2Cproject-permission-management%3Dtrue%2Centerprise-permission-management%3Dtrue%2C5c58505d; clientId=269a6ecf-ee6a-419e-8574-aa998bdb8fd2; XSRF-TOKEN=f6bbc40d-2cf3-48dc-bd34-e4d98f618a37; SameSite=Lax; cf=66ff89e5d0fe17ec799346bcc5377234; coding_demo_visited=1",
        "referer": f"https://xiaoe.coding.net/p/zidonghuaxiangmu/ci/job?id={UID}"
    }
    Params = {
        "page": 1,
        "pageSize": 5,
        "isMine": "false"
    }
    res = SendRequest.all_send_request(params=Params, url=url, method=method, headers=Header, verify=False)
    return res.json()


# 零售UI自动化
def ui_self(UID, bot, peo):
    username = 'pt9uyki6zzpt'
    password = 'c7bb9977876a7a60e0f38a290a715f867e593652'
    url = f"https://xiaoe.coding.net/api/cci/job/{UID}/trigger"
    method = "post"
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "ref": "master",
        "envs": [
            {
                "name": "bot_url",
                "value": bot,
                "sensitive": 0
            },
            {
                "name": "environment",
                "value": "bug",
                "sensitive": 0
            },
            {
                "name": "contact",
                "value": peo,
                "sensitive": 0
            }
        ]
    }
    SendRequest.all_send_request(url=url, auth=(username, password), method=method, json=data, headers=header,
                                 verify=False)


# 圈子准现网ui自动化
def cycle_ui():
    username = 'pteto51o16nn'
    password = '12e7045e91ef48a37ea13b240cba57a6854e8bb8'
    url = "https://xiaoe.coding.net/api/cci/job/2792399/trigger"
    method = "post"
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "ref": "master",
        "envs": [
            {
                "name": "bot_url",
                "value": "f6066e23-0591-48a7-9b19-d22dd41b00d9",
                "sensitive": 0
            },
            {
                "name": "environment",
                "value": "bug",
                "sensitive": 0
            },
            {
                "name": "contact",
                "value": "<@zorohuang><@haideeye><@stephenxiao><@miraclesong>",
                "sensitive": 0
            },
            {
                "name": "phones",
                "value": "15507534276,17817280527,18814480943",
                "sensitive": 0
            }
        ]
    }
    SendRequest.all_send_request(url=url, auth=(username, password), method=method, json=data, headers=header,
                                 verify=False)

                            
# 根据名单自行添加名单
def BySelfAppIds(planId, appIds):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/gray_pool/get_gray_pool_by_user/1.0.0"
    method = "POST"
    data = {
        "app_ids": appIds,
        "label_ids": [131],
        "filter_label_ids": [
            104,
            20
        ],
        "env": "pro",
        "product_line": "xiaoetong",
        "gray_env": "bug",
        "cluster_ids": ["xiaoetong-pro"]
    }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    Logger.debug(f'自动添加自动化名单结果   {res.json()}')
    return res.json()


# 删除店铺名单
def delAppId(taskId, appIds, planId):
    url = "https://ops.xiaoe-tools.com/ops/gray_setting/delete_task_gray_list"
    method = "POST"
    data = {
            "task_id": taskId,
            "gray_content": appIds,
            "type": 0
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 移除店铺
def DODelAPPID(taskId, planId, appIds):
        """移除自动化店铺名单"""
        systems_id = []
        delAppId(taskId, appIds, planId)

        res_data = get_the_whole_network_info(planId, taskId)
        systems_list = res_data['data']['list']
        for i in systems_list:
                systems_id = []
                if any(v == 8 for k, v in i.get('release_patter', {}).items()):
                    pass
                else:
                     if isinstance(i['release_last_run'], list):
                         pass
                     else:
                         systems_id.append(i['system_id'])
        Logger.debug(f"移除自动化店铺名单的系统ID为：{systems_id}")
        upload_appId(planId, taskId, systems_id)


# 获取构建状态
def build_type(systems, planId):
    url = "https://ops.xiaoe-tools.com/ops/om_release_plan/xe.bs.structure.link.status/1.0.0"
    method = "POST"
    data = {
            "list": systems
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 获取配置发布信息
def componentInfo(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.component.step.get.list/1.0.0"
    method = "POST"
    data = {
            "task_id": taskId,
            "step_type": "front_config"
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()



# 获取组件库发布信息
def configInfo(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.config.step.get.list/1.0.0"
    method = "POST"
    data = {
            "task_id": taskId,
            "step_type": "config"
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 获取SQL发布信息
def SQLInfo(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.sql.step.get.list/1.0.0"
    method = "POST"
    data = {
            "task_id": taskId,
            "step_type": "db"
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


# 获取脚本发布信息
def taskInfo(planId, taskId):
    url = "https://ops.xiaoe-tools.com/ops/xe.bs.task.step.get.list/1.0.0"
    method = "POST"
    data = {
            "task_id": taskId,
            "step_type": "task"
            }
    
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


def select_appId(number, planId, label_id, culster_id):
    url = "https://ops.xiaoe-tools.com/ops/xiaoe_shop_gray_service/gray_pool/select_appid/1.0.0"
    method = "POST"
    data = {
            "label_ids": [
                label_id
            ],
            "filter_label_ids": [
                104,
                20
            ],
            "count": number,
            "env": "pro",
            "product_line": "xiaoetong",
            "cluster_ids": [
                culster_id
            ]
            }
    res = SendRequest.all_send_request(url=url, method=method, json=data, headers=Header_allTheSame(planId), verify=False)
    return res.json()


def get_current_owner(issue_title: str):
    # 设置请求头
    # token 的获取方法：项目令牌认证，请查看：https://coding.net/help/openapi#/
    headers1 = {
        "Content-Type": "application/json",
        "Authorization": "Basic cHQ3ejkwZDcxc3MxOjc0N2VjOTdlYjY1OTA1Njk0ZTJjNWNlMDQyZGExYzI1MjZjYmYyNzA="
    }

    # 设置请求的数据
    req_data = {
        "Action": "DescribeIssueListWithPage",
        "ProjectName": "xianwangjishugongdan",
        "IssueType": "DEFECT",
        "PageNumber": 1,
        "PageSize": 1,
        "Conditions": [
            {
                "Key": "KEYWORD",
                "Value": issue_title
            }
        ]
    }

    # 发送请求并获取响应
    response = SendRequest.all_send_request(url="https://xiaoe.coding.net/open-api/Action=DescribeIssueListWithPage", method="POST",headers=headers1,
                             json=req_data)

    if response.status_code != 200:
        error_msg = f"调用 coding api 异常: status_code={response.status_code}\nresponse.text={response.text}"
        Logger.exception(error_msg)

    # 获取所属bu
    belong_bu = "未知"
    try:
        response_json = response.json()
        Logger.info(f"获取工单信息：{response_json}")
        # 提取app_id并且剔除前后空格
        belong_bu = jsonpath(response_json, "$.Response.Data.List[0].CustomFields[?(@.Name == '归属BU')].RealValue")[0]
    except Exception as e:
        response_json = {}
        Logger.exception(f"获取工单信息异常：{e}")

    return belong_bu


# 根据appid查询店铺灰度信息
def get_gray_info(app_id):
    url = 'https://openapi.xiaoe-tools.com/ops/gray_pool/query_appid'
    json_body = {
        "app_id": app_id,
        "env": 'pro'
    }
    headers = {
        "Authorization": "Basic b3BzX2dhdGV3YXk6NThtU3VhcEhEMEc2b2VibndjWmZ4V1QyekJ2M3RNclE="
    }
    res = SendRequest.all_send_request(url=url, method='POST', json=json_body, headers=headers, verify=False)
    return res.json()
