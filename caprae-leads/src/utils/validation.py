import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def deduplicate_leads(leads):
    unique_leads = {}
    for lead in leads:
        email = lead.get('email')
        if email and email not in unique_leads:
            unique_leads[email] = lead
    return list(unique_leads.values())