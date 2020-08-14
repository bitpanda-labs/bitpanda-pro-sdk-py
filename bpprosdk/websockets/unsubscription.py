# pylint: skip-file
import json


class Unsubscription:

    def __init__(self, channels=None):
        self.channels = channels

    def as_json(self):
        return json.dumps({
            "type": "UNSUBSCRIBE",
            "channels": self.channels
        })
