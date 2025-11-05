from common.Log import Logger
from common.Small_Car_BaseInfo import smallConfig
from common.robot_api import get_plan_detail, ready_line
from common.RedisConfig import r

current_plan_id = r.get(smallConfig.department_config[4])

def getTaskId(plan_id):
    """获取taskId"""
    all_task_id = {}
    task_data = get_plan_detail(plan_id).json()
    if len(task_data['data']['task_list']) == 0:
        return all_task_id
    elif len(task_data['data']['task_list']) != 0:
        for i in task_data['data']['task_list']:
            all_task_id[i['devops_stage_name']] = i['id']
        return all_task_id
    


def HadAppId():
    """获取已经发布了的AppId"""
    if getTaskId(r.get(smallConfig.department_config[4])).get('国内-准现网'):
        success_count = sum(1 for app in ready_line(
            getTaskId(r.get(smallConfig.department_config[4]))['国内-准现网'],
            r.get(smallConfig.department_config[4])
        )['data']['plan_content'] if app['publish_state'] == 1)
        return success_count
    else:
        return 0
