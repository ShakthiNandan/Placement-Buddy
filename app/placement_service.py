import json
from datetime import datetime
from app import db
from app.models import PlacementEmail, EmailAttachment
from app.gmail_service import GmailService
from app.email_parser import EmailParser
from app.logo_service import CompanyLogoService

class PlacementEmailService:
    """Main service for processing placement emails."""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.email_parser = EmailParser()
        self.logo_service = CompanyLogoService()
    
    def fetch_and_process_emails(self, max_emails=40):
        """Fetch and process emails from Gmail.
        
        Args:
            max_emails (int): Maximum number of emails to process
            
        Returns:
            dict: Processing results
        """
        results = {
            'total_fetched': 0,
            'placement_emails': 0,
            'non_placement_emails': 0,
            'errors': []
        }
        
        try:
            # Fetch emails from Gmail
            emails = self.gmail_service.fetch_emails(max_results=max_emails)
            results['total_fetched'] = len(emails)
            
            for email_data in emails:
                try:
                    processed = self.process_single_email(email_data)
                    if processed and processed.is_placement_related:
                        results['placement_emails'] += 1
                    else:
                        results['non_placement_emails'] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing email {email_data.get('id', 'unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
                    print(error_msg)
            
        except Exception as e:
            error_msg = f"Error fetching emails: {str(e)}"
            results['errors'].append(error_msg)
            print(error_msg)
        
        return results
    
    def process_single_email(self, email_data):
        """Process a single email.
        
        Args:
            email_data (dict): Email data from Gmail
            
        Returns:
            PlacementEmail: Processed email model or None
        """
        email_id = email_data.get('id')
        
        # Check if email already exists
        existing = PlacementEmail.query.filter_by(email_id=email_id).first()
        if existing:
            print(f"Email {email_id} already processed")
            return existing
        
        # Classify email
        is_placement, confidence = self.email_parser.classify_email(email_data)
        
        # Extract fields
        company_name = self.email_parser.extract_company_name(email_data)
        events = self.email_parser.extract_events(email_data)
        dates = self.email_parser.extract_dates(email_data)
        ctc = self.email_parser.extract_ctc(email_data)
        bond_details = self.email_parser.extract_bond_details(email_data)
        links = self.email_parser.extract_links(email_data)
        
        # Generate summary and scores
        jd_summary = self.email_parser.generate_jd_summary(email_data)
        sentiment_score, tone_score = self.email_parser.compute_sentiment_score(email_data)
        
        # Get company logo
        company_logo_url = None
        if company_name:
            company_logo_url = self.logo_service.get_company_logo(company_name)
        
        # Create email record
        placement_email = PlacementEmail(
            email_id=email_id,
            subject=email_data.get('subject', '')[:500],  # Limit length
            sender=email_data.get('sender', '')[:255],
            received_date=email_data.get('received_date'),
            body_text=email_data.get('body_text', ''),
            body_html=email_data.get('body_html', ''),
            company_name=company_name,
            events=json.dumps(events) if events else None,
            dates=json.dumps(dates) if dates else None,
            ctc=ctc,
            bond_details=bond_details,
            links=json.dumps(links) if links else None,
            jd_summary=jd_summary,
            sentiment_score=sentiment_score,
            tone_score=tone_score,
            company_logo_url=company_logo_url,
            is_placement_related=is_placement,
            classification_confidence=confidence
        )
        
        # Save to database
        try:
            db.session.add(placement_email)
            db.session.commit()
            
            # Process attachments
            self.process_email_attachments(email_data, email_id)
            
            print(f"Processed email: {email_data.get('subject', '')[:50]}...")
            return placement_email
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving email {email_id}: {str(e)}")
            return None
    
    def process_email_attachments(self, email_data, email_id):
        """Process email attachments.
        
        Args:
            email_data (dict): Email data
            email_id (str): Email ID
        """
        attachments = email_data.get('attachments', [])
        
        for attachment_info in attachments:
            try:
                attachment = EmailAttachment(
                    email_id=email_id,
                    filename=attachment_info.get('filename', ''),
                    content_type=attachment_info.get('mime_type', ''),
                    size=attachment_info.get('size', 0)
                )
                
                db.session.add(attachment)
                
            except Exception as e:
                print(f"Error processing attachment {attachment_info.get('filename', '')}: {str(e)}")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving attachments for email {email_id}: {str(e)}")
    
    def get_dashboard_data(self, filters=None):
        """Get data for dashboard display.
        
        Args:
            filters (dict): Optional filters
            
        Returns:
            dict: Dashboard data
        """
        query = PlacementEmail.query
        
        # Apply filters
        if filters:
            if filters.get('company'):
                query = query.filter(PlacementEmail.company_name.ilike(f"%{filters['company']}%"))
            
            if filters.get('date_from'):
                query = query.filter(PlacementEmail.received_date >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(PlacementEmail.received_date <= filters['date_to'])
            
            if filters.get('placement_only'):
                query = query.filter(PlacementEmail.is_placement_related == True)
        
        emails = query.order_by(PlacementEmail.received_date.desc()).all()
        
        # Aggregate statistics
        total_emails = len(emails)
        placement_emails = sum(1 for email in emails if email.is_placement_related)
        unique_companies = len(set(email.company_name for email in emails if email.company_name))
        
        # Average sentiment
        sentiments = [email.sentiment_score for email in emails if email.sentiment_score is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            'emails': [email.to_dict() for email in emails],
            'statistics': {
                'total_emails': total_emails,
                'placement_emails': placement_emails,
                'non_placement_emails': total_emails - placement_emails,
                'unique_companies': unique_companies,
                'average_sentiment': round(avg_sentiment, 2)
            }
        }
    
    def search_emails(self, search_term):
        """Search emails by content.
        
        Args:
            search_term (str): Search term
            
        Returns:
            list: Matching emails
        """
        query = PlacementEmail.query.filter(
            db.or_(
                PlacementEmail.subject.ilike(f"%{search_term}%"),
                PlacementEmail.company_name.ilike(f"%{search_term}%"),
                PlacementEmail.body_text.ilike(f"%{search_term}%"),
                PlacementEmail.jd_summary.ilike(f"%{search_term}%")
            )
        ).order_by(PlacementEmail.received_date.desc())
        
        return [email.to_dict() for email in query.all()]
    
    def export_data(self, format='json', filters=None):
        """Export email data.
        
        Args:
            format (str): Export format ('json' or 'csv')
            filters (dict): Optional filters
            
        Returns:
            str: Exported data
        """
        dashboard_data = self.get_dashboard_data(filters)
        emails = dashboard_data['emails']
        
        if format == 'json':
            return json.dumps(emails, indent=2)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            if emails:
                writer.writerow(emails[0].keys())
                
                # Data rows
                for email in emails:
                    writer.writerow(email.values())
            
            return output.getvalue()
        
        return None