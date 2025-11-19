import ast
from common.Exception import catch_exception
from common.RedisKey import RedisKeyManager
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from XiaoeCar.same.at_person import at, at_tester, at_driver, at_tester_Id, at_driver_Id
from common.robot_api import get_in_plan_one_detail, smallCar_createPlan, robot_smallCar, smallCar_addPlan, in_plan,   \
    GetUserId
from common.RedisConfig import r
from datetime import datetime
from XiaoeCar.small.test_a_judgeContent import test_judgeContent
from XiaoeCar.small.test_b_setPerson import test_setPerson


def _generate_robot_message(title, reason, detail, mention):
    """生成通用机器人消息模板"""
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"<font color=\"warning\">**{title}**</font>\n\n"
                       f"**有误原因：**{reason}\n\n"
                       f"**具体原因：**{detail}\n\n"
                       f"**负责人：**{GetUserId([mention], [])[0]}\n\n"
        }
    }


def _process_error(i, error_type, error_done, new_errors, reason, detail, creator):
    """统一处理错误记录和通知"""
    error_key = f"{i}{error_type}{reason}"
    if error_key not in error_done:
        robot_smallCar(_generate_robot_message("计划操作异常", reason, detail, creator), smallConfig.robotWebHook)
    if error_key not in new_errors and '未归档' not in reason:
        new_errors.append(error_key)
        Logger.debug(f'错误名单   {new_errors}')
    return new_errors


def _build_plan_content(plan_id, name, lucky_data):
    """构建计划通知内容"""
    plan_url = f"https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{plan_id}"
    content = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"<font color=\"warning\">**{name}计划操作成功！**</font>  {at_tester}{at_driver}\n"
                       f"**小车计划：**[{smallConfig.PartPlanName}今日小车]({plan_url})\n"
                       f"<font color='green'>**请开发人员做好自测工作**</font>\n\n"
        }
    }
    for idx, (cs, kf, title, url) in enumerate(zip(*lucky_data), 1):
        Logger.debug(f"计划每个内容信息：{cs}  {kf}  {title}  {url}")
        content["markdown"]["content"] += (
            f"**{idx}、工单标题：** [{title}]({url})\n   {GetUserId([kf], [])[0]} \n\n"
        )
    Logger.debug(f"计划内容为：{content}")
    return content


def _clean_error_data(data_lists, error_indices):
    """清理错误数据"""
    if not error_indices:
        return data_lists
    for data_list in data_lists:
        for idx in reversed(error_indices):
            del data_list[idx]
    Logger.debug(f"清理后的数据为：{data_lists}")
    return data_lists


def _attempt_create_plan(plan_name, name, date_str, iteration_id, auth):
    """尝试创建计划"""
    res = smallCar_createPlan(plan_name, name, smallConfig.PartPlanName + "小版本",
                              date_str, [iteration_id], smallConfig.DepartmentId, auth)
    if '计划名字存在重复' in res.json()['msg']:
        res_other = smallCar_createPlan(plan_name, name, smallConfig.PartPlanName + "Other小版本",
                                        date_str, [iteration_id], smallConfig.DepartmentId, auth)
        return res_other.json()
    return res.json()

def _handle_successful_plan(res_data, yaml, iteration_id):
    """处理成功创建的计划"""
    plan_id = res_data['data']['plan_id']
    r.set(yaml, "1")
    r.set(RedisKeyManager().get_key('PlanId'),str(plan_id))
    Logger.debug(f"{iteration_id}为正常迭代创建计划成功")
    return plan_id


def FailedContent(res_data, iteration_id, creator, idx):
    iteration_content = []
    if '未归档' in res_data.get('msg'):
        content = '你有未归档的迭代，请先归档后再进行计划操作！'
        at = at_tester

    elif '系统未授权' in res_data.get('msg'):
        content = ' '.join(res_data.get('data'))
        at = creator[idx]
    else:
        res = get_in_plan_one_detail(iteration_id).json()
        iteration_name = res['data']['iteration_name']
        iteration_url = f'https://ops.xiaoe-tools.com/#/xiaoe_bus/workorders/detail/{iteration_id}'
        iteration_content.append(f"工单-->[{iteration_name}]({iteration_url})   与   {','.join(res_data['data']['time_conflict'])}")
        content = '\n'.join(iteration_content)
        at = creator[idx]
    return content, at


def _add_iterations_to_plan(plan_id, ids, lucky_person, lucky_name, lucky_url, people, error_done, new_errors):
    """添加迭代进计划"""
    error_ids = []
    if ids:
        for idx, iteration_id in enumerate(ids):
            res_data = smallCar_addPlan(str(plan_id), [iteration_id]).json()
            Logger.info(f"添加结果：{res_data}")
            if res_data['code'] == 0 and '补充计划迭代成功' in res_data['msg']:
                real_new_error = new_errors
            else:
                Logger.debug(f"{iteration_id}为出错迭代")
                content, at = FailedContent(res_data, iteration_id, people, idx)
                Logger.debug(f"添加工单  错误内容为：{content}  {at}")
                real_new_error = _process_error(iteration_id, "makePlan", error_done, new_errors,
                                res_data.get('msg'), content, at)
                error_ids.append(idx)

        data = _clean_error_data([ids, lucky_person, lucky_name, lucky_url, people], error_ids)
    else:
        Logger.debug("没有迭代需要添加到计划中")
        data = [[], [], [], [], []]
        real_new_error = new_errors
    return data, real_new_error


# 创建计划
def create_plan(ids, auth, name, yaml, lucky_person, lucky_name, lucky_url, people):
    Logger.debug("创建计划......")
    plan_id, bad_ids, new_errors, only_create_tag = None, [], [], 0
    date_str = datetime.now().strftime("%Y-%m-%d")
    plan_name = datetime.now().strftime("%y%m%d")
    error_done = ast.literal_eval(r.get(RedisKeyManager().get_key('DanErrorToast')) or "[]")

    for idx, i in enumerate(ids):
        res_data = _attempt_create_plan(plan_name, name, date_str, i, auth)
        Logger.info(f"创建计划的结果为：{res_data}")

        if res_data['code'] == 0 and '创建计划成功' in res_data['msg']:
            if res_data.get('data', {}).get('plan_id'):
                plan_id = _handle_successful_plan(res_data, yaml, i)
                bad_ids.append(idx)
                success_create_info = [lucky_person[idx], lucky_name[idx], lucky_url[idx], people[idx]]
                only_create_tag = 1
                break
        else:
             content, at = FailedContent(res_data, i, people, idx)
             if '未归档' in content:
                new_errors = _process_error(i, "makePlan", error_done, new_errors,
                                res_data.get('msg'), content, at)
                bad_ids.append(idx)
                break
             else:
                new_errors = _process_error(i, "makePlan", error_done, new_errors,
                                res_data.get('msg'), content, at)
                bad_ids.append(idx)
    r.set(RedisKeyManager().get_key('DanErrorToast'), str(new_errors))

    # 清理错误数据
    # 遍历包含多个列表的集合，依次对每个列表进行删除操作
    data_lists = _clean_error_data([ids, lucky_person, lucky_name, lucky_url, people], bad_ids)

    if plan_id:
        data, final_new_error = _add_iterations_to_plan(plan_id, data_lists[0], data_lists[1], data_lists[2], data_lists[3], data_lists[4], error_done, new_errors)
        Logger.debug(f"添加迭代到计划后的数据：{data}")
        if data[0]:
            data[1].append(success_create_info[0])
            data[2].append(success_create_info[1])
            data[3].append(success_create_info[2])
            data[4].append(success_create_info[3])
            robot_smallCar(_build_plan_content(plan_id, "", (data[1], data[4], data[2], data[3])), smallConfig.robotWebHook)
        elif only_create_tag == 1:
            Logger.debug(f'只提醒创建计划成功工单')
            robot_smallCar(_build_plan_content(plan_id, "", ([success_create_info[0]], [success_create_info[3]], [success_create_info[1]], [success_create_info[2]])), smallConfig.robotWebHook)
        r.set(RedisKeyManager().get_key('DanErrorToast'), str(final_new_error))
         
    return plan_id


def add_to_plan(ids, name, lucky_person, lucky_name, lucky_url, people, planId):
    error_id, new_error_done = [], []
    error_done = ast.literal_eval(r.get(RedisKeyManager().get_key('DanErrorToast')) if r.get(RedisKeyManager().get_key('DanErrorToast')) else "[]")
    Logger.debug(f"创建计划时有问题已提醒的单：  {error_done}")
    for index, i in enumerate(ids):
        # 添加迭代进计划接口
        res = smallCar_addPlan(str(planId), [i])
        Logger.info(f"添加结果  {res.json()}")
        if res.json()['code'] == 0 and '补充计划迭代成功' in res.json()['msg']:
            Logger.debug(f"{i}添加计划成功")
        else:
            Logger.debug(f"{i}为出错迭代")

            content, at = FailedContent(res.json(), i, people, index)
            new_error_done = _process_error(i, "makePlan", error_done, new_error_done,
                            res.json().get('msg'),
                            content, at)
            error_id.append(index)

    r.set(RedisKeyManager().get_key('DanErrorToast'), str(new_error_done))
     
    data_info = _clean_error_data([ids, lucky_person, lucky_name, lucky_url, people], error_id)

    if ids:
        robot_smallCar(_build_plan_content(planId, name, (data_info[1], data_info[4], data_info[2], data_info[3])), smallConfig.robotWebHook)


def judgeSystem(pId):
    new_error_done = []
    error_done = ast.literal_eval(r.get(RedisKeyManager().get_key('NOSystemError'))) if r.get(RedisKeyManager().get_key('NOSystemError')) else []
    if pId:
        res = in_plan(pId)
        if res.json()["data"]['list']:
            for item in res.json()["data"]['list']:
                Logger.debug(f"对应小车工单的系统为：   {item.get('system_list')}")
                creator = item.get("creator")

                if len(item.get("system_list")) == 0 and item.get("iteration_name") not in error_done:
                    data = {
                        "msgtype": "markdown",
                        "markdown": {
                            "content": f"**工单url：**[{item.get('iteration_name')}]({item.get('coding_order_url')})\n\n"
                                       + f"**原因：**没有添加系统，请添加相关系统\n\n"
                                       + f"**工单创建人：**{GetUserId([creator], [])[0]}"
                        }
                    }
                    Logger.debug("no system")
                    new_error_done.append(item.get("iteration_name"))
                    robot_smallCar(data, smallConfig.robotWebHook)
                elif len(item.get("system_list")) == 0 and item.get("iteration_name") in error_done:
                    new_error_done.append(item.get("iteration_name"))
                else:
                    Logger.debug("yes system")
        else:
            Logger.debug("系统检查失败！！！\n")
        r.set(RedisKeyManager().get_key('NOSystemError'), str(new_error_done))
    else:
        Logger.debug("无法检查系统")


@catch_exception(Logger)
def test_makePlan():
    all_ids, all_luck, all_url, all_name, all_creator = [], [], [], [], []
    # 获取当前时间
    now = datetime.now()
    morning_end_time = datetime.strptime(f"{now.date()} {smallConfig.SeekOrdersTime[1]}", "%Y-%m-%d %H:%M:%S")
    morning_start_time = datetime.strptime(f"{now.date()} {smallConfig.SeekOrdersTime[0]}", "%Y-%m-%d %H:%M:%S")
    if now > morning_end_time or now < morning_start_time:
        Logger.debug("当日已过捞单时间不再捞单")
        return

    Logger.debug("到达捞单时间，开始捞单")
    test_judgeContent()
    test_setPerson()

    dan_data1 = ast.literal_eval(r.get(RedisKeyManager().get_key('AllDan')) or "[]")
    Logger.debug(f"捞单存储结果为：{dan_data1}")
    # 版本1.0启用
    allPlan = r.get(RedisKeyManager().get_key('IsCreatePlan'))

    # 查找所有工单信息
    if dan_data1:
        for item in dan_data1:
            all_ids.append(item.get("iteration_id"))
            all_luck.append(item.get("tester_name"))
            all_url.append(item.get("coding_order_url"))
            all_name.append(item.get("iteration_name"))
            all_creator.append(item.get("creator"))
        Logger.debug(f"捞单结果为：{all_ids}  {all_luck}  {all_url}  {all_name}  {all_creator}")
        if allPlan == '0':
            AuthorizePerson = smallConfig.AuthorizePersonId + at_tester_Id + at_driver_Id
            create_plan(all_ids, AuthorizePerson, "", RedisKeyManager().get_key('IsCreatePlan'), all_luck, all_name, all_url,
                        all_creator)
            if r.get(RedisKeyManager().get_key('PlanId')):
                judgeSystem(r.get(RedisKeyManager().get_key('PlanId')))
            else:
                Logger.debug("无小车计划id，无需检查系统")
        # 添加迭代进计划
        elif allPlan == '1':
            add_to_plan(all_ids, "", all_luck, all_name, all_url, all_creator,
                        r.get(RedisKeyManager().get_key('PlanId')))
            judgeSystem(r.get(RedisKeyManager().get_key('PlanId')))

    else:
        Logger.debug("没有新工单")



