import os
import base64
import json
import pickle
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import email
from email.mime.multipart import MIMEMultipart

class GmailService:
    """Service for interacting with Gmail API."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Check if token.json exists (stored credentials)
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # For development, we'll use a placeholder
                print("Gmail authentication required. Please set up OAuth2 credentials.")
                return None
        
        # Save credentials for next run
        if creds:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
        
        return self.service
    
    def fetch_emails(self, max_results=40, query=''):
        """Fetch emails from Gmail.
        
        Args:
            max_results (int): Maximum number of emails to fetch
            query (str): Gmail search query
            
        Returns:
            list: List of email data
        """
        if not self.service:
            print("Gmail service not authenticated")
            return []
        
        try:
            # Default query to look for placement-related emails
            if not query:
                placement_keywords = [
                    'placement', 'internship', 'job', 'recruitment', 'hiring', 
                    'career', 'opportunity', 'position', 'opening', 'apply'
                ]
                query = ' OR '.join(placement_keywords)
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self.get_message_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def get_message_details(self, message_id):
        """Get detailed information about a specific message.
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            dict: Email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract body
            body_text, body_html = self.extract_body(message['payload'])
            
            # Extract attachments
            attachments = self.extract_attachments(message_id, message['payload'])
            
            # Convert received date
            received_timestamp = int(message['internalDate']) / 1000
            received_date = datetime.fromtimestamp(received_timestamp)
            
            email_data = {
                'id': message_id,
                'subject': headers.get('Subject', ''),
                'sender': headers.get('From', ''),
                'to': headers.get('To', ''),
                'received_date': received_date,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments,
                'thread_id': message.get('threadId', ''),
                'snippet': message.get('snippet', '')
            }
            
            return email_data
            
        except Exception as e:
            print(f"Error getting message details for {message_id}: {str(e)}")
            return None
    
    def extract_body(self, payload):
        """Extract text and HTML body from email payload.
        
        Args:
            payload (dict): Email payload
            
        Returns:
            tuple: (text_body, html_body)
        """
        body_text = ""
        body_html = ""
        
        def decode_body(data):
            """Decode base64 encoded body data."""
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            return ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body_text = decode_body(part['body'].get('data', ''))
                elif part['mimeType'] == 'text/html':
                    body_html = decode_body(part['body'].get('data', ''))
                elif 'parts' in part:
                    # Nested parts
                    nested_text, nested_html = self.extract_body(part)
                    body_text += nested_text
                    body_html += nested_html
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                body_text = decode_body(payload['body'].get('data', ''))
            elif payload['mimeType'] == 'text/html':
                body_html = decode_body(payload['body'].get('data', ''))
        
        return body_text, body_html
    
    def extract_attachments(self, message_id, payload):
        """Extract attachment information from email payload.
        
        Args:
            message_id (str): Gmail message ID
            payload (dict): Email payload
            
        Returns:
            list: List of attachment info
        """
        attachments = []
        
        def process_part(part):
            if 'filename' in part and part['filename']:
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachment_id': attachment_id,
                        'message_id': message_id
                    })
            
            if 'parts' in part:
                for subpart in part['parts']:
                    process_part(subpart)
        
        if 'parts' in payload:
            for part in payload['parts']:
                process_part(part)
        
        return attachments
    
    def download_attachment(self, message_id, attachment_id, filename):
        """Download an attachment from Gmail.
        
        Args:
            message_id (str): Gmail message ID
            attachment_id (str): Attachment ID
            filename (str): Filename to save as
            
        Returns:
            bytes: Attachment data
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = base64.urlsafe_b64decode(attachment['data'])
            return data
            
        except Exception as e:
            print(f"Error downloading attachment {filename}: {str(e)}")
            return None