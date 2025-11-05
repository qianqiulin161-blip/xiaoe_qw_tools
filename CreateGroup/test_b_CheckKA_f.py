import ast
import logging

from common import robot_api
from common.Log import Logger
from common.RedisConfig import r

def test_checkKA():
        alone(r.lrange('allDan', 0, -1))
        


def alone(dan):
    if r.get("set") == "0":
        ids = set([ast.literal_eval(item)[0] for item in dan])
        # 查询所有已拉群的单的id
        all_dan = set(r.lrange('is_create', 0, -1))
        # 获取两个集合的交集
        congFu = list(ids.intersection(all_dan))

        Logger.debug(f"重复的单为：{congFu},  即将删除")

        r.delete("is_create")
        r.delete('remind')
        for i in congFu:
            r.rpush("is_create", i)
            r.rpush("remind", i)
        r.persist("is_create")
        r.persist("remind")
        r.set("set", "1")
    else:
        Logger.debug("redis已清楚多余数据")
