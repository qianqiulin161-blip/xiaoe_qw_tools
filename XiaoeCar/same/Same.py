from datetime import datetime
from common.Log import Logger
from common.robot_api import BySelfAppIds, SQLInfo, add_appId, back_plan, back_plan_another, build_type, change_statue_end, componentInfo, configInfo, find_use_appId_list, gary_other_operation, get_all_no_guiDang, get_hit, get_the_whole_network_info, in_plan, push_ready_appId, ready_line, recommend_appId, robot_smallCar, select_appId, taskInfo, upload_appId
from common.RedisConfig import r


def up_appId(taskId, num, SelfAppIds, planId, label_id, culster_id, environment):
    """发布准现网名单逻辑 """

    from XiaoeCar.self.test_SelfRun_API_UI import SelfRunAPIUI
    runner = SelfRunAPIUI(planId)

    total = []
    systems, systems_id = [], []
    res = in_plan(planId).json()
    for i in res['data']['list']:
        if len(i['system_list']) != 0 or i['system_list'] is not None:
            for j in i['system_list']:
                systems.append(j['sys_en_name'])
                systems_id.append(j['system_id'])
        else:
            continue
    for s in systems:
        system_dict = {'system_name': str(s), 'query_urls': ""}
        total.append(system_dict)
    Logger.debug(f'系统传参  {total}')
    
    if len(SelfAppIds) == 0:
        res1 = find_use_appId_list(planId, num, total)

        if res1.status_code != 200 or len(res1.json()['data']['list']['is_use_list']) == 0:
            gary_other_operation(planId, taskId)
            res_data = select_appId(num, planId, label_id, culster_id)
        else:
            res_data = res1.json()
            
        # 选中可用的appid
        is_use_appId = res_data['data']['list']['is_use_list']  # array
        Logger.debug(f"本次可用名单为 {is_use_appId}  一共有{len(is_use_appId)}")

    else:
        res_data = BySelfAppIds(planId, ','.join(i for i in SelfAppIds))
        missing_self_name = [v.split('-')[0] for item in res_data['data']['filter_list_by_plan'] for k, v in item.items() if k == 'err_msg']  # 获取完整的计划名称
        is_use_appId = res_data['data']['is_use_list']
        Logger.debug(f"本次可用名单为 {is_use_appId}  一共有{len(is_use_appId)}    {r.get(runner.redisKey)}")
        # 判断自动化名单是否加入到当前计划中，直接通过
        if missing_self_name == runner._get_plan_name(): 
            return Logger.debug(f"{runner._get_plan_name()}自动化名单已加入到当前计划中"), True
        elif len(res_data['data']['filter_list_by_plan']) != 0 and r.get(runner.redisKey) == '0':
            missing_planIds = []
            missing_self_appid = [v for item in res_data['data']['filter_list_by_plan'] for k, v in item.items() if k == 'app_id']
            for i in missing_self_name:
                res = get_all_no_guiDang('', '', '', i, '')
                missing_planIds += res[0]
            content = '\n'.join(f'{i}在计划[{missing_self_name[ids]}](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{missing_planIds[ids]})' for ids, i in enumerate(missing_self_appid))
            r.set(runner.redisKey, "0.5")
            return robot_smallCar({"msgtype": "markdown",
                                    "markdown": {
                                        "content": f"<font color='red'>**{runner._get_plan_name()}自动化店铺被占用，无法添加到计划中，请注意！！！**</font>\n\n{content} \n\n {runner.tester} {runner.develop}"
                                    }}, runner.webHook), False
    
    if len(is_use_appId) != 0:
        recommend_res_data = recommend_appId(planId, total)
        if recommend_res_data['code'] != 0:
            return robot_smallCar({"msgtype": "markdown",
                                "markdown": {
                                    "content": f'推荐外部{environment}名单失败，请手动添加 {runner.develop}'
                                }}, runner.webHook), False

        # 添加名单
        def addId(appIds):
            other_add = gary_other_operation(planId, taskId)
            add_res_data = add_appId(planId, taskId,
                                    ','.join(f'{i}' for i in appIds))
            if add_res_data['code'] == 0 and other_add['code'] == 0:
                upload_appId(planId, taskId, systems_id)
            elif add_res_data['code'] == 1:
                for item in add_res_data['data']:
                    appIds.remove(item)
                addId(appIds)
            else:
                return robot_smallCar({"msgtype": "markdown",
                                    "markdown": {
                                        "content": f"{runner._get_plan_name()}   {environment}添加名单失败请关注{runner.develop}"
                                    }}, runner.webHook), False

        addId(is_use_appId)

        plan_content = ready_line(taskId, planId)

        if len(SelfAppIds) == 0:
            return robot_smallCar({"msgtype": "markdown",
                                "markdown": {
                                    "content": f"{runner._get_plan_name()}  {environment}已添加名单至 {plan_content['data']['total_count']}"
                                }}, runner.webHook), True
        if len(SelfAppIds) != 0 and len(is_use_appId) == len(SelfAppIds):
            return robot_smallCar({"msgtype": "markdown",
                                "markdown": {
                                    "content": f"{runner._get_plan_name()}  {environment}已添加准现网名单{','.join(i for i in is_use_appId)}"
                                }}, runner.webHook), True
        else:
            return Logger.debug(f"{runner._get_plan_name()}  {environment}已添加部分准现网名单{','.join(i for i in is_use_appId)}"), False
    else:
        return Logger.debug(f"{runner._get_plan_name()}  无可用名单"), False
    

def get_whole_network_statu(yId, taskId, msg, tester, driver, webHook, PlanName) -> bool:
    """获取合并代码发布系统后的系统状态"""
    all_count = []
    total = 0
    res_data = get_the_whole_network_info(yId, taskId)
    systems_list = res_data['data']['list']
    for i in systems_list:
        count = []
        if any(v == 8 for k, v in i.get('release_patter', {}).items()):
            total += 1
        else:
            if isinstance(i['release_last_run'], list):
                pass
            else:
                for l, b in i.get('release_last_run', {}).items():
                    for l1, b1 in b.items():
                        count.append(b1['last_run_state'])
                        all_count.append(b1['last_run_state'])
            if all(num in {0, 2} for num in count) is True and 2 in count:
                total += 1
    Logger.debug(f'已经发布的系统数为  {total}     实际系统数为：{len(systems_list)}')
    if total == len(systems_list):
        return True
    elif total != 0 and (r.get(msg + str(taskId)) == '0' or r.get(msg + str(taskId)) is None) and any(i in [3, 4] for i in all_count):
        robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color='res'>**{msg}**</font> {tester}{driver}\n"
                           f"[点击进入--》{PlanName}](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{yId})"
            }
        }, webHook)
        r.set(msg + str(taskId), '1')
        return False
    else:
        return False


def get_upload_appId_system_statu(planId, taskId, msg, tester, driver, webHook, PlanName) -> bool:
    """获取发布名单后的系统情况"""
    all_count = []
    total = 0
    res_data = push_ready_appId(taskId)
    systems_list = res_data['data']['list']
    for i in systems_list:
        count = []
        if any(v == 8 for k, v in i.get('release_patter', {}).items()):
            total += 1
        else:
            if isinstance(i['release_last_run'], list):
                pass
            else:
                for l, b in i.get('release_last_run', {}).items():
                    for l1, b1 in b.items():
                        count.append(b1['last_run_state'])
                        all_count.append(b1['last_run_state'])
                if all(num in {0, 2} for num in count) is True and 2 in count:
                    total += 1
    Logger.debug(f'1已经发布的系统数为  {total}     1实际系统数为：{len(systems_list)}')
    if total == len(systems_list):
        return True
    elif total != 0 and (r.get(msg + str(taskId)) == '0' or r.get(msg + str(taskId)) is None) and any(i in [3, 4] for i in all_count):
        robot_smallCar({
            "msgtype": "markdown",
            "markdown": {
                "content": f"<font color='res'>**{msg}**</font> {tester}{driver}\n"
                           f"[点击进入--》{PlanName}](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{planId})"
            }
        }, webHook)
        r.set(msg + str(taskId), '1')
        return False
    else:
        return False


def build_plan(planId, taskId):
    """获取计划构建状态"""
    in_plan_data = in_plan(planId).json()['data']['list']
    current_tag = get_the_whole_network_info(planId, taskId)['data']['list']
    system_list = []
    for i in in_plan_data:
        if len(i['system_list']) == 0:
            continue

        system_list = system_list + [{"system_id": j["system_id"], "tag_name": "", "tag_type": 3} for j in i["system_list"]]
    for item in current_tag:
        for j in system_list:
            if item['id'] == j['system_id']:
                j['tag_name'] = item['current']
                break
    Logger.debug(f"获取构建状态的参数  {system_list}")

    
    build_data = build_type(system_list, planId)['data']
    if build_data:
        piple_status = [a['piple_status'] for a in build_data]
        Logger.debug(f"系统所有构建状态为  {piple_status}")
    else:
        Logger.debug(f"系统还没有打tag")
        return  False
    
    if all(b in [1, 3] for b in piple_status):
        return True
    else:
        return False
    

def back(planId):
    res = in_plan(planId)
    order_ids = [i['iteration_id'] for i in res.json()['data']['list']]
    statue_data = change_statue_end(planId, order_ids, str(datetime.now().date()))
    Logger.debug(f'所有小车单扭转到版本已全网的状态返回值 {statue_data}')
    back_data = back_plan(planId)
    back_another_data = back_plan_another(planId)
    Logger.debug(f'归档返回值 {back_data}    {back_another_data}')


def get_hit_probability(planId):
    """全网后的系统命中率消息"""
    res_data = get_hit(planId)
    if 'data' in res_data and res_data['data']:
        project_hit_rate = res_data['data']['project_hit_rate']
        sorted_data = sorted(
            res_data['data']['gray_hit_rate'],
            key=lambda x: float(x['system_hit_rate'].strip('%')),
            reverse=False  # 升序排列
        )
        content = '   '.join(f"<font color='red'>{i['system_name']}: {i['system_hit_rate']}</font>"
                             if float(i['system_hit_rate'].strip('%')) < 30
                             else f"{i['system_name']}: {i['system_hit_rate']}"
                             for i in sorted_data)
    else:
        content = '无'
        project_hit_rate = '无后端系统'
    return project_hit_rate, content
