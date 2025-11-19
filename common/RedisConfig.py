import os
import redis as redis_lib


# redis配置信息
r = redis_lib.Redis(
    host="sh-redis-test-platform-standard.xiaoe-conf.com",
    port=6379,
    password="oXjFzTuH8PKkZFqe",
    db="1",
    decode_responses=True,
    charset='UTF-8',
    encoding='UTF-8'
)

