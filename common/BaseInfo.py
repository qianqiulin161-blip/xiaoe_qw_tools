import ast
import os


def all_project():
    Self = ast.literal_eval(os.getenv("Self"))
    return Self


class BaseConfig:
    """获取基础配置"""

    def __init__(self):
        self.Self = all_project()


baseConfig = BaseConfig()
