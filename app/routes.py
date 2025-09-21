from flask import render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from app import app, db
from app.placement_service import PlacementEmailService
from app.models import PlacementEmail
from datetime import datetime, timedelta
import json
import os

# Initialize service
placement_service = PlacementEmailService()

@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('dashboard.html')

@app.route('/api/fetch-emails', methods=['POST'])
def fetch_emails():
    """API endpoint to fetch emails via UI button trigger."""
    try:
        max_emails = request.json.get('max_emails', 40) if request.is_json else 40
        
        # Trigger email fetching and processing
        results = placement_service.fetch_and_process_emails(max_emails=max_emails)
        
        return jsonify({
            'success': True,
            'message': f"Processed {results['total_fetched']} emails",
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching emails: {str(e)}"
        }), 500

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Get dashboard data with optional filters."""
    try:
        # Parse filters from query parameters
        filters = {}
        
        if request.args.get('company'):
            filters['company'] = request.args.get('company')
        
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        
        if request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        
        if request.args.get('placement_only') == 'true':
            filters['placement_only'] = True
        
        data = placement_service.get_dashboard_data(filters)
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting dashboard data: {str(e)}"
        }), 500

@app.route('/api/search')
def search_emails():
    """Search emails API endpoint."""
    try:
        search_term = request.args.get('q', '')
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': "Search term is required"
            }), 400
        
        results = placement_service.search_emails(search_term)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error searching emails: {str(e)}"
        }), 500

@app.route('/api/export')
def export_data():
    """Export data API endpoint."""
    try:
        format_type = request.args.get('format', 'json')
        
        # Parse filters
        filters = {}
        if request.args.get('company'):
            filters['company'] = request.args.get('company')
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        if request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        if request.args.get('placement_only') == 'true':
            filters['placement_only'] = True
        
        exported_data = placement_service.export_data(format_type, filters)
        
        if not exported_data:
            return jsonify({
                'success': False,
                'message': "Unsupported export format"
            }), 400
        
        # Set appropriate content type
        if format_type == 'json':
            content_type = 'application/json'
            filename = f"placement_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif format_type == 'csv':
            content_type = 'text/csv'
            filename = f"placement_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = app.response_class(
            exported_data,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error exporting data: {str(e)}"
        }), 500

@app.route('/api/email/<int:email_id>')
def get_email_details(email_id):
    """Get detailed information about a specific email."""
    try:
        email = PlacementEmail.query.get_or_404(email_id)
        
        return jsonify({
            'success': True,
            'data': email.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting email details: {str(e)}"
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """Get email processing statistics."""
    try:
        # Get overall statistics
        total_emails = PlacementEmail.query.count()
        placement_emails = PlacementEmail.query.filter_by(is_placement_related=True).count()
        
        # Get recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_emails = PlacementEmail.query.filter(
            PlacementEmail.processed_date >= week_ago
        ).count()
        
        # Get top companies
        company_stats = db.session.query(
            PlacementEmail.company_name,
            db.func.count(PlacementEmail.id).label('count')
        ).filter(
            PlacementEmail.company_name.is_not(None),
            PlacementEmail.is_placement_related == True
        ).group_by(
            PlacementEmail.company_name
        ).order_by(
            db.desc('count')
        ).limit(10).all()
        
        # Get sentiment distribution
        sentiment_stats = db.session.query(
            db.func.avg(PlacementEmail.sentiment_score).label('avg_sentiment'),
            db.func.count(PlacementEmail.id).label('count')
        ).filter(
            PlacementEmail.sentiment_score.is_not(None)
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'total_emails': total_emails,
                'placement_emails': placement_emails,
                'non_placement_emails': total_emails - placement_emails,
                'recent_activity': recent_emails,
                'top_companies': [{'name': name, 'count': count} for name, count in company_stats],
                'average_sentiment': round(sentiment_stats.avg_sentiment or 0, 2),
                'emails_with_sentiment': sentiment_stats.count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting statistics: {str(e)}"
        }), 500

@app.route('/api/reprocess-email/<int:email_id>', methods=['POST'])
def reprocess_email(email_id):
    """Reprocess a specific email."""
    try:
        email = PlacementEmail.query.get_or_404(email_id)
        
        # Create email data for reprocessing
        email_data = {
            'id': email.email_id,
            'subject': email.subject,
            'sender': email.sender,
            'received_date': email.received_date,
            'body_text': email.body_text,
            'body_html': email.body_html
        }
        
        # Delete existing record
        db.session.delete(email)
        db.session.commit()
        
        # Reprocess
        processed_email = placement_service.process_single_email(email_data)
        
        if processed_email:
            return jsonify({
                'success': True,
                'message': "Email reprocessed successfully",
                'data': processed_email.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': "Failed to reprocess email"
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error reprocessing email: {str(e)}"
        }), 500

@app.route('/static/logos/<filename>')
def serve_logo(filename):
    """Serve cached logo files."""
    try:
        return send_from_directory('static/logos', filename)
    except:
        # Return default logo if file not found
        return redirect('/static/images/default-company-logo.png')

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500