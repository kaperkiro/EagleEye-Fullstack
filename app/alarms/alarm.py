import os
import json
from app.logger import get_logger

logger = get_logger("ALARM")

class Alarm:
    def __init__(self, id, topLeft, bottomRight, active, triggered):
        self.id = id
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.active = active
        self.triggered = triggered

    def __repr__(self):
        return f"Alarm(id={self.id}, topLeft={self.topLeft}, bottomRight={self.bottomRight}, active={self.active}, triggered={self.triggered})"
    
    def alarm_contains(self, position: tuple):
        """Check if the given position is within the alarm zone."""
        if not self.active or self.triggered:
            return False
        x, y = position
        tl_x, tl_y = self.topLeft["x"], self.topLeft["y"]
        br_x, br_y = self.bottomRight["x"], self.bottomRight["y"]
        return tl_x <= x <= br_x and tl_y <= y <= br_y
    
    def disable_alarm(self):
        self.active = False
        self.triggered = False

    def enable_alarm(self):
        self.active = True
        self.triggered = False

    def trigger_alarm(self):
        self.triggered = True

    def untrigger_alarm(self):
        self.triggered = False

    def create_from_json(json_data):
        """Create an Alarm object from JSON data."""
        return Alarm(
            id=json_data["id"],
            topLeft=json_data["topLeft"],
            bottomRight=json_data["bottomRight"],
            active=json_data["active"],
            triggered=json_data["triggered"]
        )

class AlarmManager:
    def __init__(self):
        self.alarms = None
        self.active_alarms = None
        self.triggered_alarms = None
        self.alarm_file = os.path.join(os.path.dirname(__file__), "alarms.json")
        self.load_alarms()

    def load_alarms(self):
        if os.path.exists(self.alarm_file):
            try:
                with open(self.alarm_file, "r") as f:
                    alarms_file = json.load(f)
                    if isinstance(alarms_file, list):
                        self.alarms = [Alarm(**alarm) for alarm in alarms_file]
                        self.active_alarms = [alarm for alarm in self.alarms if alarm.active]
                        self.triggered_alarms = [alarm for alarm in self.alarms if alarm.triggered]
            except Exception as e:
                logger.error(f"Error reading alarms file: {e}")
        else:
            self.alarms = []
            self.active_alarms = []
            self.triggered_alarms = []
            logger.info(f"Alarms file {self.alarm_file} not found. Creating a new one.")
            with open(self.alarm_file, "w") as f:
                json.dump([], f, indent=4)
                logger.info(f"Created new alarms file: {self.alarm_file}")
    
    def check_alarms(self, position):
        if not self.active_alarms:
            return
        for alarm in self.active_alarms:
            if alarm.alarm_contains(position):
                alarm.trigger_alarm()
                self.triggered_alarms.append(alarm)
                logger.info(f"Alarm {alarm.id} triggered by object at {position}")
                # Save the alarm to the file
                with open(self.alarm_file, "w") as f:
                    json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
                logger.info(f"Saved triggered alarm to {self.alarm_file}")

    def get_alarms_file(self):
        """Get the alarms from the file."""
        if os.path.exists(self.alarm_file):
            with open(self.alarm_file, "r") as f:
                if os.path.getsize(self.alarm_file) == 0:
                    return []
                try:
                    alarms = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON from {self.alarm_file}")
                    return []
                return alarms
        else:
            return []
    
    def add_alarm(self, alarm: json):
        new_alarm = Alarm.create_from_json(alarm)
        self.alarms.append(new_alarm)
        self.active_alarms.append(new_alarm)
        
        # Save the alarm to the file
        with open(self.alarm_file, "w") as f:
            json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
        logger.info(f"Added new alarm: {new_alarm.id}")

    def remove_alarm(self, alarm_id):
        self.alarms = [alarm for alarm in self.alarms if alarm.id != alarm_id]
        self.active_alarms = [alarm for alarm in self.active_alarms if alarm.id != alarm_id]
        self.triggered_alarms = [alarm for alarm in self.triggered_alarms if alarm.id != alarm_id]
        # Remove the alarm from the file
        with open(self.alarm_file, "w") as f:
            json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
        logger.info(f"Removed alarm: {alarm_id}")

    def toggle_alarm(self, alarm_id):
        for alarm in self.alarms:
            if alarm.id == alarm_id:
                if alarm.active:
                    alarm.disable_alarm()
                else:
                    alarm.enable_alarm()
                # Save the alarm to the file
                with open(self.alarm_file, "w") as f:
                    json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
                logger.info(f"Toggled alarm: {alarm_id} to {'enabled' if alarm.active else 'disabled'}")
                return True
        logger.warning(f"Alarm {alarm_id} not found")
        return False
