import datetime

class OutreachManager:
    def __init__(self):
        self.outreach_schedule = {}
        self.response_tracking = {}

    def schedule_outreach(self, lead_id, email_content, send_time):
        self.outreach_schedule[lead_id] = {
            'email_content': email_content,
            'send_time': send_time,
            'status': 'Pending'
        }

    def track_responses(self, lead_id, response):
        if lead_id in self.outreach_schedule:
            self.response_tracking[lead_id] = {
                'response': response,
                'timestamp': datetime.datetime.now()
            }
            self.outreach_schedule[lead_id]['status'] = 'Replied' if response else 'No Reply'