import openai
from config.api_keys import GOOGLE_API_KEY

class EmailGenerator:
    def __init__(self):
        openai.api_key = GOOGLE_API_KEY

    def generate_email(self, lead_info):
        prompt = f"Create a personalized outreach email for the following lead: {lead_info}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    def send_email(self, recipient, subject, body):
        # Implementation for sending email using SendGrid or similar service
        pass