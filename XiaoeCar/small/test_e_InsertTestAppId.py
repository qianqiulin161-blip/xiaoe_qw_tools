from XiaoeCar.same.Same import build_plan
from XiaoeCar.small.test_g_uploadAppId import getTaskId
from common.RedisConfig import r
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from common.robot_api import BySelfAppIds

app_ids = {'AIO平台中心': 'appc5ewdhfe6373, appggkt9det3815', '教培产品中心':'appp29ib3ms1332, app4do3eacy8172, appnw3brjoj8317, appbrsddwff3517, appr24AyB7C3644, appdheztlsk2061, app3rnbir7r7831, appc89jijo16895', 'AIO平台中心数智':'', '零售产品中心':'appsB4pPlKb5930, apptlzfbqiz3807, appdlyfdtsl2016'}


# 添加测试名单
def upload_code():
    plan_id = r.get(smallConfig.department_config[4])
    department = smallConfig.PartPlanName
    department_appid = app_ids[department]

    add_appid_res = BySelfAppIds(plan_id, department_appid)
    Logger().info(f"添加测试名单返回结果：{add_appid_res}")
    
    if len(add_appid_res['is_use_list']) == 0:
        Logger().info("没有可添加的AppId，请手动添加")
    else:
        


