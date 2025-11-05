import ast
import os

from common.YamlUtil import read_yaml_special


def Small_Car():
    """获取小车单的相关配置"""

    department = os.getenv("Config")

    SeekOrdersTime = ast.literal_eval(os.getenv("SeekOrdersTime"))
    OrderType = ast.literal_eval(os.getenv("OrderType"))
    OrderTypeTester = ast.literal_eval(os.getenv("OrderTypeTester"))
    PartPlanName = os.getenv("PartPlanName")
    DepartmentId = int(os.getenv("DepartmentId"))
    AuthorizePersonId = ast.literal_eval(os.getenv("AuthorizePersonId"))
    AddAppIdList = ast.literal_eval(os.getenv("AddAppIdList"))
    ReviewTime = ast.literal_eval(os.getenv("ReviewTime"))
    relaxWorkDay = ast.literal_eval(os.getenv("relaxWorkDay"))
    robotWebHook = os.getenv("robotWebHook")
    AttentionNetWorkTime = ast.literal_eval(os.getenv("AttentionNetWorkTime"))
    PhoneNum = os.getenv("PhoneNum")
    Testers = ast.literal_eval(os.getenv("Testers"))
    Drivers = ast.literal_eval(os.getenv("Drivers"))
    ReviewPerson = ast.literal_eval(os.getenv("ReviewPerson"))
    DriverTag = int(os.getenv("DriverTag"))
    department_config = read_yaml_special(department)
    TesterEmail = ast.literal_eval(os.getenv("TesterEmail"))
    OverseasAddAppIdList = ast.literal_eval(os.getenv("OverseasAddAppIdList"))

    return (SeekOrdersTime, OrderType, OrderTypeTester, PartPlanName, DepartmentId, AuthorizePersonId,
            AddAppIdList, ReviewTime, relaxWorkDay, robotWebHook,
            AttentionNetWorkTime, PhoneNum, Testers, Drivers, ReviewPerson, DriverTag,
            department_config, TesterEmail, OverseasAddAppIdList)


class SmallConfig:
    """获取小车配置"""
    def __init__(self):
        self.SeekOrdersTime, self.OrderType, self.OrderTypeTester, self.PartPlanName, \
            self.DepartmentId, self.AuthorizePersonId, \
            self.AddAppIdList, self.ReviewTime, self.relaxWorkDay, self.robotWebHook, \
            self.AttentionNetWorkTime, self.PhoneNum, self.Testers, self.Drivers, \
            self.ReviewPerson, self.DriverTag, self.department_config, self.TesterEmail, \
            self.OverseasAddAppIdList = Small_Car()


smallConfig = SmallConfig()
