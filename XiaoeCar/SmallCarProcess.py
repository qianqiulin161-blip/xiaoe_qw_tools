import ast
from datetime import datetime, timedelta
import time
from XiaoeCar.same.Same import judge_plan
from XiaoeCar.small.test_c_makePlan import test_makePlan
from XiaoeCar.small.test_d_souquan import test_shouQuan
from XiaoeCar.small.test_e_createEvn import test_selfRunJieKou
from XiaoeCar.small.test_e_outSideGray import test_outSideGray
from XiaoeCar.small.test_f_comeback import test_comeback
from common.Log import Logger
from common.Small_Car_BaseInfo import smallConfig
from common.RedisConfig import r
from common.RedisKey import RedisKeyManager
from common.robot_api import get_plan_detail
from chinese_calendar import is_workday, is_holiday
from XiaoeCar.same.at_person  import at_tester, at, at_driver
from XiaoeCar.same.SelfRun_API_UI_Enum import MessageTemplate


class Process:
    def __init__(self):
        self.isWork = is_workday(datetime.now().date())
        self.isHoliday = is_holiday(datetime.now().date())
        self.weekDay = datetime.now().date().today().weekday()
        
        if  self.isWork or self.weekDay in smallConfig.relaxWorkDay: 
            self.Base()
        # 今日小车计划id
        self.plan_id, self.yesterdat_plan_id = judge_plan()

        # 今日小车环境任务dict
        if self.plan_id:
            self.task_id_dict = self.getTaskId(self.plan_id)
        else:
            self.task_id_dict = {}
        
        # 昨日小车环境任务dict
        if self.yesterdat_plan_id:
            self.yesterdat_task_id_dict = self.getTaskId(self.yesterdat_plan_id)
        else:
            self.yesterdat_task_id_dict = {}

        # 昨日小车值班测试、司机
        self.review_person, self.y_tester, self.y_driver = ast.literal_eval(r.get(RedisKeyManager().get_key('YesterdayPersonofWeek')))[0], ast.literal_eval(r.get(RedisKeyManager().get_key('YesterdayPersonofWeek')))[1], ast.literal_eval(r.get(RedisKeyManager().get_key('YesterdayPersonofWeek')))[2]
        Logger.debug(f"今日计划id {self.plan_id}    昨日计划id {self.yesterdat_plan_id}   今日环境id字典 {self.task_id_dict}   昨日环境id字典 {self.yesterdat_task_id_dict}   昨日小车测试和司机{self.review_person}、{self.y_tester}、{self.y_driver}")


    def getTaskId(self, pid):
        """获取taskId"""
        all_task_id = {}
        task_data = get_plan_detail(pid).json()
        if len(task_data['data']['task_list']) == 0:
            return all_task_id
        elif len(task_data['data']['task_list']) != 0:
            for i in task_data['data']['task_list']:
                all_task_id[i['devops_stage_name']] = i['id']
            return all_task_id
        
    
    def Base(self):
        time1 = datetime.now().date()
        if r.get(RedisKeyManager().get_key('TodayTime')) is None:
            r.set(RedisKeyManager().get_key('TodayTime'), str((time1 - timedelta(days=1)).strftime("%Y-%m-%d")))
        if datetime.strptime(r.get(RedisKeyManager().get_key('TodayTime')), "%Y-%m-%d").date() != time1:

            r.delete(RedisKeyManager().get_key('ColumnErrorToasted'))

            r.delete(RedisKeyManager().get_key('ColumnErrorId'))

            r.set("remind_self", '0')

            r.delete(RedisKeyManager().get_key('DanErrorToast'))

            r.delete(RedisKeyManager().get_key('NOSystemError'))

            r.delete(smallConfig.PartPlanName) # 清空小车接口自动化执行结果

            # for one_type in smallConfig.OrderType:
            #     r.delete(f"roundRobinIndex{one_type}")
            # r.delete("setPersonAll" + smallConfig.PartPlanName)

            # 重置time.yaml中的值
            r.set(RedisKeyManager().get_key('TodayTime'), str(time.strftime("%Y-%m-%d")))

            r.set(RedisKeyManager().get_key('WholeNetworkReport'), '0')

            r.set(RedisKeyManager().get_key('OutsideGrayIndex'), '0')
            r.set(RedisKeyManager().get_key('OverseaGrayIndex'), '0')

            r.set(RedisKeyManager().get_key('EvnTag'), '0')
            
            # 重置小车下车比对信息
            r.delete(RedisKeyManager().get_key('PlanContent'))

            # 1.0
            r.set(RedisKeyManager().get_key('IsCreatePlan'), "0")
            if r.get(RedisKeyManager().get_key('PlanId')):
                r.set(RedisKeyManager().get_key('YesterdatPlanId'), r.get(RedisKeyManager().get_key('PlanId')))
                r.delete(RedisKeyManager().get_key('PlanId'))
                # 提醒一次小车验证
                r.set(RedisKeyManager().get_key('RemindTest'), "0")
            else:
                r.delete(RedisKeyManager().get_key('YesterdatPlanId'))
                r.set(RedisKeyManager().get_key('RemindTest'), "0")
            
            for k,v in MessageTemplate.env_dict.items():
                r.set(f'RemindTest_{k}_{smallConfig.PartPlanName}', "0")

        Logger.debug(
            f"time记录的日期是 {r.get(RedisKeyManager().get_key('TodayTime'))}   今日计划planId {r.get(RedisKeyManager().get_key('PlanId'))}    提醒验证小车标签 {r.get(RedisKeyManager().get_key('RemindTest'))}")

        
    
    def All_Process(self):
        end_time = datetime.strptime(f"{datetime.now().date()} 22:08:00", "%Y-%m-%d %H:%M:%S")
        start_time = datetime.strptime(f"{datetime.now().date()} 21:58:00", "%Y-%m-%d %H:%M:%S")
        if start_time < datetime.now() < end_time:
            r.set(RedisKeyManager().get_key('YesterdayPersonofWeek'), str([at, at_tester, at_driver]))
    
        if smallConfig.PlanId != '无':
            r.set(RedisKeyManager().get_key('PlanId'), smallConfig.PlanId)
            r.set(RedisKeyManager().get_key('IsCreatePlan'), "1")

        if self.isWork and self.weekDay not in smallConfig.relaxWorkDay:
            if self.yesterdat_plan_id:
                test_comeback(self.yesterdat_plan_id, self.yesterdat_task_id_dict, self.y_tester, self.y_driver)

            test_makePlan()
            Logger.debug("111111111111111111111111111111111111111111111111111")

            test_shouQuan(self.plan_id, self.yesterdat_plan_id)
            Logger.debug("2222222222222222222222222222222222222222222222222222222")
            
            if self.plan_id:
                test_selfRunJieKou(self.plan_id, self.task_id_dict)
                Logger.debug("333333333333333333333333333333333333333333333")
                test_outSideGray(self.plan_id, self.task_id_dict)
        elif self.weekDay in smallConfig.relaxWorkDay:
            if self.yesterdat_plan_id:
                test_comeback(self.yesterdat_plan_id, self.yesterdat_task_id_dict, self.y_tester, self.y_driver)
        elif self.isHoliday:
            pass
            
