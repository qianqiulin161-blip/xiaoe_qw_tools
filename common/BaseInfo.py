import ast
import os


def all_project():
    planType = os.getenv("PlanType")
    Self = ast.literal_eval(os.getenv("Self"))
    return planType, Self


class BaseConfig:
    """获取基础配置"""

    def __init__(self):
        self.planType, self.Self = all_project()


baseConfig = BaseConfig()
