// Dashboard JavaScript
class PlacementDashboard {
    constructor() {
        this.currentFilters = {};
        this.currentEmails = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadDashboardData();
        this.loadStatistics();
    }

    bindEvents() {
        // Fetch emails button
        document.getElementById('fetchEmailsBtn').addEventListener('click', () => {
            this.fetchEmails();
        });

        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Filter buttons
        document.getElementById('applyFiltersBtn').addEventListener('click', () => {
            this.applyFilters();
        });

        document.getElementById('clearFiltersBtn').addEventListener('click', () => {
            this.clearFilters();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadDashboardData();
        });

        // Export functionality
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.showExportModal();
        });

        document.getElementById('confirmExportBtn').addEventListener('click', () => {
            this.exportData();
        });
    }

    async fetchEmails() {
        this.showLoadingModal('Fetching emails from Gmail...');

        try {
            const response = await fetch('/api/fetch-emails', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ max_emails: 40 })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Success', `Processed ${result.data.total_fetched} emails`, 'success');
                this.loadDashboardData();
                this.loadStatistics();
            } else {
                this.showToast('Error', result.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Failed to fetch emails', 'error');
            console.error('Fetch emails error:', error);
        }

        this.hideLoadingModal();
    }

    async loadDashboardData() {
        try {
            const queryParams = new URLSearchParams(this.currentFilters);
            const response = await fetch(`/api/dashboard-data?${queryParams}`);
            const result = await response.json();

            if (result.success) {
                this.currentEmails = result.data.emails;
                this.renderEmails(result.data.emails);
                this.updateSummaryCards(result.data.statistics);
            } else {
                this.showToast('Error', result.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Failed to load dashboard data', 'error');
            console.error('Load dashboard data error:', error);
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/statistics');
            const result = await response.json();

            if (result.success) {
                this.renderStatistics(result.data);
            }
        } catch (error) {
            console.error('Load statistics error:', error);
        }
    }

    renderEmails(emails) {
        const container = document.getElementById('emailsContainer');
        
        if (emails.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>No emails found</p>
                </div>
            `;
            return;
        }

        const emailsHtml = emails.map(email => this.createEmailCard(email)).join('');
        container.innerHTML = emailsHtml;

        // Bind click events for email details
        container.querySelectorAll('.email-item').forEach(item => {
            item.addEventListener('click', () => {
                const emailId = item.dataset.emailId;
                this.showEmailDetails(emailId);
            });
        });
    }

    createEmailCard(email) {
        const placementClass = email.is_placement_related ? 'placement-email' : 'non-placement-email';
        const sentimentClass = this.getSentimentClass(email.sentiment_score);
        const confidenceClass = this.getConfidenceClass(email.classification_confidence);
        
        const companyLogo = email.company_logo_url || '/static/images/default-company-logo.png';
        const receivedDate = new Date(email.received_date).toLocaleDateString();

        return `
            <div class="email-item ${placementClass} fade-in" data-email-id="${email.id}">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <img src="${companyLogo}" alt="Company Logo" class="company-logo">
                    </div>
                    <div class="col">
                        <h6 class="mb-1">${this.escapeHtml(email.subject)}</h6>
                        <div class="email-meta">
                            <span><i class="fas fa-envelope me-1"></i>${this.escapeHtml(email.sender)}</span>
                            <span class="ms-3"><i class="fas fa-calendar me-1"></i>${receivedDate}</span>
                            ${email.company_name ? `<span class="ms-3"><i class="fas fa-building me-1"></i>${this.escapeHtml(email.company_name)}</span>` : ''}
                        </div>
                        ${email.jd_summary ? `<div class="email-summary text-muted">${this.escapeHtml(email.jd_summary)}</div>` : ''}
                    </div>
                    <div class="col-auto">
                        <div class="text-end">
                            <span class="badge ${email.is_placement_related ? 'bg-success' : 'bg-secondary'} badge-custom">
                                ${email.is_placement_related ? 'Placement' : 'Other'}
                            </span>
                            ${email.ctc ? `<div class="mt-1"><small class="text-success fw-bold">${this.escapeHtml(email.ctc)}</small></div>` : ''}
                            ${email.sentiment_score !== null ? `<div class="mt-1"><small class="${sentimentClass}"><i class="fas fa-smile me-1"></i>${email.sentiment_score.toFixed(2)}</small></div>` : ''}
                            <div class="mt-1"><small class="${confidenceClass}">Confidence: ${(email.classification_confidence * 100).toFixed(0)}%</small></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async showEmailDetails(emailId) {
        try {
            const response = await fetch(`/api/email/${emailId}`);
            const result = await response.json();

            if (result.success) {
                this.renderEmailDetails(result.data);
                const modal = new bootstrap.Modal(document.getElementById('emailDetailModal'));
                modal.show();
            } else {
                this.showToast('Error', result.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Failed to load email details', 'error');
            console.error('Show email details error:', error);
        }
    }

    renderEmailDetails(email) {
        const content = document.getElementById('emailDetailContent');
        const receivedDate = new Date(email.received_date).toLocaleString();
        const processedDate = new Date(email.processed_date).toLocaleString();

        content.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Basic Information</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Subject:</strong></td><td>${this.escapeHtml(email.subject)}</td></tr>
                        <tr><td><strong>Sender:</strong></td><td>${this.escapeHtml(email.sender)}</td></tr>
                        <tr><td><strong>Received:</strong></td><td>${receivedDate}</td></tr>
                        <tr><td><strong>Processed:</strong></td><td>${processedDate}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Extracted Information</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Company:</strong></td><td>${email.company_name || 'N/A'}</td></tr>
                        <tr><td><strong>CTC:</strong></td><td>${email.ctc || 'N/A'}</td></tr>
                        <tr><td><strong>Bond:</strong></td><td>${email.bond_details || 'N/A'}</td></tr>
                        <tr><td><strong>Classification:</strong></td><td>
                            <span class="badge ${email.is_placement_related ? 'bg-success' : 'bg-secondary'}">
                                ${email.is_placement_related ? 'Placement' : 'Other'}
                            </span>
                            (${(email.classification_confidence * 100).toFixed(0)}%)
                        </td></tr>
                    </table>
                </div>
            </div>

            ${email.jd_summary ? `
                <div class="mt-3">
                    <h6>Job Description Summary</h6>
                    <p class="text-muted">${this.escapeHtml(email.jd_summary)}</p>
                </div>
            ` : ''}

            ${email.events && email.events.length > 0 ? `
                <div class="mt-3">
                    <h6>Events</h6>
                    <div class="d-flex flex-wrap gap-2">
                        ${email.events.map(event => `<span class="badge bg-primary">${this.escapeHtml(event)}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${email.dates && email.dates.length > 0 ? `
                <div class="mt-3">
                    <h6>Important Dates</h6>
                    <div class="d-flex flex-wrap gap-2">
                        ${email.dates.map(date => `<span class="badge bg-info">${date}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${email.links && email.links.length > 0 ? `
                <div class="mt-3">
                    <h6>Links</h6>
                    <ul class="list-unstyled">
                        ${email.links.map(link => `<li><a href="${link.url}" target="_blank" class="text-decoration-none">${this.escapeHtml(link.text || link.url)}</a></li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${email.sentiment_score !== null ? `
                <div class="mt-3">
                    <h6>Sentiment Analysis</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <span class="text-muted">Sentiment Score:</span>
                            <span class="${this.getSentimentClass(email.sentiment_score)} fw-bold">${email.sentiment_score.toFixed(2)}</span>
                        </div>
                        <div class="col-md-6">
                            <span class="text-muted">Tone Score:</span>
                            <span class="fw-bold">${email.tone_score.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            ` : ''}

            <div class="mt-3">
                <h6>Email Content</h6>
                <div class="email-content">
                    ${email.body_text || 'No content available'}
                </div>
            </div>
        `;
    }

    updateSummaryCards(statistics) {
        document.getElementById('totalEmailsCount').textContent = statistics.total_emails;
        document.getElementById('placementEmailsCount').textContent = statistics.placement_emails;
        document.getElementById('companiesCount').textContent = statistics.unique_companies;
        document.getElementById('avgSentimentScore').textContent = statistics.average_sentiment;
    }

    renderStatistics(statistics) {
        const container = document.getElementById('statisticsCard');
        
        container.innerHTML = `
            <div class="mb-3">
                <h6 class="card-title">Recent Activity</h6>
                <p class="mb-1">Last 7 days: <strong>${statistics.recent_activity}</strong> emails</p>
                <p class="mb-0">Total emails: <strong>${statistics.total_emails}</strong></p>
            </div>
            
            ${statistics.top_companies.length > 0 ? `
                <div class="mb-3">
                    <h6 class="card-title">Top Companies</h6>
                    ${statistics.top_companies.slice(0, 5).map(company => `
                        <div class="d-flex justify-content-between mb-1">
                            <small>${this.escapeHtml(company.name)}</small>
                            <small><strong>${company.count}</strong></small>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div>
                <h6 class="card-title">Sentiment Overview</h6>
                <p class="mb-1">Average: <strong>${statistics.average_sentiment}</strong></p>
                <p class="mb-0"><small class="text-muted">${statistics.emails_with_sentiment} emails analyzed</small></p>
            </div>
        `;
    }

    async performSearch() {
        const searchTerm = document.getElementById('searchInput').value.trim();
        
        if (!searchTerm) {
            this.showToast('Warning', 'Please enter a search term', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(searchTerm)}`);
            const result = await response.json();

            if (result.success) {
                this.renderEmails(result.data);
                this.showToast('Success', `Found ${result.data.length} matching emails`, 'success');
            } else {
                this.showToast('Error', result.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Search failed', 'error');
            console.error('Search error:', error);
        }
    }

    applyFilters() {
        this.currentFilters = {};

        const company = document.getElementById('companyFilter').value.trim();
        if (company) this.currentFilters.company = company;

        const dateFrom = document.getElementById('dateFromFilter').value;
        if (dateFrom) this.currentFilters.date_from = dateFrom;

        const dateTo = document.getElementById('dateToFilter').value;
        if (dateTo) this.currentFilters.date_to = dateTo;

        const placementOnly = document.getElementById('placementOnlyFilter').checked;
        if (placementOnly) this.currentFilters.placement_only = 'true';

        this.loadDashboardData();
    }

    clearFilters() {
        document.getElementById('companyFilter').value = '';
        document.getElementById('dateFromFilter').value = '';
        document.getElementById('dateToFilter').value = '';
        document.getElementById('placementOnlyFilter').checked = false;
        document.getElementById('searchInput').value = '';

        this.currentFilters = {};
        this.loadDashboardData();
    }

    showExportModal() {
        const modal = new bootstrap.Modal(document.getElementById('exportModal'));
        modal.show();
    }

    async exportData() {
        const format = document.getElementById('exportFormat').value;
        
        try {
            const queryParams = new URLSearchParams({
                ...this.currentFilters,
                format: format
            });
            
            const response = await fetch(`/api/export?${queryParams}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                
                const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                a.download = `placement_emails_${timestamp}.${format}`;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast('Success', 'Data exported successfully', 'success');
                
                // Hide modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
                modal.hide();
            } else {
                this.showToast('Error', 'Export failed', 'error');
            }
        } catch (error) {
            this.showToast('Error', 'Export failed', 'error');
            console.error('Export error:', error);
        }
    }

    showLoadingModal(message) {
        document.getElementById('loadingMessage').textContent = message;
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }

    hideLoadingModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }

    showToast(title, message, type = 'info') {
        const toastHtml = `
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <strong class="me-auto text-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'}">${title}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;

        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        container.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = container.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    getSentimentClass(score) {
        if (score === null || score === undefined) return 'sentiment-neutral';
        if (score > 0.1) return 'sentiment-positive';
        if (score < -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.7) return 'confidence-high';
        if (confidence >= 0.4) return 'confidence-medium';
        return 'confidence-low';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PlacementDashboard();
});