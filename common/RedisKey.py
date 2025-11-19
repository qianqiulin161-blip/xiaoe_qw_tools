from singleton_decorator import singleton
from common.YamlUtil import read_yaml_special
from common.Small_Car_BaseInfo import smallConfig


@singleton
class RedisKeyManager:
    def __init__(self):
        self.yaml_config = read_yaml_special(smallConfig.department)

    def get_key(self, key):
        return self.yaml_config.get(key)
    

