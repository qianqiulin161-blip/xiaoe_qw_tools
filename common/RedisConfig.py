import os
import redis as redis_lib


# redis配置信息
r = redis_lib.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    db=os.getenv("REDIS_DB"),
    decode_responses=True,
    charset='UTF-8',
    encoding='UTF-8'
)

