import argparse
import os


parser = argparse.ArgumentParser(description="启动小车脚本")
parser.add_argument("--Config", type=str, help="配置文件名")
parser.add_argument("--SeekOrdersTime", type=str, help="捞单时间段")
parser.add_argument("--OrderType", type=str, help="捞单部门")
parser.add_argument("--OrderTypeTester", type=str, help="部门对应负责测试")
parser.add_argument("--PartPlanName", type=str, help="小车计划名称关键字")
parser.add_argument("--DepartmentId", type=int, help="所属部门id")
parser.add_argument("--AuthorizePersonId", type=str, help="授权人id")
parser.add_argument("--AddAppIdList", type=str, help="需要添加的appId列表")
parser.add_argument("--ReviewTime", type=str, help="评审时间段")
parser.add_argument("--relaxWorkDay", type=str, help="放松捞单的工作日")
parser.add_argument("--robotWebHook", type=str, help="机器人webhook地址")
parser.add_argument("--AttentionNetWorkTime", type=str, help="关注全网时间段")
parser.add_argument("--PhoneNum", type=str, help="电话提醒号码")
parser.add_argument("--Testers", type=str, help="测试人员名单")
parser.add_argument("--Drivers", type=str, help="司机人员名单")
parser.add_argument("--ReviewPerson", type=str, help="评审人员名单")
parser.add_argument("--DriverTag", type=int, help="司机标签")
parser.add_argument("--TesterEmail", type=str, help="测试人员邮箱")
parser.add_argument("--OverseasAddAppIdList", type=str, help="海外需要添加的appId列表")
parser.add_argument("--PlanId", type=str, help="计划ID")
parser.add_argument("--Self", type=str, help="自动化信息")
parser.add_argument("--department", type=str, help="部门list")
parser.add_argument("--iterationStage", type=str, help="迭代状态")
parser.add_argument("--CodingOrderStage", type=str, help="上线单状态")
parser.add_argument("--filterConditions", type=str, help="筛选人物条件")
parser.add_argument("--AppId", type=str, help="班车灰度名单")

args = parser.parse_args()

os.environ["Config"] = args.Config
os.environ["SeekOrdersTime"] = args.SeekOrdersTime
os.environ["OrderType"] = args.OrderType
os.environ["OrderTypeTester"] = args.OrderTypeTester
os.environ["PartPlanName"] = args.PartPlanName
os.environ["DepartmentId"] = str(args.DepartmentId)
os.environ["AuthorizePersonId"] = args.AuthorizePersonId
os.environ["AddAppIdList"] = args.AddAppIdList
os.environ["ReviewTime"] = args.ReviewTime
os.environ["relaxWorkDay"] = args.relaxWorkDay
os.environ["robotWebHook"] = args.robotWebHook
os.environ["AttentionNetWorkTime"] = args.AttentionNetWorkTime
os.environ["PhoneNum"] = args.PhoneNum
os.environ["Testers"] = args.Testers
os.environ["Drivers"] = args.Drivers
os.environ["ReviewPerson"] = args.ReviewPerson
os.environ["DriverTag"] = str(args.DriverTag)
os.environ["TesterEmail"] = args.TesterEmail
os.environ["OverseasAddAppIdList"] = args.OverseasAddAppIdList
os.environ["PlanId"] = args.PlanId
os.environ["Self"] = args.Self
os.environ["department"] = args.department
os.environ["iterationStage"] = args.iterationStage
os.environ["CodingOrderStage"] = args.CodingOrderStage
os.environ["filterConditions"] = args.filterConditions
os.environ["AppId"] = args.AppId


from XiaoeCar.SmallCarProcess import Process

if __name__ == '__main__':
   Process().All_Process()