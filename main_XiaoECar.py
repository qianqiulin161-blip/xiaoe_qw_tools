import time
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from common.BaseInfo import baseConfig
from common.Log import Logger
from common.robot_api import get_plan_detail, robot_app
from common.RedisConfig import r


def Base():
    time1 = datetime.now().date()
    if r.get(smallConfig.department_config[13]) is None:
        r.set(smallConfig.department_config[13], str((time1 - timedelta(days=1)).strftime("%Y-%m-%d")))
    if datetime.strptime(r.get(smallConfig.department_config[13]), "%Y-%m-%d").date() != time1:

        r.delete(smallConfig.department_config[1])

        r.delete(smallConfig.department_config[2])

        r.set("remind_self", '0')

        r.delete(smallConfig.department_config[3])

        r.delete(smallConfig.department_config[5])

        r.delete(smallConfig.PartPlanName) # 清空小车接口自动化执行结果

        # for one_type in smallConfig.OrderType:
        #     r.delete(f"roundRobinIndex{one_type}")
        # r.delete("setPersonAll" + smallConfig.PartPlanName)

        # 重置time.yaml中的值
        r.set(smallConfig.department_config[13], str(time.strftime("%Y-%m-%d")))

        r.set(smallConfig.department_config[14], "0")

        r.set(smallConfig.department_config[17], '0')

        r.set(smallConfig.department_config[18], '0')
        r.set(smallConfig.department_config[27], '0')

        r.set(smallConfig.department_config[19], '0')
        
        # 重置小车下车比对信息
        r.delete(smallConfig.department_config[25])

        # 1.0
        r.set(smallConfig.department_config[6], "0")
        if r.get(smallConfig.department_config[4]):
            r.set(smallConfig.department_config[7], r.get(smallConfig.department_config[4]))
            r.delete(smallConfig.department_config[4])
            # 提醒一次小车验证
            r.set(smallConfig.department_config[11], "0")
        else:
            r.delete(smallConfig.department_config[7])
            r.set(smallConfig.department_config[11], "0")
    Logger.debug(
        f"time记录的日期是 {r.get(smallConfig.department_config[13])}   今日计划planId {r.get(smallConfig.department_config[4])}    提醒验证小车标签 {r.get(smallConfig.department_config[11])}")


def judge_plan():
    if r.get(smallConfig.department_config[7]):
        res = get_plan_detail(r.get(smallConfig.department_config[7]))
        Logger.debug(f"准现网计划详情{res.json()}")
        if '计划不存在' in res.json()['msg']:
            r.delete(smallConfig.department_config[7])
    if r.get(smallConfig.department_config[4]):
        res = get_plan_detail(r.get(smallConfig.department_config[4]))
        if '计划不存在' in res.json()['msg']:
            r.delete(smallConfig.department_config[4])
    elif r.get(smallConfig.department_config[4]) is None:
        r.set(smallConfig.department_config[6], '0')


isWork = is_workday(datetime.now().date())
isHoliday = is_holiday(datetime.now().date())
weekDay = datetime.now().date().today().weekday()


if __name__ == '__main__':
    try:
        if baseConfig.planType == '0':
            from common.Small_Car_BaseInfo import smallConfig
            from XiaoeCar.same.at_person  import at_tester, at, at_driver
            from XiaoeCar.small.test_c_makePlan import test_makePlan
            from XiaoeCar.small.test_d_souquan import test_shouQuan
            from XiaoeCar.small.test_e_createEvn import test_selfRunJieKou
            from XiaoeCar.small.test_f_comeback import test_remind_environment
            from XiaoeCar.small.test_e_outSideGray import test_outSideGray

            end_time = datetime.strptime(f"{datetime.now().date()} 22:08:00", "%Y-%m-%d %H:%M:%S")
            start_time = datetime.strptime(f"{datetime.now().date()} 21:58:00", "%Y-%m-%d %H:%M:%S")
            if start_time < datetime.now() < end_time:
                r.set(smallConfig.department_config[22], str([at, at_tester, at_driver]))
            Logger.debug(f'昨日发车人员  {r.get(smallConfig.department_config[22])}')

            if weekDay in smallConfig.relaxWorkDay:
                Base()
                time.sleep(5)
                judge_plan()
                test_remind_environment()
            elif isWork:
                Base()
                time.sleep(5)
                judge_plan()
                Logger.debug(f'test_remind_environment()11111111111111111111111111111111111111111111')
                test_remind_environment()
                Logger.debug(f'test_makePlan()22222222222222222222222222222222222222')
                test_makePlan()
                Logger.debug(f'test_shouQuan()333333333333333333333333333333333333333333333')
                test_shouQuan()
                Logger.debug(f'test_selfRunJieKou()4444444444444444444444444444444444444444444444')
                test_selfRunJieKou()
                Logger.debug(f'test_outSideGray()5555555555555555555555555555555555555555555555')
                test_outSideGray()
            elif isHoliday:
                pass
    except Exception as e:
        Logger.debug(f"异常：{e}")


