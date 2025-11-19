import argparse
import ast
import os


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
    TesterEmail = ast.literal_eval(os.getenv("TesterEmail"))
    OverseasAddAppIdList = ast.literal_eval(os.getenv("OverseasAddAppIdList"))
    PlanId = os.getenv("PlanId")
    Self = ast.literal_eval(os.getenv("Self"))
    department_list = ast.literal_eval(os.getenv("department"))
    iterationStage = ast.literal_eval(os.getenv("iterationStage"))
    CodingOrderStage = ast.literal_eval(os.getenv("CodingOrderStage"))
    filterConditions = ast.literal_eval(os.getenv("filterConditions"))
    AppId = os.getenv("AppId")

    return (department,SeekOrdersTime, OrderType, OrderTypeTester, PartPlanName, DepartmentId, AuthorizePersonId,
            AddAppIdList, ReviewTime, relaxWorkDay, robotWebHook,
            AttentionNetWorkTime, PhoneNum, Testers, Drivers, ReviewPerson, DriverTag,
            TesterEmail, OverseasAddAppIdList, PlanId, Self, department_list, iterationStage, 
            CodingOrderStage, filterConditions, AppId)


class SmallConfig:
    """获取小车配置"""
    def __init__(self):
        self.department, self.SeekOrdersTime, self.OrderType, self.OrderTypeTester, self.PartPlanName, \
            self.DepartmentId, self.AuthorizePersonId, \
            self.AddAppIdList, self.ReviewTime, self.relaxWorkDay, self.robotWebHook, \
            self.AttentionNetWorkTime, self.PhoneNum, self.Testers, self.Drivers, \
            self.ReviewPerson, self.DriverTag, self.TesterEmail, \
            self.OverseasAddAppIdList, self.PlanId, self.Self, self.department_list, \
            self.iterationStage, self.CodingOrderStage, self.filterConditions, self.AppId = Small_Car()


smallConfig = SmallConfig()
