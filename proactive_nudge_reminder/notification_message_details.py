from typing import List


class NotificationMessage:
    def __init__(
        self, hospital_name: str, recipients: List[str], content: str, doctor_name: str, link_for_surgeon: str
    ):
        self.hospital_name = hospital_name
        self.recipients = recipients
        self.nudge_content = content
        self.doctor_name = doctor_name
        self.link_for_surgeon = link_for_surgeon
