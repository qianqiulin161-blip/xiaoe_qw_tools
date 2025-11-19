from enum import Enum

class AutoStatus(Enum):
    INITIALIZING = 'INITIALIZING'
    RUNNING = 'RUNNING'
    QUEUED = 'QUEUED'
    FAILED = 'FAILED'
    PASS = 'PASS'
    FAIL = 'FAIL'


class MessageTemplate:
    API_ERROR = "{planName}   ** 接口自动化执行错误 **：{content}  {at_tester}\n"
    UI_ERROR = "{planName}   ** UI自动化执行错误 **：{content}  {at_tester}\n"
    RUNNING = "自动化正在执行中..."
    env_dict = {"国内-准现网": "国内-现网", "海外-准现网": "海外-现网"}
    env_dict_id = {"国内-准现网": 35}
