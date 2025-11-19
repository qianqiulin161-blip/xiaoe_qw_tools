import ast
from datetime import datetime, timedelta
from chinese_calendar import is_workday, is_holiday
from common.Exception import catch_exception
from common.Log import Logger
from common.RedisConfig import r
from common.RedisKey import RedisKeyManager
from common.robot_api import GetUserId


# 获取要@的测试人员和发车人员
def get_week_person(Testers1, ReviewPerson1, Drivers1, DriverTag1):
    from common.Small_Car_BaseInfo import smallConfig
    # 计算本周周一和周日
    current_date = datetime.now()
    monday = current_date - timedelta(days=current_date.weekday())
    sunday = monday + timedelta(days=6)
    # 生成键名（格式：月日-月日）
    date_key = f"{monday.strftime('%Y%m%d')}-{sunday.strftime('%Y%m%d')}"

    today = f"{current_date.now().date().strftime('%Y-%m-%d')}"

    if r.get(RedisKeyManager().get_key('PersonOfWeek')):
        cache = ast.literal_eval(r.get(RedisKeyManager().get_key('PersonOfWeek')))
        if cache[0] == date_key:
            tester = Testers1[cache[1]]
            personOfReview = ReviewPerson1[cache[2]]
        elif cache[0] != date_key:
            if (len(Testers1) == cache[1] + 1) and (len(ReviewPerson1) == cache[2] + 1):
                r.set(RedisKeyManager().get_key('PersonOfWeek'), str([date_key, 0, 0]))
                tester = Testers1[0]
                personOfReview = ReviewPerson1[0]
            elif len(Testers1) == cache[1] + 1:
                r.set(RedisKeyManager().get_key('PersonOfWeek'), str([date_key, 0, cache[2] + 1]))
                tester = Testers1[0]
                personOfReview = ReviewPerson1[cache[2] + 1]
            elif len(ReviewPerson1) == cache[2] + 1:
                r.set(RedisKeyManager().get_key('PersonOfWeek'), str([date_key, cache[1] + 1, 0]))
                tester = Testers1[cache[1] + 1]
                personOfReview = ReviewPerson1[0]
            else:
                r.set(RedisKeyManager().get_key('PersonOfWeek'), str([date_key, cache[1] + 1, cache[2] + 1]))
                tester = Testers1[cache[1] + 1]
                personOfReview = smallConfig.ReviewPerson[cache[2] + 1]
            Logger.debug(f'这周负责小车的测试为{tester}  评审人员为{personOfReview}')
    else:
        r.set(RedisKeyManager().get_key('PersonOfWeek'), str([date_key, 0, 0]))
        tester = Testers1[0]
        personOfReview = ReviewPerson1[0]
    Logger.info(f'今日小车测试人员和评审人员为：{tester} {personOfReview}')

    if r.get(RedisKeyManager().get_key('Driver')):
        driver_cache = ast.literal_eval(r.get(RedisKeyManager().get_key('Driver')))
        if DriverTag1 == 1:
            if driver_cache[0] == today:
                driver = Drivers1[driver_cache[1]]
            elif driver_cache[0] != today:
                if len(Drivers1) == driver_cache[1] + 1:
                    r.set(RedisKeyManager().get_key('Driver'), str([today, 0]))
                    driver = Drivers1[0]
                else:
                    r.set(RedisKeyManager().get_key('Driver'), str([today, driver_cache[1] + 1]))
                    driver = Drivers1[driver_cache[1] + 1]

        if DriverTag1 == 7:
            is_in_week = is_in_same_week(datetime.strptime(driver_cache[0], '%Y-%m-%d').date())
            if is_in_week is True:
                driver = Drivers1[driver_cache[1]]
            elif is_in_week is False:
                if len(Drivers1) == driver_cache[1] + 1:
                    r.set(RedisKeyManager().get_key('Driver'), str([today, 0]))
                    driver = Drivers1[0]
                else:
                    r.set(RedisKeyManager().get_key('Driver'), str([today, driver_cache[1] + 1]))
                    driver = Drivers1[driver_cache[1] + 1]
    else:
        r.set(RedisKeyManager().get_key('Driver'), str([today, 0]))
        driver = smallConfig.Drivers[0]
    Logger.debug(f'今日发车人员为： {driver}')

    return tester, personOfReview, driver


def is_in_same_week(target_date):
    """
    判断目标日期是否在当天所在的周内（包含当天）
    """
    today = datetime.now().date()
    start_of_this_week = today - timedelta(days=today.weekday())
    end_of_this_week = start_of_this_week + timedelta(days=6)
    return start_of_this_week <= target_date <= end_of_this_week


@catch_exception(Logger)
def at_person():
    isWork = is_workday(datetime.now().date())
    isHoliday = is_holiday(datetime.now().date())
    weekDay = datetime.now().date().today().weekday()

    from common.Small_Car_BaseInfo import smallConfig
    
    if isWork or smallConfig.PartPlanName == '电商产品中心':
        testers, personOfReviews, drivers = get_week_person(smallConfig.Testers, smallConfig.ReviewPerson,
                                                            smallConfig.Drivers, smallConfig.DriverTag)
        at = GetUserId(personOfReviews, [])[0]
        at_tester = GetUserId(testers, [])[0]
        at_driver = GetUserId(drivers, [])[0]
        at_tester_Id = GetUserId(testers, [])[1]
        at_driver_Id = GetUserId(drivers, [])[1]
    elif isHoliday or weekDay in smallConfig.relaxWorkDay:
        at_list = ast.literal_eval(r.get(RedisKeyManager().get_key('YesterdayPersonofWeek')))
        at = at_list[0]
        at_tester = at_list[1]
        at_driver = at_list[2]
        at_tester_Id = None
        at_driver_Id = None
    
    return at, at_tester, at_driver, at_tester_Id, at_driver_Id
