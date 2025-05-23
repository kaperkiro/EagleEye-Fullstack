import os
import json
from app.logger import get_logger
from app.alarms.mail_sender import send_mail

logger = get_logger("ALARM")

"""
Alarm class represents a rectangular alarm zone defined by its top-left and bottom-right corners.
"""


class Alarm:
    def __init__(self, id, topLeft, bottomRight, active, triggered):
        """
        Initialize an Alarm instance.
        Args:
            id (str): Unique identifier for the alarm.
            topLeft (dict): Coordinates of the top-left corner (keys: 'x', 'y').
            bottomRight (dict): Coordinates of the bottom-right corner (keys: 'x', 'y').
            active (bool): Whether the alarm is currently active.
            triggered (bool): Whether the alarm has been triggered.
        """
        self.id = id
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.active = active
        self.triggered = triggered

    def __repr__(self):
        """
        Return a string representation of the Alarm.
        Returns:
            str: String showing the alarm's properties.
        """
        return f"Alarm(id={self.id}, topLeft={self.topLeft}, bottomRight={self.bottomRight}, active={self.active}, triggered={self.triggered})"

    def alarm_contains(self, position: tuple):
        """
        Check if a given position falls within the alarm's defined zone.
        Args:
            position (tuple): (x, y) coordinates to check.
        Returns:
            bool: True if the position is within the zone and the alarm is active and not yet triggered.
        """
        if not self.active or self.triggered:
            return False
        x, y = position
        tl_x, tl_y = self.topLeft["x"], self.topLeft["y"]
        br_x, br_y = self.bottomRight["x"], self.bottomRight["y"]
        return tl_x <= x <= br_x and tl_y <= y <= br_y

    def disable_alarm(self):
        """
        Disable the alarm, resetting its triggered state.
        """
        self.active = False
        self.triggered = False

    def enable_alarm(self):
        """
        Enable the alarm and reset its triggered state.
        """
        self.active = True
        self.triggered = False

    def trigger_alarm(self):
        """
        Trigger the alarm: log the event, send a notification email, and mark it as triggered.
        """
        logger.info("Triggering alarm")
        send_mail()
        self.triggered = True

    def untrigger_alarm(self):
        """
        Reset the alarm's triggered state without disabling it.
        """
        self.triggered = False

    def create_from_json(json_data):
        """
        Create an Alarm instance from a JSON-like dictionary.
        Args:
            json_data (dict): Dictionary containing alarm properties.
        Returns:
            Alarm: A new Alarm object initialized from json_data.
        """
        return Alarm(
            id=json_data["id"],
            topLeft=json_data["topLeft"],
            bottomRight=json_data["bottomRight"],
            active=json_data["active"],
            triggered=json_data["triggered"],
        )


class AlarmManager:
    """
    Manages multiple Alarm instances, handling loading from and saving to a JSON file,
    checking for triggers, and adding/removing alarms.
    """

    def __init__(self):
        """
        Initialize the AlarmManager, load existing alarms from disk,
        and categorize them into active and triggered lists.
        """
        self.alarms = None
        self.active_alarms = None
        self.triggered_alarms = None
        self.alarm_file = os.path.join(os.path.dirname(__file__), "alarms.json")
        self.load_alarms()

    def load_alarms(self):
        """
        Load alarms from the JSON file. If the file doesn't exist, create a new one.
        Categorize alarms into active and triggered lists.
        """
        if os.path.exists(self.alarm_file):
            try:
                with open(self.alarm_file, "r") as f:
                    alarms_file = json.load(f)
                    if isinstance(alarms_file, list):
                        self.alarms = [Alarm(**alarm) for alarm in alarms_file]
                        self.active_alarms = [
                            alarm for alarm in self.alarms if alarm.active
                        ]
                        self.triggered_alarms = [
                            alarm for alarm in self.alarms if alarm.triggered
                        ]
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
        """
        Check all active alarms against a given position and trigger any that match.

        Args:
            position (tuple): (x, y) coordinates of the detected object.
        """
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
        """
        Retrieve the raw alarm data from the JSON file.

        Returns:
            list: List of alarm dictionaries, or an empty list if file is missing or invalid.
        """
        if os.path.exists(self.alarm_file):
            with open(self.alarm_file, "r") as f:
                if os.path.getsize(self.alarm_file) == 0:
                    return []
                try:
                    alarms = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Alarm file {self.alarm_file} is empty.")
                    return []
                return alarms
        else:
            return []

    def add_alarm(self, alarm: json):
        """
        Add a new alarm from a dictionary, persist to disk, and mark it as active.
        Args:
            alarm_data (dict): JSON-like dictionary defining the new alarm.
        """
        new_alarm = Alarm.create_from_json(alarm)
        self.alarms.append(new_alarm)
        self.active_alarms.append(new_alarm)

        # Save the alarm to the file
        with open(self.alarm_file, "w") as f:
            json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
        logger.info(f"Added new alarm: {new_alarm.id}")

    def remove_alarm(self, alarm_id):
        """
        Remove an alarm by its ID, update in-memory lists, and persist changes.
        Args:
            alarm_id (str): ID of the alarm to remove.
        """
        self.alarms = [alarm for alarm in self.alarms if alarm.id != alarm_id]
        self.active_alarms = [
            alarm for alarm in self.active_alarms if alarm.id != alarm_id
        ]
        self.triggered_alarms = [
            alarm for alarm in self.triggered_alarms if alarm.id != alarm_id
        ]
        # Remove the alarm from the file
        with open(self.alarm_file, "w") as f:
            json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
        logger.info(f"Removed alarm: {alarm_id}")

    def toggle_alarm(self, alarm_id):
        """
        Toggle an alarm's active state by its ID and persist the change.
        Args:
            alarm_id (str): ID of the alarm to toggle.
        Returns:
            bool: True if the alarm was found and toggled; False otherwise.
        """
        for alarm in self.alarms:
            if alarm.id == alarm_id:
                if alarm.active:
                    alarm.disable_alarm()
                else:
                    alarm.enable_alarm()
                # Save the alarm to the file
                with open(self.alarm_file, "w") as f:
                    json.dump([alarm.__dict__ for alarm in self.alarms], f, indent=4)
                logger.info(
                    f"Toggled alarm: {alarm_id} to {'enabled' if alarm.active else 'disabled'}"
                )
                return True
        logger.warning(f"Alarm {alarm_id} not found")
        return False
