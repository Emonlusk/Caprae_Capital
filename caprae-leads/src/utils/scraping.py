import requests
from bs4 import BeautifulSoup
import scrapy

def scrape_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to retrieve data from {url}")

def extract_tech_stack(html_content):
    """Enhanced technology stack detection"""
    soup = BeautifulSoup(html_content, 'html.parser')
    tech_stack = set()  # Use set to avoid duplicates

    # Technology signatures to look for
    tech_signatures = {
        'cloud': {
            'AWS': ['aws-', 'amazon web services', 'cloudfront', 's3.amazonaws'],
            'Azure': ['azure', 'microsoft cloud', '.azurewebsites.'],
            'GCP': ['google cloud', 'gcp', 'firebase']
        },
        'analytics': {
            'Google Analytics': ['gtag', 'google-analytics', 'GA-', 'UA-'],
            'Mixpanel': ['mixpanel'],
            'Segment': ['segment.io', 'segment.com']
        },
        'crm': {
            'Salesforce': ['salesforce', 'force.com'],
            'HubSpot': ['hubspot', 'hs-script'],
            'Zendesk': ['zendesk', 'zdassets']
        },
        'marketing': {
            'Marketo': ['marketo', 'mktoweb'],
            'Mailchimp': ['mailchimp', 'mc.js'],
            'Intercom': ['intercom', 'intercomcdn']
        }
    }

    # Check page source
    page_text = soup.get_text().lower()
    page_source = str(soup).lower()

    # Look for technology signatures
    for category, technologies in tech_signatures.items():
        for tech, signatures in technologies.items():
            for sig in signatures:
                if sig.lower() in page_source or sig.lower() in page_text:
                    tech_stack.add(tech)
                    break

    # Check meta tags and scripts
    for script in soup.find_all(['script', 'meta', 'link']):
        src = script.get('src', '')
        content = script.get('content', '')
        href = script.get('href', '')
        
        for category, technologies in tech_signatures.items():
            for tech, signatures in technologies.items():
                if any(sig.lower() in s.lower() for sig in signatures for s in [src, content, href]):
                    tech_stack.add(tech)

    return list(tech_stack)