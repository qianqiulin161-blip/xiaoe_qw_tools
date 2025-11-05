import os
from datetime import datetime
import time
from common.RedisConfig import r
from CreateGroup.test_a_MysqlDan import test_Mysql
from CreateGroup.test_b_CheckKA_f import test_checkKA
from CreateGroup.test_c_CreateQun import test_getAllDan
from CreateGroup.test_d_Quty import test_quty
from CreateGroup.test_f_GuiDang import test_back

if __name__ == '__main__':
    print(os.getenv("GRAY_FROM"))
    time1 = datetime.now().date()
    if datetime.strptime(r.get("time"), "%Y-%m-%d").date() != time1:
        r.delete("time")
        r.set("time", str(time.strftime("%Y-%m-%d")))
        r.expire('time', 129600)

        r.delete("set")
        r.set("set", "0")
        r.expire('set', 129600)

        r.delete("quty")
        r.set("quty", "0")
        r.expire('quty', 129600)

        r.delete("is_judge_back")
        r.set("is_judge_back", "0")
        r.expire('is_judge_back', 129600)

        r.delete("is_send")
        r.set("is_send", "0")
        r.expire('is_send', 129600)

        r.delete("KA_api")
        r.set("KA_api", "0")
        r.expire("KA_api", 129600)
        print(f"初始化完成，还是执行用例：{time1}")

        r.set("tag", "0")
        r.expire("KA_api", 129600)

        r.set("usingmonkey", "0")
        r.expire("usingmonkey", 129600)
    test_Mysql()
    test_checkKA()
    test_getAllDan()
    test_back()
    test_quty()