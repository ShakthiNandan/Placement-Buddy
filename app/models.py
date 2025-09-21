from app import db
from datetime import datetime
import json

class PlacementEmail(db.Model):
    """Model for storing parsed placement emails."""
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(255), unique=True, nullable=False)
    subject = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(255), nullable=False)
    received_date = db.Column(db.DateTime, nullable=False)
    body_text = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    
    # Extracted fields
    company_name = db.Column(db.String(255), nullable=True)
    events = db.Column(db.Text, nullable=True)  # JSON string
    dates = db.Column(db.Text, nullable=True)   # JSON string
    ctc = db.Column(db.String(255), nullable=True)
    bond_details = db.Column(db.Text, nullable=True)
    links = db.Column(db.Text, nullable=True)   # JSON string
    
    # Analysis fields
    jd_summary = db.Column(db.Text, nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    tone_score = db.Column(db.Float, nullable=True)
    
    # Company info
    company_logo_url = db.Column(db.String(500), nullable=True)
    
    # Classification
    is_placement_related = db.Column(db.Boolean, default=False)
    classification_confidence = db.Column(db.Float, nullable=True)
    
    # Metadata
    processed_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlacementEmail {self.company_name}: {self.subject[:50]}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'subject': self.subject,
            'sender': self.sender,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'company_name': self.company_name,
            'events': json.loads(self.events) if self.events else [],
            'dates': json.loads(self.dates) if self.dates else [],
            'ctc': self.ctc,
            'bond_details': self.bond_details,
            'links': json.loads(self.links) if self.links else [],
            'jd_summary': self.jd_summary,
            'sentiment_score': self.sentiment_score,
            'tone_score': self.tone_score,
            'company_logo_url': self.company_logo_url,
            'is_placement_related': self.is_placement_related,
            'classification_confidence': self.classification_confidence,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None
        }

class EmailAttachment(db.Model):
    """Model for storing email attachments."""
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(255), db.ForeignKey('placement_email.email_id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=True)
    size = db.Column(db.Integer, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # Local storage path
    
    # Relationship
    email = db.relationship('PlacementEmail', backref=db.backref('attachments', lazy=True))
    
    def __repr__(self):
        return f'<EmailAttachment {self.filename}>'