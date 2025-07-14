import re
import json
import logging
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import openai
import time
import google.generativeai as genai
from config.api_keys import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Configure Gemini
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def gather_data(self, website_url: str) -> Dict[str, Any]:
        """Simplified company research focusing on basic info first"""
        try:
            # 1. Basic web scraping
            html_content = self._scrape_website(website_url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 2. Extract basic information
            basic_info = {
                'website_url': website_url,
                'company_name': self._extract_company_name(soup),
                'description': self._get_meta_description(soup),
                'raw_text': self._get_clean_text(soup)[:3000]  # First 3000 chars
            }
            
            # 3. Use Gemini to analyze this basic information
            prompt = """
            Based on the website content provided, analyze the company and return ONLY a valid JSON object with the following structure:
            {
                "industry": "specific industry category",
                "business_type": "B2B/B2C/Both",
                "company_stage": "Startup/Growth/Enterprise",
                "company_size": "team size estimate",
                "target_market": "primary customer segments",
                "usp": "unique selling proposition"
            }

            Company Website: %s
            Company Name: %s
            Description: %s
            Content Preview: %s

            Rules:
            1. Return ONLY the JSON object, no other text
            2. Use "Unknown" if you can't determine a value
            3. Be specific with industry categories
            4. Base conclusions on visible evidence
            """ % (
                basic_info['website_url'],
                basic_info['company_name'],
                basic_info['description'],
                basic_info['raw_text']
            )
            
            # Get Gemini response
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean the response text to ensure valid JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            # Parse JSON with error handling
            try:
                analysis = json.loads(response_text)
                logger.info(f"Successfully parsed Gemini response for {website_url}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}\nResponse: {response_text}")
                analysis = {
                    "industry": "Unknown",
                    "business_type": "Unknown",
                    "company_stage": "Unknown",
                    "company_size": "Unknown",
                    "target_market": "Unknown",
                    "usp": "Unknown"
                }
            
            # 4. Combine results
            result = {**basic_info, **analysis}
            logger.info(f"Research completed for {website_url}")
            return result
            
        except Exception as e:
            logger.error(f"Error gathering data: {str(e)}")
            return {
                "company_name": basic_info.get('company_name', 'Unknown'),
                "industry": "Unknown",
                "business_type": "Unknown",
                "company_stage": "Unknown",
                "company_size": "Unknown",
                "target_market": "Unknown",
                "usp": "Unknown"
            }

    def _analyze_with_ai(self, content: str, url: str) -> Dict[str, Any]:
        """Enhanced company analysis with tech intent detection"""
        prompt = f"""
        Analyze this website content and provide detailed company intelligence in JSON format.
        Look for specific evidence in the content for each field.
        
        URL: {url}
        Content includes main page, about page, and contact information.
        
        Required fields (ONLY include if strong evidence exists, otherwise mark as "Unknown"):
        
        1. Basic Information:
        - company_name: Look for legal entity name
        - industry: Identify specific vertical/sector
        - business_type: Find evidence of B2B/B2C focus
        - company_size: Look for team/employee count mentions
        - revenue_range: Search for revenue indicators or funding amounts
        
        2. Technology Analysis:
        - current_tech_stack: List technologies mentioned or detected
        - tech_maturity_score: Rate sophistication (0-100)
        - migration_signals: Note any platform/tool changes
        - tech_gaps: Identify missing critical technologies
        
        3. Growth Indicators:
        - hiring_status: Check for job listings/hiring mentions
        - expansion_signals: Look for new markets/products
        - funding_stage: Find funding/investor mentions
        - growth_rate: Analyze year-over-year changes
        
        4. Engagement Potential:
        - decision_maker_roles: Find mentioned leadership titles
        - pain_points: Identify stated challenges/needs
        - buying_stage: Evidence of current tool evaluation
        - competitive_products: Note competitor tools used
        
        Return clean JSON with "Unknown" for uncertain fields.
        """

        try:
            response = self.model.generate_content(prompt)
            
            # Clean and parse JSON response
            json_str = response.text.strip().strip('`').strip()
            if json_str.startswith('json'):
                json_str = json_str[4:]
                
            analysis = json.loads(json_str)
            
            # Add derived scores
            analysis['ai_score'] = self._calculate_ai_score(analysis)
            analysis['priority_badge'] = self._get_priority_badge(analysis['ai_score'])
            
            logger.info(f"Enhanced AI analysis completed for {url}")
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {}

    def _calculate_ai_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate comprehensive AI score based on multiple factors"""
        try:
            # Component scores (0-100 each)
            scores = {
                'revenue': self._score_revenue(analysis.get('revenue_range', 'Unknown')),
                'tech_maturity': analysis.get('tech_maturity_score', 50),
                'growth': self._score_growth_signals(analysis),
                'engagement': self._score_engagement_potential(analysis)
            }
            
            # Weighted average
            weights = {
                'revenue': 0.3,
                'tech_maturity': 0.25,
                'growth': 0.25,
                'engagement': 0.2
            }
            
            final_score = sum(
                scores[component] * weight 
                for component, weight in weights.items()
            )
            
            return round(final_score)
            
        except Exception as e:
            logger.error(f"Error calculating AI score: {str(e)}")
            return 50

    def _score_revenue(self, revenue_range: str) -> int:
        """Score revenue range on 0-100 scale"""
        ranges = {
            'Under $1M': 20,
            '$1M-$10M': 40,
            '$10M-$50M': 70,
            '$50M-$100M': 85,
            'Over $100M': 100,
            'Unknown': 50
        }
        return ranges.get(revenue_range, 50)

    def _score_growth_signals(self, analysis: Dict[str, Any]) -> int:
        """Score growth indicators"""
        score = 50  # Base score
        
        # Hiring status
        hiring_scores = {'Active': 30, 'Moderate': 20, 'Limited': 10}
        score += hiring_scores.get(analysis.get('hiring_status', 'Limited'), 10)
        
        # Funding stage
        funding_scores = {
            'Bootstrap': 10,
            'Seed': 15,
            'Series A': 20,
            'Series B': 25,
            'Series C+': 30,
            'Public': 20
        }
        score += funding_scores.get(analysis.get('funding_stage', 'Bootstrap'), 10)
        
        return min(score, 100)

    def _score_engagement_potential(self, analysis: Dict[str, Any]) -> int:
        """Score likelihood of successful engagement"""
        score = 50  # Base score
        
        # Buying stage
        stage_scores = {'Ready': 30, 'Evaluation': 20, 'Research': 10}
        score += stage_scores.get(analysis.get('buying_stage', 'Research'), 10)
        
        # Pain points
        score += min(len(analysis.get('pain_points', [])) * 10, 20)
        
        return min(score, 100)

    def _get_priority_badge(self, score: int) -> str:
        """Determine priority badge based on AI score"""
        if score >= 85:
            return "🔥 Hot"
        elif score >= 70:
            return "⚡ Active"
        return "💤 Dormant"

    def _enrich_company_data(self, company_name: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich company data with additional sources"""
        enriched_data = {}
        
        # Add LinkedIn search
        linkedin_url = f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"

        # Add Crunchbase search if startup
        if initial_data.get('company_stage') == 'Startup':
            crunchbase_url = f"https://www.crunchbase.com/organization/{company_name.lower().replace(' ', '-')}"
            enriched_data['crunchbase_url'] = crunchbase_url
        
        return enriched_data

    def _scrape_website(self, url: str) -> str:
        """Enhanced website scraping with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {str(e)}")
                time.sleep(1)

    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """
        Extract company name from website using multiple methods
        """
        try:
            # Method 1: Look for common meta tags
            meta_selectors = {
                'og:site_name': lambda s: s.find('meta', property='og:site_name'),
                'twitter:title': lambda s: s.find('meta', property='twitter:title'),
                'title': lambda s: s.find('title')
            }
            
            for selector_name, selector_func in meta_selectors.items():
                if element := selector_func(soup):
                    name = element.get('content', element.string)
                    if name:
                        # Clean up common suffixes
                        name = re.sub(r'\s*[|]-.*$', '', name.strip())
                        logger.info(f"Found company name in {selector_name}: {name}")
                        return name

            # Method 2: Look for company name in logo alt text
            if logo := soup.find('img', alt=re.compile(r'.*logo.*', re.I)):
                name = logo.get('alt', '').replace('logo', '').strip()
                if name:
                    logger.info(f"Found company name in logo alt text: {name}")
                    return name

            # Method 3: Look for company name in structured data
            structured_data = soup.find_all('script', type='application/ld+json')
            for data in structured_data:
                try:
                    json_data = json.loads(data.string)
                    if name := json_data.get('name'):
                        logger.info(f"Found company name in structured data: {name}")
                        return name
                except (json.JSONDecodeError, AttributeError):
                    continue

            # Method 4: Look for company name in common header elements
            header_selectors = [
                'header h1',
                '.logo',
                '#logo',
                '.brand',
                '.company-name'
            ]
            
            for selector in header_selectors:
                if element := soup.select_one(selector):
                    name = element.get_text().strip()
                    if name:
                        logger.info(f"Found company name in {selector}: {name}")
                        return name

            # Fallback: Extract domain name from URL
            domain = urlparse(soup.find('meta', property='og:url').get('content', '')).netloc
            name = domain.split('.')[0].title()
            logger.warning(f"Using fallback domain name: {name}")
            return name

        except Exception as e:
            logger.error(f"Error extracting company name: {str(e)}")
            return "Unknown Company"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract meaningful content from main areas of the page"""
        content_areas = []
        
        # Common content selectors
        selectors = [
            'main',
            'article',
            '#content',
            '.content',
            '.main-content',
            '[role="main"]'
        ]
        
        for selector in selectors:
            if elements := soup.select(selector):
                for element in elements:
                    # Remove script, style, and nav elements
                    for tag in element.find_all(['script', 'style', 'nav']):
                        tag.decompose()
                    content_areas.append(element.get_text(separator=' ', strip=True))
        
        return ' '.join(content_areas)

    def _scrape_about_page(self, base_url: str) -> str:
        """Attempt to scrape the about page"""
        about_urls = [
            f"{base_url}/about",
            f"{base_url}/about-us",
            f"{base_url}/company",
            f"{base_url}/who-we-are"
        ]
        
        for url in about_urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    return self._extract_main_content(soup)
            except:
                continue
        
        return ""

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information from the page"""
        contact_info = {
            'address': '',
            'phone': '',
            'email': '',
            'social_links': []
        }
        
        # Common contact info patterns
        try:
            # Phone: Look for patterns like (123) 456-7890 or 123-456-7890
            if phone := soup.find(text=re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')):
                contact_info['phone'] = phone.strip()

            # Email: Look for patterns like info@example.com
            if email := soup.find(text=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')):
                contact_info['email'] = email.strip()

            # Address: Look for patterns indicating a physical address
            address_patterns = [
                r'\d{1,5}\s\w+(\s\w+){1,3}',  # 123 Main St or 1234 Elm St Apt 567
                r'\b(?:[A-Za-z]+\s){1,3}\d{1,5}\b'  # Main St 123 or Elm St Apt 567 1234
            ]
            for pattern in address_patterns:
                if address := soup.find(text=re.compile(pattern)):
                    contact_info['address'] = address.strip()
                    break

            # Social links: Look for common social media URLs
            social_media = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']
            for platform in social_media:
                if link := soup.find('a', href=re.compile(f'^{platform}\\.com')):
                    contact_info['social_links'].append(link['href'])

        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
        
        return contact_info

    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the gathered data, using Gemini for enrichment"""
        try:
            # 1. Basic validation and cleaning
            cleaned_data = {}
            
            # Define validation rules for each field
            validation_rules = {
                'company_name': lambda x: x if x and x != "Unknown Company" else None,
                'industry': lambda x: x if x and x != "Unknown" else None,
                'business_type': lambda x: x if x in ['B2B', 'B2C', 'Both'] else None,
                'company_size': self._validate_company_size,
                'revenue_range': self._validate_revenue_range,
                'tech_stack': lambda x: list(set(x)) if isinstance(x, list) else [],
                'contact_info': lambda x: x if isinstance(x, dict) else {}
            }
            
            # Apply validation rules
            for key, value in data.items():
                if key in validation_rules:
                    cleaned_value = validation_rules[key](value)
                    cleaned_data[key] = cleaned_value if cleaned_value is not None else "Unknown"
                else:
                    cleaned_data[key] = value

            # 2. Use Gemini for missing critical fields
            if cleaned_data.get('company_name') and cleaned_data.get('company_name') != "Unknown":
                missing_fields = []
                for field in ['industry', 'business_type', 'company_size']:
                    if cleaned_data.get(field) in [None, "Unknown"]:
                        missing_fields.append(field)
                
                if missing_fields:
                    enriched_data = self._enrich_with_gemini({
                        'company_name': cleaned_data['company_name'],
                        'website': data.get('website_url', ''),
                        'known_info': {k: v for k, v in cleaned_data.items() if v != "Unknown"}
                    }, missing_fields)
                    cleaned_data.update(enriched_data)

            return cleaned_data

        except Exception as e:
            logger.error(f"Error in data validation: {str(e)}")
            return data

    def _validate_company_size(self, size: Any) -> str:
        """Validate and standardize company size"""
        if isinstance(size, int):
            if size < 10:
                return "1-10"
            elif size < 50:
                return "11-50"
            elif size < 200:
                return "51-200"
            elif size < 1000:
                return "201-1000"
            else:
                return "1000+"
        elif isinstance(size, str):
            size_patterns = {
                r'(?i)1-10|less than 10|small team': "1-10",
                r'(?i)11-50|small|dozen': "11-50",
                r'(?i)51-200|medium': "51-200",
                r'(?i)201-1000|large': "201-1000",
                r'(?i)1000\+|enterprise|very large': "1000+"
            }
            for pattern, category in size_patterns.items():
                if re.search(pattern, size):
                    return category
        return "Unknown"

    def _validate_revenue_range(self, revenue: Any) -> str:
        """Validate and standardize revenue range"""
        if isinstance(revenue, (int, float)):
            if revenue < 1000000:
                return "Under $1M"
            elif revenue < 10000000:
                return "$1M-$10M"
            elif revenue < 50000000:
                return "$10M-$50M"
            elif revenue < 100000000:
                return "$50M-$100M"
            else:
                return "Over $100M"
        elif isinstance(revenue, str):
            revenue_patterns = {
                r'(?i)under.*1M|<.*1M|less than.*1M': "Under $1M",
                r'(?i)1M.*10M|million.*ten': "$1M-$10M",
                r'(?i)10M.*50M': "$10M-$50M",
                r'(?i)50M.*100M': "$50M-$100M",
                r'(?i)over.*100M|>.*100M|more than.*100M': "Over $100M"
            }
            for pattern, category in revenue_patterns.items():
                if re.search(pattern, revenue):
                    return category
        return "Unknown"

    def _enrich_with_gemini(self, context: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
        """Use Gemini to enrich missing company information"""
        try:
            prompt = f"""
            Research this company and provide accurate information. The company appears to be an Indian business.
            
            Company: {context['company_name']}
            Website: {context.get('website', '')}
            
            Known Information:
            {json.dumps(context['known_info'], indent=2)}
            
            Required fields to research:
            1. Industry: Be specific (e.g., "Sustainable Fashion", "Eco-friendly Apparel")
            2. Business Type: Analyze if they sell B2B, B2C, or Both
            3. Company Stage: Based on their market presence (Startup/Growth/Enterprise)
            4. Target Market: Identify primary customer segments
            
            Search beyond the website:
            - Look for company profiles on business directories
            - Check social media presence
            - Look for news articles or press mentions
            - Analyze their product listings and pricing
            
            Format your response as JSON with:
            {{
                "field_name": {{
                    "value": "specific finding",
                    "confidence": 0-100,
                    "evidence": "brief explanation of why this conclusion was reached",
                    "source": "where this information was found"
                }}
            }}
            
            Only include high-confidence information (>70%). Mark as "Unknown" if uncertain.
            """

            response = self.model.generate_content(prompt)
            
            # Process response
            json_str = response.text.strip().strip('`').strip()
            if json_str.startswith('json'):
                json_str = json_str[4:]
                
            enriched_data = json.loads(json_str)
            
            # Extract high-confidence values with logging
            validated_data = {}
            for field, info in enriched_data.items():
                if isinstance(info, dict):
                    confidence = info.get('confidence', 0)
                    if confidence > 70:
                        validated_data[field] = info['value']
                        logger.info(f"Found {field}: {info['value']} (confidence: {confidence}%)")
                        logger.info(f"Evidence: {info.get('evidence', 'No evidence provided')}")
                    else:
                        logger.warning(f"Low confidence ({confidence}%) for {field}: {info.get('value', 'Unknown')}")
                        validated_data[field] = "Unknown"
                else:
                    validated_data[field] = "Unknown"
                
            logger.info(f"Gemini enrichment completed for {context['company_name']}")
            return validated_data
            
        except Exception as e:
            logger.error(f"Gemini enrichment failed: {str(e)}")
            return {field: "Unknown" for field in missing_fields}

    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        if meta := soup.find('meta', attrs={'name': 'description'}):
            return meta.get('content', '')
        if meta := soup.find('meta', attrs={'property': 'og:description'}):
            return meta.get('content', '')
        return ''

    def _extract_products(self, soup: BeautifulSoup) -> List[str]:
        """Extract product/service information"""
        products = []
        product_selectors = [
            '.product',
            '.product-title',
            '.product-name',
            '[class*="product"]',
            '[id*="product"]'
        ]
        
        for selector in product_selectors:
            if items := soup.select(selector):
                products.extend([item.get_text().strip() for item in items[:5]])
        
        return list(set(products))[:5]  # Return up to 5 unique products

    def _get_clean_text(self, soup: BeautifulSoup) -> str:
        """Get clean text content"""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer']):
            element.decompose()
        
        # Get text and clean it
        text = soup.get_text(separator=' ')
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

