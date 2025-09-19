import datetime
import zoneinfo

def intersect(list1, list2):
    return [a for a in list1 if a in list2]

def now():
    return datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin"))