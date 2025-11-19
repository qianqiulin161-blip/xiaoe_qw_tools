
from common.robot_api import robot_smallCar
from functools import wraps


def catch_exception(logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数{func.__name__}执行失败: {str(e)}", exc_info=True)
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"函数{func.__name__}执行失败: {str(e)}"
                    }
                }
                robot_smallCar(data, "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=41fe706f-61c3-4969-b013-7b9078f5bb0c")
                return  None
        return wrapper
    return decorator
