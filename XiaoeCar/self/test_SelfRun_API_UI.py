import ast
from datetime import datetime
from typing import Dict, List, Tuple, Any
from XiaoeCar.enum.SelfRun_API_UI_Enum import AutoStatus, MessageTemplate
from XiaoeCar.same.GetEveryDayPerson import at_person
from XiaoeCar.same.Same import up_appId
from common.BaseInfo import baseConfig
from common.Log import Logger
from common.RedisConfig import r
from common.robot_api import DODelAPPID, delAppId, do_jieKou, get_the_whole_network_info, in_plan, ui_self, ready_line, get_plan_detail, find_api, \
    robot_smallCar, getUIDetail, getUIReport, upload_appId


class SelfRunAPIUI:
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.taskName = None
        self.taskId = None
        self.webHook = None
        self.redisKey = None
        self.Self = None
        self.apiRedis = None
        self.uiRedis = None
        self.department = None
        self.tester = at_person()[1]
        self.develop = at_person()[2]
        self._init_task_info()

    def _init_task_info(self):
        """初始化任务信息"""
        task_list = self._get_task_ids()
        if not task_list:
            return

        if baseConfig.planType == '0':
            from common.Small_Car_BaseInfo import smallConfig
            self.taskId = task_list['国内-准现网']
            self.taskName = '国内-准现网'
            self.webHook = smallConfig.robotWebHook
            self.redisKey = smallConfig.department_config[24] + self.plan_id
            self.apiRedis = smallConfig.department_config[16]
            self.uiRedis = smallConfig.department_config[23]
            self.Self = baseConfig.Self['准现网']
            self.department = smallConfig.PartPlanName

        Logger.debug(f"初始化任务信息: {self.taskName}, 任务ID: {self.taskId}, WebHook: {self.webHook}, RedisKey: {self.redisKey}, API Redis: {self.apiRedis}, UI Redis: {self.uiRedis}, Tester: {self.tester}, Developer: {self.develop}, Plan ID: {self.plan_id}, self: {self.Self}")
    
    def _get_plan_name(self) -> str:
        PlanName_result = get_plan_detail(self.plan_id).json()
        PlanName = PlanName_result['data']['plan_name']
        return PlanName


    def _get_task_ids(self):
        all_task_id = {}
        task_data = get_plan_detail(self.plan_id).json()
        task_list = task_data['data']['task_list']
        if len(task_list) == 0:
            return all_task_id
        elif len(task_list) != 0:
            for i in task_list:
                all_task_id[i['devops_stage_name']] = i['id']
            return all_task_id

    def _get_All_Tester(self) -> List[str]:
        """获取已经加入计划的名单"""
        plan_content = ready_line(
            self.taskId,
            self.plan_id
        )
        if len(plan_content['data']['plan_content']) != 0:
            app_list = [app['name'] for app in plan_content['data']['plan_content']]
        else:
            app_list = []
        return app_list


    def judge_SelfAppId_In_list(self) -> List[str]:
        """判断自动化店铺是否在名单中"""
        app_list = self._get_All_Tester()
        missing = []

        for i in self.Self['appid']:
            for _, v in i.items():
                if v not in app_list:
                    missing.append(v)
        return missing

    def run_api_tests(self) -> Dict:
        """运行API测试"""
        for api in self.Self['api']:
            for k, _ in api.items():
                do_jieKou(k)
        return Logger.debug(f"{k}:API自动化已运行")

    def run_ui_tests(self) -> List:
        """运行UI测试"""
        for ui in self.Self['ui']:
            ui_self(ui[1], ui[2], ui[3])
        return  Logger.debug(f"ui自动化已执行！！！")

    def _get_api_results(self) -> Dict:
        """获取API测试结果"""
        results = []

        for api in self.Self['api']:
            for k, v in api.items():
                res = find_api(v)
                if not res.json()['results']:
                    continue

                result = res.json()['results']
                
                status = AutoStatus.PASS.value if result[0]['execute_status'] == 1 else AutoStatus.FAIL.value

                results.append({
                        'api_name': v,
                        'status': status,
                        'report_url': result[0]['report_url'],
                        'create_time': result[0]['create_time']
                    })

        return {
            'results': results,
            'content': self._format_api_results(results)
        }

    def _get_ui_status(self, ui_info: List) -> Dict:
        """获取UI测试状态"""
        res = getUIDetail(ui_info[1])
        status = res['data']['list'][0]['status']
        task_num = res['data']['list'][0]['number']

        if status in [AutoStatus.INITIALIZING.value,
                      AutoStatus.RUNNING.value,
                      AutoStatus.QUEUED.value]:
            return {
                'department': ui_info[0],
                'status': AutoStatus.RUNNING.value,
                'report': MessageTemplate.RUNNING
            }

        report_res = getUIReport(ui_info[1], task_num)
        return {
            'department': ui_info[0],
            'status': AutoStatus.PASS.value if status != 'FAILED' else AutoStatus.FAIL.value,
            'report': report_res['data'][0]['url']
        }

    @staticmethod
    def _format_api_results(results: List[Dict]) -> str:
        """格式化API测试结果"""
        return '\n'.join(
            f"{r['api_name']}: {r['status']}  报告：[{r['report_url']}]({r['report_url']})"
            for r in results
        )

    def send_error_notification(self, msg_type: str, content: str, redis_key: str):
        """发送错误通知"""
        redis_full_key = redis_key + self.plan_id
        if not r.get(redis_full_key) or content != r.get(redis_full_key):
            Logger.debug(f"发送错误通知：{msg_type.format(planName = self._get_plan_name(), content=content, at_tester=self.tester)}")
            robot_smallCar({
                "msgtype": "markdown",
                "markdown": {
                    "content": msg_type.format(planName = self._get_plan_name(), content=content, at_tester=self.tester)
                }
            }, self.webHook)
            r.set(redis_full_key, content)

    def runSelf(self):
        """运行自动化测试"""
        # 初始化返回值
        api_results = None
        ui_results = None

        missing_apps = self.judge_SelfAppId_In_list()
        if r.get(self.redisKey):
            redis_status = r.get(self.redisKey)
        else:
            redis_status = '0'
            r.set(self.redisKey, "0")
        
        try:
            if redis_status in ['0', '0.5']:
                if missing_apps:
                    Logger.debug(f"自动化店铺不在名单中，缺失的店铺: {missing_apps}")
                    _, is_added = up_appId(self.taskId, '', missing_apps, self.plan_id, 131, "xiaoetong-pro", '国内-准现网')
                    if is_added is False:
                        Logger.debug('自动添加自动化店铺失败')
                        return None, None
                    
                    Logger.debug('自动添加自动化店铺成功')
                    api_results = self.run_api_tests()
                    ui_results = self.run_ui_tests()
                    robot_smallCar({
                                        "msgtype": "markdown",
                                        "markdown": {
                                            "content": f"**{self._get_plan_name()}    {self.taskName}   接口/UI自动化已执行 {self.tester}, 请关注!**\n"
                                        }
                                    }, self.webHook)
                    r.set(self.redisKey, "1")
                else:
                    api_results = self.run_api_tests()
                    ui_results = self.run_ui_tests()
                    robot_smallCar({
                                        "msgtype": "markdown",
                                        "markdown": {
                                            "content": f"**{self._get_plan_name()}   {self.taskName}    接口/UI自动化已执行 {self.tester}, 请关注!**\n"
                                        }
                                   }, self.webHook)
                    r.set(self.redisKey, "1")

            elif redis_status in ['1', '2']:
                api_results = self._get_api_results()
                ui_results = [
                    self._get_ui_status(ui) 
                    for ui in self.Self['ui']
                ]
            else:
                Logger.debug(f"Unexpected redis status: {redis_status}")
                return None, None
        except Exception as e:
            Logger.error(f"Error during automation run: {e}")
            return None, None
        
        return api_results, ui_results


def keep_result(plan_id, api_results, ui_results):
    # 将自动化结果存入redis
    runner = SelfRunAPIUI(plan_id)
    if r.get(runner.department) is None:
        api_final_result = []
    else:
        api_final_result = ast.literal_eval(r.get(runner.department))
        
    if api_results:
        api_is_pass = [i['status'] for i in api_results['results']]
        api_final_result.append(api_is_pass)
        if baseConfig.planType == '0':
            r.set(runner.department, str(api_final_result))
    else:
        pass


def run_automation(plan_id: str):
    """运行自动化测试入口"""
    runner = SelfRunAPIUI(plan_id)

    api_results, ui_results = runner.runSelf()
    Logger.debug(f"API自动化结果: {api_results}")
    Logger.debug(f"UI自动化结果: {ui_results}")

    keep_result(plan_id, api_results, ui_results)
    # 检查并发送错误通知
    if api_results:
        for idx, i in enumerate(api_results['results']):
            create_datetime = datetime.strptime(i['create_time'], "%Y-%m-%d %H:%M:%S")
            today = datetime.now().date()
            if i['status'] == AutoStatus.PASS.value or create_datetime.date() != today:
                api_results['results'].pop(idx)
        
        if api_results['results']:
            content = '\n'.join(
                f"{i['api_name']}: {i['status']}  报告：[{i['report_url']}]({i['report_url']})"
                for i in api_results['results']
            )
            runner.send_error_notification(
                MessageTemplate.API_ERROR,
                content,
                runner.apiRedis
            )
    else:
        Logger.debug(f'接口自动化结果为None')

    if ui_results:
        if any(i['status'] == AutoStatus.FAIL.value for i in ui_results):
            ui_content = '\n'.join(
                f"{i['department']}UI自动化: {i['status']}  报告：[{i['report']}]({i['report']})"
                for i in ui_results if i['status'] == 'FAIL'
            )
            runner.send_error_notification(
                MessageTemplate.UI_ERROR,
                ui_content,
                runner.uiRedis
            )
    else:
        Logger.debug(f'UI自动化结果为None')
    
    if ui_results and api_results and r.get(runner.redisKey) == '1':
        if all(i['status'] == AutoStatus.PASS.value for i in api_results['results']) and all(
                i['status'] == AutoStatus.PASS.value for i in ui_results):
            
            # """移除自动化店铺名单"""
            # appids = ','.join(v for i in runner.Self['appid'] for k, v in i.items())
            # DODelAPPID(runner.taskId, runner.plan_id, appids)
            r.set(runner.redisKey, "2")
