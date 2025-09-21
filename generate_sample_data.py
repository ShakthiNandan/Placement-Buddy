"""
Sample data generator for testing the Placement Email Parser Dashboard.
This creates realistic sample data to test the application without requiring Gmail API access.
"""

import json
import random
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from app.models import PlacementEmail, EmailAttachment

def generate_sample_data():
    """Generate sample placement emails for testing."""
    
    # Sample companies
    companies = [
        "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla",
        "Spotify", "Uber", "Airbnb", "Stripe", "Zoom", "Adobe", "Intel",
        "TCS", "Infosys", "Wipro", "HCL", "Cognizant", "Accenture"
    ]
    
    # Sample subjects
    subjects = [
        "Placement Opportunity - Software Engineer",
        "Internship Program 2024 - Apply Now",
        "Technical Assessment Invitation",
        "Final Round Interview Scheduled",
        "Pre-Placement Talk - {} Campus Drive",
        "Job Opening: Full Stack Developer",
        "Summer Internship - Data Science",
        "Graduate Program - {} Technologies",
        "Recruitment Drive - Multiple Positions",
        "Assessment Test - Software Engineering"
    ]
    
    # Sample email bodies
    body_templates = [
        """Dear Students,

We are excited to announce a placement opportunity for Software Engineer positions at {company}.

Position Details:
- Role: Software Engineer
- CTC: {ctc} LPA
- Location: {location}
- Bond: {bond} years

Selection Process:
1. Online Test - {date1}
2. Technical Interview - {date2}
3. HR Interview - {date3}

Please find the application link: https://careers.{domain}.com/apply

Best regards,
Placement Team
{company}""",

        """Hello,

This is to inform you about the upcoming campus recruitment drive by {company}.

Package: {ctc} LPA
Service Bond: {bond} years
Last date to apply: {date1}

Recruitment Process:
- Aptitude Test
- Group Discussion
- Technical Round
- HR Round

For more information, visit: https://{domain}.com/careers

Regards,
HR Team""",

        """Subject: Internship Opportunity

Dear Candidates,

{company} is offering summer internship positions for 2024.

Stipend: ₹{stipend} per month
Duration: 6 months
Start Date: {date1}

Assessment rounds:
1. Online coding test
2. Technical interview
3. Final interview

Apply here: https://internships.{domain}.com

Best,
Talent Acquisition Team"""
    ]
    
    # Generate sample emails
    sample_emails = []
    
    for i in range(50):  # Generate 50 sample emails
        company = random.choice(companies)
        subject = random.choice(subjects).format(company)
        
        # Generate random dates
        base_date = datetime.now() - timedelta(days=random.randint(1, 30))
        date1 = (base_date + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')
        date2 = (base_date + timedelta(days=random.randint(8, 14))).strftime('%Y-%m-%d')
        date3 = (base_date + timedelta(days=random.randint(15, 21))).strftime('%Y-%m-%d')
        
        # Generate random CTC
        ctc_values = ["3.5", "4.2", "5.5", "6.8", "8.0", "10.5", "12.0", "15.0", "18.0", "25.0"]
        ctc = random.choice(ctc_values)
        
        # Generate random bond
        bond_years = random.choice(["1", "2", "3", "No"])
        
        # Generate random locations
        locations = ["Bangalore", "Hyderabad", "Chennai", "Pune", "Mumbai", "Delhi", "Noida"]
        location = random.choice(locations)
        
        # Generate stipend for internships
        stipends = ["15000", "20000", "25000", "30000", "35000", "40000"]
        stipend = random.choice(stipends)
        
        # Create domain from company name
        domain = company.lower().replace(" ", "")
        
        # Select and format body template
        body_template = random.choice(body_templates)
        body = body_template.format(
            company=company,
            ctc=ctc,
            location=location,
            bond=bond_years,
            date1=date1,
            date2=date2,
            date3=date3,
            domain=domain,
            stipend=stipend
        )
        
        # Generate sender email
        sender_domains = ["hr.com", "careers.com", "recruiting.com", "talent.com"]
        sender = f"recruitment@{company.lower().replace(' ', '')}.{random.choice(sender_domains)}"
        
        # Create placement classification (most are placement-related)
        is_placement = random.choice([True, True, True, True, False])  # 80% placement emails
        
        # Generate sentiment scores
        sentiment_score = random.uniform(-0.5, 0.8)  # Generally positive for placement emails
        tone_score = random.uniform(0.2, 0.9)
        
        # Generate confidence score
        confidence = random.uniform(0.6, 0.95) if is_placement else random.uniform(0.1, 0.4)
        
        # Create sample email data
        email_data = {
            'email_id': f'sample_{i+1}_{random.randint(1000, 9999)}',
            'subject': subject,
            'sender': sender,
            'received_date': base_date,
            'body_text': body,
            'body_html': f'<html><body><pre>{body}</pre></body></html>',
            'company_name': company,
            'events': json.dumps(['Online Test', 'Technical Interview', 'HR Interview']) if is_placement else None,
            'dates': json.dumps([date1, date2, date3]) if is_placement else None,
            'ctc': f'₹{ctc} LPA' if is_placement and 'internship' not in subject.lower() else None,
            'bond_details': f'{bond_years} years service bond' if is_placement and bond_years != 'No' else None,
            'links': json.dumps([
                {'url': f'https://careers.{domain}.com/apply', 'text': 'Apply Here'},
                {'url': f'https://{domain}.com/about', 'text': 'About Company'}
            ]) if is_placement else None,
            'jd_summary': f'{company} offering {"internship" if "internship" in subject.lower() else "placement"} opportunity with {"₹" + ctc + " LPA" if is_placement else "good"} package',
            'sentiment_score': sentiment_score,
            'tone_score': tone_score,
            'company_logo_url': f'https://ui-avatars.com/api/?name={company[0:2]}&size=128&background=random&color=ffffff&bold=true',
            'is_placement_related': is_placement,
            'classification_confidence': confidence
        }
        
        sample_emails.append(email_data)
    
    return sample_emails

def populate_database():
    """Populate database with sample data."""
    
    with app.app_context():
        # Clear existing data
        EmailAttachment.query.delete()
        PlacementEmail.query.delete()
        db.session.commit()
        
        # Generate and insert sample data
        sample_emails = generate_sample_data()
        
        for email_data in sample_emails:
            placement_email = PlacementEmail(**email_data)
            db.session.add(placement_email)
        
        try:
            db.session.commit()
            print(f"Successfully inserted {len(sample_emails)} sample emails")
            
            # Print some statistics
            total = PlacementEmail.query.count()
            placement_count = PlacementEmail.query.filter_by(is_placement_related=True).count()
            companies = db.session.query(PlacementEmail.company_name).distinct().count()
            
            print(f"Total emails: {total}")
            print(f"Placement emails: {placement_count}")
            print(f"Other emails: {total - placement_count}")
            print(f"Unique companies: {companies}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting sample data: {str(e)}")

if __name__ == "__main__":
    populate_database()