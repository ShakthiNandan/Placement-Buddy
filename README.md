# Placement Buddy - Flask Email Parser Dashboard

A Flask-based web application that fetches, parses, classifies, and analyzes placement-related emails from Gmail. The dashboard provides an interactive interface to view email analytics, search through emails, and export data.

## Features

### 🚀 Core Functionality
- **Gmail Integration**: Fetch up to 40 emails via Gmail API
- **Email Classification**: Automatically identify placement-related emails using ML techniques
- **Field Extraction**: Extract key information including:
  - Company names
  - Events and recruitment processes
  - Important dates (normalized format)
  - CTC/salary information
  - Bond details
  - Application links
- **Smart Analysis**:
  - Auto-generate 1-2 line job description summaries
  - Sentiment/tone scoring of email content
  - Company logo fetching and caching
- **Interactive Dashboard**: Filter, search, and browse emails
- **Data Export**: Export filtered data in JSON/CSV formats

### 📧 Email Processing
- Parse both text and HTML email content
- Handle email attachments
- Extract and normalize date information
- Classify emails with confidence scoring
- Generate meaningful summaries

### 🎨 Dashboard Features
- **Real-time Statistics**: Overview of email processing metrics
- **Advanced Filters**: Filter by company, date range, placement status
- **Search Functionality**: Full-text search across all email content
- **Responsive Design**: Works on desktop and mobile devices
- **Export Options**: Download data in multiple formats

## Quick Start

### Prerequisites
- Python 3.8+
- Gmail API credentials (optional for demo)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShakthiNandan/Placement-Buddy.git
   cd Placement-Buddy
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Generate sample data (for testing)**
   ```bash
   python generate_sample_data.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the dashboard**
   Open your browser and navigate to `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Gmail API Credentials (optional)
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here

# Custom Search API for company logos (optional)
CUSTOM_SEARCH_API_KEY=your_custom_search_api_key_here
CUSTOM_SEARCH_ENGINE_ID=your_custom_search_engine_id_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
DATABASE_URL=sqlite:///placement_buddy.db
```

### Gmail API Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and save as `credentials.json`
6. Update `.env` with your client ID and secret

**Note**: The application works with sample data even without Gmail API setup.

## Usage

### Dashboard Overview

The main dashboard provides several sections:

1. **Summary Cards**: Quick statistics about processed emails
2. **Filters Panel**: 
   - Search emails by content
   - Filter by company name
   - Filter by date range
   - Show only placement-related emails
3. **Email List**: Browse through processed emails with key information
4. **Statistics Panel**: Detailed analytics and top companies

### Key Actions

#### Fetch Emails
- Click "Fetch Emails" button to trigger Gmail API and process new emails
- Emails are automatically classified and analyzed
- Company logos are fetched and cached

#### Search and Filter
- Use the search box to find specific emails
- Apply filters to narrow down results
- Clear filters to reset view

#### View Email Details
- Click on any email card to view detailed information
- See extracted fields, sentiment analysis, and full content
- View attachments and links

#### Export Data
- Click "Export" button to download current filtered data
- Choose between JSON and CSV formats
- Exported data includes all processed fields

## Technical Architecture

### Backend Components

1. **Flask Application** (`app.py`): Main application setup and configuration
2. **Database Models** (`app/models.py`): SQLAlchemy models for emails and attachments
3. **Gmail Service** (`app/gmail_service.py`): Gmail API integration
4. **Email Parser** (`app/email_parser.py`): Email classification and field extraction
5. **Logo Service** (`app/logo_service.py`): Company logo fetching and caching
6. **Placement Service** (`app/placement_service.py`): Main orchestration service
7. **Routes** (`app/routes.py`): Flask API endpoints

### Frontend Components

1. **Dashboard Template** (`templates/dashboard.html`): Main UI layout
2. **CSS Styling** (`static/css/dashboard.css`): Custom styles and responsive design
3. **JavaScript** (`static/js/dashboard.js`): Interactive functionality and API calls

### Database Schema

#### PlacementEmail Table
- Basic email information (subject, sender, dates)
- Extracted fields (company, CTC, bond details)
- Analysis results (sentiment, classification confidence)
- Company information (logo URLs)

#### EmailAttachment Table
- Attachment metadata linked to emails

## API Endpoints

### Core Endpoints

- `POST /api/fetch-emails`: Trigger email fetching from Gmail
- `GET /api/dashboard-data`: Get dashboard data with optional filters
- `GET /api/search`: Search emails by content
- `GET /api/export`: Export filtered data
- `GET /api/email/<id>`: Get detailed email information
- `GET /api/statistics`: Get processing statistics

### Query Parameters

Most endpoints support filtering via query parameters:
- `company`: Filter by company name
- `date_from`: Start date filter (YYYY-MM-DD)
- `date_to`: End date filter (YYYY-MM-DD)
- `placement_only`: Show only placement emails (true/false)

## Sample Data

The application includes a sample data generator for testing:

```bash
python generate_sample_data.py
```

This creates 50 realistic sample emails with:
- Various companies (Google, Microsoft, TCS, etc.)
- Different email types (placements, internships)
- Extracted information (CTC, dates, bonds)
- Sentiment analysis scores
- Classification confidence

## Testing

### Manual Testing Checklist

#### Dashboard Loading
- [ ] Dashboard loads successfully
- [ ] Summary cards display correct statistics
- [ ] Email list loads with sample data
- [ ] Statistics panel shows analytics

#### Email Processing
- [ ] Fetch emails button triggers processing
- [ ] Progress is shown during processing
- [ ] New emails are classified correctly
- [ ] Extracted fields are accurate

#### Search and Filtering
- [ ] Search functionality works across all fields
- [ ] Company filter narrows results correctly
- [ ] Date range filter works properly
- [ ] Placement-only filter shows correct emails
- [ ] Clear filters resets all filters

#### Email Details
- [ ] Clicking email opens detail modal
- [ ] All extracted information is displayed
- [ ] Sentiment scores are shown
- [ ] Links and attachments are listed

#### Export Functionality
- [ ] Export modal opens correctly
- [ ] JSON export downloads successfully
- [ ] CSV export formats data correctly
- [ ] Filters are applied to export

#### Responsive Design
- [ ] Dashboard works on mobile devices
- [ ] Cards stack properly on small screens
- [ ] Modals display correctly on all screen sizes

### API Testing

Test API endpoints using curl or a tool like Postman:

```bash
# Get dashboard data
curl http://localhost:5000/api/dashboard-data

# Search emails
curl "http://localhost:5000/api/search?q=Google"

# Get statistics
curl http://localhost:5000/api/statistics

# Export data
curl "http://localhost:5000/api/export?format=json" -o emails.json
```

## Performance Considerations

### Email Processing
- Batch processing of emails for efficiency
- Caching of company logos to reduce API calls
- Database indexing on key fields

### Frontend Optimization
- Lazy loading of email details
- Efficient DOM updates
- Responsive image loading

### Caching Strategy
- Company logos cached locally
- Database query optimization
- Static asset caching

## Troubleshooting

### Common Issues

1. **Gmail API Errors**
   - Check credentials configuration
   - Verify API is enabled in Google Cloud Console
   - Ensure OAuth consent screen is configured

2. **Database Errors**
   - Check SQLite file permissions
   - Verify database schema is created
   - Clear database and regenerate if needed

3. **Logo Loading Issues**
   - Check Custom Search API configuration
   - Verify API quota is not exceeded
   - Fallback to default logos if API fails

4. **Frontend Issues**
   - Check browser console for JavaScript errors
   - Verify all static files are loading
   - Clear browser cache if needed

### Debugging

Enable debug mode in Flask:
```bash
export FLASK_ENV=development
python app.py
```

Check application logs for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

## Developer Notes

### Project Structure
```
Placement-Buddy/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── gmail_service.py
│   ├── email_parser.py
│   ├── logo_service.py
│   └── placement_service.py
├── static/
│   ├── css/dashboard.css
│   ├── js/dashboard.js
│   └── logos/ (generated)
├── templates/
│   └── dashboard.html
├── app.py
├── requirements.txt
├── generate_sample_data.py
├── .env.example
├── .gitignore
└── README.md
```

### Key Design Decisions

1. **Flask Framework**: Chosen for simplicity and rapid development
2. **SQLite Database**: Lightweight solution suitable for MVP
3. **Bootstrap UI**: Responsive design with minimal custom CSS
4. **jQuery/Vanilla JS**: Simple client-side interactions
5. **Gmail API**: Official Google integration for email access
6. **TextBlob**: Simple sentiment analysis library

This MVP provides a solid foundation that can be extended with additional features like advanced ML models, real-time updates, user authentication, and more sophisticated analytics.