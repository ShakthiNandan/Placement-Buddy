import re
import json
from datetime import datetime
from dateutil import parser
from textblob import TextBlob
from bs4 import BeautifulSoup
import requests
import os

class EmailParser:
    """Service for parsing and classifying placement emails."""
    
    def __init__(self):
        self.placement_keywords = [
            'placement', 'internship', 'job', 'recruitment', 'hiring',
            'career', 'opportunity', 'position', 'opening', 'apply',
            'interview', 'selection', 'campus', 'drive', 'ctc', 'package',
            'salary', 'compensation', 'bond', 'service', 'notice', 'period'
        ]
        
        self.company_indicators = [
            'company', 'corporation', 'ltd', 'limited', 'inc', 'incorporated',
            'pvt', 'private', 'technologies', 'solutions', 'systems', 'services'
        ]
        
        self.event_keywords = [
            'interview', 'test', 'assessment', 'screening', 'round',
            'presentation', 'group discussion', 'gd', 'technical',
            'aptitude', 'coding', 'written', 'online', 'offline'
        ]
    
    def classify_email(self, email_data):
        """Classify if email is placement-related.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            tuple: (is_placement_related, confidence_score)
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        text_content = text_content.lower()
        
        # Count placement keywords
        keyword_matches = sum(1 for keyword in self.placement_keywords if keyword in text_content)
        total_words = len(text_content.split())
        
        if total_words == 0:
            return False, 0.0
        
        # Calculate confidence based on keyword density
        confidence = min(keyword_matches / len(self.placement_keywords), 1.0)
        
        # Additional checks
        subject = email_data.get('subject', '').lower()
        if any(keyword in subject for keyword in ['placement', 'internship', 'job', 'recruitment']):
            confidence += 0.2
        
        is_placement = confidence > 0.1
        
        return is_placement, min(confidence, 1.0)
    
    def extract_company_name(self, email_data):
        """Extract company name from email.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            str: Company name or None
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        sender = email_data.get('sender', '')
        
        # Try to extract from sender email domain
        if '@' in sender:
            domain = sender.split('@')[1].split('.')[0]
            if domain.lower() not in ['gmail', 'yahoo', 'outlook', 'hotmail']:
                return domain.title()
        
        # Look for company patterns in text
        # Pattern: "Company Name Ltd" or "ABC Corporation"
        company_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:Ltd|Limited|Inc|Corporation|Corp|Pvt|Private|Technologies|Solutions|Systems|Services))',
            r'(?:company|organization|firm):\s*([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+\s+(?:Technologies|Solutions|Systems|Services|Corporation|Ltd))'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def extract_events(self, email_data):
        """Extract recruitment events from email.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            list: List of events
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        events = []
        
        # Look for event patterns
        event_patterns = [
            r'(?:round|stage)\s*(\d+):\s*([^.\n]+)',
            r'(technical|aptitude|coding|written|group discussion|interview)\s*(?:round|test|assessment)',
            r'(pre-placement talk|ppt|presentation)',
            r'(online test|written test|coding test)'
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    event = ' '.join(match).strip()
                else:
                    event = match.strip()
                if event and event not in events:
                    events.append(event)
        
        return events
    
    def extract_dates(self, email_data):
        """Extract dates from email and normalize to reception format.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            list: List of normalized dates
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        dates = []
        
        # Date patterns
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b',
            r'\b(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = parser.parse(match, fuzzy=True)
                    normalized_date = parsed_date.strftime('%Y-%m-%d')
                    if normalized_date not in dates:
                        dates.append(normalized_date)
                except:
                    continue
        
        return dates
    
    def extract_ctc(self, email_data):
        """Extract CTC/salary information from email.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            str: CTC information or None
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        
        # CTC patterns
        ctc_patterns = [
            r'ctc[:\s]*(?:rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)\s*(?:lakh|lakhs|lpa|per annum|yearly)',
            r'salary[:\s]*(?:rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)\s*(?:lakh|lakhs|lpa|per annum|yearly)',
            r'package[:\s]*(?:rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)\s*(?:lakh|lakhs|lpa|per annum|yearly)',
            r'compensation[:\s]*(?:rs\.?|inr)?\s*([\d,]+(?:\.\d{2})?)\s*(?:lakh|lakhs|lpa|per annum|yearly)'
        ]
        
        for pattern in ctc_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                return f"₹{matches[0]} LPA"
        
        return None
    
    def extract_bond_details(self, email_data):
        """Extract bond/service agreement details.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            str: Bond details or None
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        
        # Bond patterns
        bond_patterns = [
            r'bond[:\s]*(\d+)\s*(?:year|years|month|months)',
            r'service\s+agreement[:\s]*(\d+)\s*(?:year|years|month|months)',
            r'notice\s+period[:\s]*(\d+)\s*(?:month|months|days)',
            r'minimum\s+tenure[:\s]*(\d+)\s*(?:year|years|month|months)'
        ]
        
        for pattern in bond_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                return f"{matches[0]} years service bond"
        
        return None
    
    def extract_links(self, email_data):
        """Extract links from email.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            list: List of links
        """
        links = []
        
        # Extract from HTML body
        html_content = email_data.get('body_html', '')
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            for link in soup.find_all('a', href=True):
                url = link['href']
                if url.startswith('http'):
                    links.append({
                        'url': url,
                        'text': link.get_text().strip()
                    })
        
        # Extract from text body
        text_content = email_data.get('body_text', '')
        url_pattern = r'https?://[^\s]+'
        text_urls = re.findall(url_pattern, text_content)
        for url in text_urls:
            if not any(link['url'] == url for link in links):
                links.append({
                    'url': url,
                    'text': 'Link'
                })
        
        return links
    
    def generate_jd_summary(self, email_data):
        """Generate 1-2 line job description summary.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            str: JD summary
        """
        body_text = email_data.get('body_text', '')
        subject = email_data.get('subject', '')
        
        # Extract key information
        company = self.extract_company_name(email_data)
        ctc = self.extract_ctc(email_data)
        events = self.extract_events(email_data)
        
        # Create summary
        summary_parts = []
        
        if company:
            summary_parts.append(f"{company}")
        
        if 'internship' in subject.lower():
            summary_parts.append("internship opportunity")
        else:
            summary_parts.append("placement opportunity")
        
        if ctc:
            summary_parts.append(f"offering {ctc}")
        
        if events:
            summary_parts.append(f"with {len(events)} selection rounds")
        
        summary = ' '.join(summary_parts[:2])  # Keep it to 1-2 lines
        
        return summary if summary else f"Placement opportunity from {subject[:50]}..."
    
    def compute_sentiment_score(self, email_data):
        """Compute sentiment score of the email content.
        
        Args:
            email_data (dict): Email data
            
        Returns:
            tuple: (sentiment_score, tone_score)
        """
        text_content = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
        
        if not text_content.strip():
            return 0.0, 0.0
        
        # Use TextBlob for sentiment analysis
        blob = TextBlob(text_content)
        sentiment_score = blob.sentiment.polarity  # -1 to 1
        tone_score = blob.sentiment.subjectivity    # 0 to 1
        
        return sentiment_score, tone_score