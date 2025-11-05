
import ast
from datetime import datetime, timedelta
from Session.test_a_find_gray import test_session
from common.RedisConfig import r


if __name__ == '__main__':
    no_use_idx = []
    if r.get("all_gray_dict"):
        all_gray_dict = ast.literal_eval(r.get("all_gray_dict"))
        for idx, item in enumerate(all_gray_dict):
            if datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S")+timedelta(days=3) <= datetime.now():
                no_use_idx.append(idx)

        for index in sorted(no_use_idx, reverse=True):
            del all_gray_dict[index]

        r.set("all_gray_dict", str(all_gray_dict))
    else:
        pass
    

    test_session()
