import os
import json
import logging


ALARM_FILE = "alarms.json"


def load_alarms():
    if os.path.exists(ALARM_FILE):
        try:
            with open(ALARM_FILE, "r") as f:
                alarms = json.load(f)
                if isinstance(alarms, list):
                    return alarms
        except Exception as e:
            logging.error(f"Error reading alarms file: {e}")
    return []


def alarm_contains(Alarm, object):
    xmin = min(Alarm.topLeft.x, Alarm.bottomRight.x)
    xmax = max(Alarm.topLeft.x, Alarm.bottomRight.x)
    ymin = min(Alarm.topLeft.y, Alarm.bottomRight.y)
    ymax = max(Alarm.topLeft.y, Alarm.bottomRight.y)
    if (object.x > xmin and object.x < xmax) and (object.y > ymin and object.y < ymax):
        return True
    return False


def trigger_alarm(objects):
    trigger_alarms = []
    if not alarms:
        return []
    alarms = load_alarms()
    for alarm in alarms:
        for obj in objects:
            if alarm_contains(alarm, obj):
                trigger_alarms.append(alarm)

    return trigger_alarms
