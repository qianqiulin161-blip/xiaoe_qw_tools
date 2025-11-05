import logging

from common.Small_Car_BaseInfo import smallConfig
from common.robot_api import smallCar_findApply, smallCar_apply
from common.Log import Logger
from common.RedisConfig import r


def test_shouQuan():
    # 版本1.0启用
    plan_ids = [str(r.get(smallConfig.department_config[4])), str(r.get(smallConfig.department_config[7]))]

    valid_plan_ids = [plan_id for plan_id in plan_ids if plan_id != 'None']

    for plan_id in valid_plan_ids:
        res = smallCar_findApply(plan_id)
        result = res.json()
        Logger.debug(f"授权-{result}")
        for item in result["data"]["list"]:
            if item["auth_status"] == 1:
                # 开始授权
                smallCar_apply(plan_id, [item["auth_id"]])
                Logger.debug("授权成功")
            else:
                Logger.debug("已授权")
