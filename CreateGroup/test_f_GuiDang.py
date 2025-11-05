import ast
import logging
from datetime import datetime, timedelta
from common.RedisConfig import r
from common.Log import Logger
from common import robot_api


def test_back():
    all_list = []

    # 查出所有未归档的教培产品中心小车计划id
    result = robot_api.get_all_no_guiDang(0, "", "", "教培产品", 3618)
    all_planId = result[0]
    plan_name = result[1]
    product_at = result[5]
    for planId in all_planId:
        name = plan_name[all_planId.index(planId)]
        time = datetime.strptime(product_at[all_planId.index(planId)], "%Y-%m-%d").date()
        today = datetime.today().date()
        data_list = []

        if planId == 'None':
            continue
        else:
            if today > time:
                data_list.append(planId)
                data_list.append(name)
                all_list.append(data_list)
              
    is_judge_back = r.get("is_judge_back")
    if datetime.now() >= datetime.now().replace(hour=9, minute=30, second=0, microsecond=0) and is_judge_back == "0":
        if len(all_list) != 0:
            qiwei_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"<font color=\"warning\">**超过归档日期还未归档的计划！！！**</font>\n\n"
                }
            }
            for i in range(len(all_list)):
                index = i + 1
                qiwei_data["markdown"]["content"] += f"\n**{index}、**\n"
                qiwei_data["markdown"]["content"] += f"\n**计划url：**\n[{all_list[i][1]}](https://ops.xiaoe-tools.com/#/xiaoe_bus/workplan/plan_details/{all_list[i][0]})\n"
                qiwei_data["markdown"]["content"] += f"**<@qiulinqian>\n"
            robot_api.robot_no_back_plan(qiwei_data)
        r.set("is_judge_back", "1")
    else:
        pass

