class NotificationMessage:
    def __init__(self, hospital_name, recipients, content, doctor_name, link_for_surgeon):
        self.hospital_name = hospital_name
        self.recipients = recipients
        self.nudge_content = content
        self.doctor_name = doctor_name
        self.link_for_surgeon = link_for_surgeon
