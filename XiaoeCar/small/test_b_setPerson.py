import ast
import time
import random
from contextlib import suppress

from common.Exception import catch_exception
from common.RedisKey import RedisKeyManager
from common.Small_Car_BaseInfo import smallConfig
from common.Log import Logger
from common.robot_api import smallCar_setPerson, smallCar_getDan
from common.RedisConfig import r


def _get_redis_data(key):
    """统一处理Redis数据解析"""
    return ast.literal_eval(r.get(key) or "[]")


# def _update_redis_dict(key, field, value):
#     """原子更新Redis中的字典字段（避免读取-修改-写入的竞态问题）"""
#     current = _get_redis_data(key)
#     current[field] = value
#     r.set(key, str(current))


# 随机只能分配小车测试人员
# def test_setPerson():
#     _cleanup_error_records()
    
#     data1, result = _get_redis_data(RedisKeyManager().get_key('AllDan')), {}

#     if not data1:
#         Logger.debug("没有工单，不用设置测试人员")
#         return
    
#     # 提前统计 data1 中每个 tester_name 的计数
#     tester_count = {}
#     for item in data1:
#         tester_name = item.get('tester_name')
#         if tester_name and tester_name.strip():
#             tester_count[tester_name] = tester_count.get(tester_name, 0) + 1


#     for item in data1:
#         # 判断工单是否有测试人员
#         if item.get('tester_name'):
#             Logger.debug(f"{item.get('iteration_name')}  已经设置过测试人员")
#             continue

#         # 获取部门名称，工单id和创建人员
#         department, ids = item.get('department_id'), item.get('iteration_id')

#         for idx, one_type in enumerate(smallConfig.OrderType):
#             if r.get("setPersonAll" + smallConfig.PartPlanName) is None:
#                 """处理人员分配逻辑"""
#                 for p in smallConfig.OrderTypeTester[idx]:
#                     result[p] = tester_count.get(p, 0)
                
#                 if idx + 1 == len(smallConfig.OrderType): 
#                     r.set("setPersonAll" + smallConfig.PartPlanName, str(result))
#                     r.set(f"roundRobinIndex{one_type}", "0")

#                 Logger.debug(f"小车人员占用比   {result}")
                
#         for idx, one_type in enumerate(smallConfig.OrderType):
#             if one_type in department:
#                 _handle_person_assignment(
#                     item.get('iteration_name'),
#                     ids, one_type, idx)
#     _cleanup_error_records()


# def _handle_person_assignment(dan_name, ids, one_type, tester_idx):
#     result = _get_redis_data("setPersonAll" + smallConfig.PartPlanName)  # {测试人员: 工单数量}

#     current_index = int(r.get(f"roundRobinIndex{one_type}") or 0)  # 当前轮询位置

#     all_testers = smallConfig.OrderTypeTester[tester_idx]  # 该类型下的所有测试人员

#     real_result = {i: result.get(i, 0)  for i in all_testers}
#     Logger.debug(f"当前工单 {dan_name} 的测试人员准备分配情况: {real_result}")

#     # 当日单最少的人
#     min_count = min(real_result.values())
#     min_testers = [t for t in all_testers if real_result[t] == min_count]

#     # 计算在min_testers中的位置（避免索引越界）
#     selected_idx = current_index % len(min_testers)
#     selected_tester = min_testers[selected_idx]

#     res = smallCar_setPerson({"ids": [ids], "tester": selected_tester})
#     Logger.debug(f"添加参数人员结果{res}    ids:{ids},   tester:{selected_tester}")
#     Logger.debug(f"{dan_name}的测试人员为 {selected_tester}（当前计数：{result[selected_tester]} → {result[selected_tester] + 1})")

#     # 更新计数和轮询索引（轮询索引+1，确保下次选下一个）
#     _update_redis_dict(f"setPersonAll" + smallConfig.PartPlanName, selected_tester, result[selected_tester] + 1)
#     r.set(f"roundRobinIndex{one_type}", current_index + 1)  # 轮询位置+1


@catch_exception(Logger)
def test_setPerson():
    _cleanup_error_records()
    data1 = _get_redis_data(RedisKeyManager().get_key('AllDan'))
    cache = ast.literal_eval(r.get(RedisKeyManager().get_key('PersonOfWeek')))
    for item in data1:
        # 判断工单是否有测试人员
        if item.get('tester_name'):
            Logger.debug(f"{item.get('iteration_name')}  已经设置过测试人员")
            continue

        # 工单id和创建人员
        ids = item.get('iteration_id')
        tester = smallConfig.TesterEmail[cache[1]]
        smallCar_setPerson({"ids": [ids], "tester": tester})
    _cleanup_error_records()


def _cleanup_error_records():
    """清理错误记录"""
    error_id = sorted(set(_get_redis_data(RedisKeyManager().get_key('ColumnErrorId'))))
    Logger.debug(f"错误工单ERROR_ID: {error_id}")
    data = smallCar_getDan()
    res = [item for item in data for department in smallConfig.OrderType if department in item['department_id']]
    Logger.debug(f"处理中工单状态: {res}")
    if len(error_id) > 0 and res:
        for idx in sorted(error_id, reverse=True):
            res.pop(idx) if idx < len(res) else None
    
    r.delete(RedisKeyManager().get_key('AllDan'))
    r.set(RedisKeyManager().get_key('AllDan'), str(res))
    Logger.debug(f"最终工单状态: {res}")
    time.sleep(1)