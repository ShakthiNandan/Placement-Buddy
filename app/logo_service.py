import os
import requests
from urllib.parse import quote
import hashlib
import json

class CompanyLogoService:
    """Service for fetching and caching company logos."""
    
    def __init__(self):
        self.api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('CUSTOM_SEARCH_ENGINE_ID')
        self.cache_dir = 'static/logos'
        self.ensure_cache_dir()
    
    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_company_logo(self, company_name):
        """Get company logo URL with caching.
        
        Args:
            company_name (str): Company name
            
        Returns:
            str: Logo URL or None
        """
        if not company_name:
            return None
        
        # Check cache first
        cached_logo = self.get_cached_logo(company_name)
        if cached_logo:
            return cached_logo
        
        # Search for logo
        logo_url = self.search_company_logo(company_name)
        
        # Cache the result
        if logo_url:
            self.cache_logo_url(company_name, logo_url)
        
        return logo_url
    
    def get_cached_logo(self, company_name):
        """Get cached logo URL.
        
        Args:
            company_name (str): Company name
            
        Returns:
            str: Cached logo URL or None
        """
        cache_file = self.get_cache_filename(company_name)
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get('logo_url')
            except:
                pass
        
        return None
    
    def cache_logo_url(self, company_name, logo_url):
        """Cache logo URL.
        
        Args:
            company_name (str): Company name
            logo_url (str): Logo URL
        """
        cache_file = self.get_cache_filename(company_name)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'company_name': company_name,
                    'logo_url': logo_url
                }, f)
        except Exception as e:
            print(f"Error caching logo for {company_name}: {str(e)}")
    
    def get_cache_filename(self, company_name):
        """Get cache filename for company.
        
        Args:
            company_name (str): Company name
            
        Returns:
            str: Cache filename
        """
        # Create hash of company name for filename
        hash_name = hashlib.md5(company_name.lower().encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_name}.json")
    
    def search_company_logo(self, company_name):
        """Search for company logo using Custom Search API.
        
        Args:
            company_name (str): Company name
            
        Returns:
            str: Logo URL or None
        """
        if not self.api_key or not self.search_engine_id:
            # Fallback to default logo generation
            return self.generate_default_logo_url(company_name)
        
        try:
            # Search query
            query = f"{company_name} logo"
            
            # Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'searchType': 'image',
                'num': 5,
                'imgType': 'photo',
                'imgSize': 'medium'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if items:
                    # Return the first suitable image
                    for item in items:
                        logo_url = item.get('link')
                        if logo_url and self.is_valid_image_url(logo_url):
                            return logo_url
            
        except Exception as e:
            print(f"Error searching for logo of {company_name}: {str(e)}")
        
        # Fallback to default logo
        return self.generate_default_logo_url(company_name)
    
    def is_valid_image_url(self, url):
        """Check if URL points to a valid image.
        
        Args:
            url (str): Image URL
            
        Returns:
            bool: True if valid image URL
        """
        try:
            response = requests.head(url, timeout=5)
            content_type = response.headers.get('content-type', '')
            return content_type.startswith('image/')
        except:
            return False
    
    def generate_default_logo_url(self, company_name):
        """Generate default logo URL using a service like UI Avatars.
        
        Args:
            company_name (str): Company name
            
        Returns:
            str: Default logo URL
        """
        # Use UI Avatars as fallback
        initials = ''.join([word[0].upper() for word in company_name.split()[:2]])
        encoded_name = quote(initials)
        
        # Generate a color based on company name hash
        hash_color = hashlib.md5(company_name.encode()).hexdigest()[:6]
        
        return f"https://ui-avatars.com/api/?name={encoded_name}&size=128&background={hash_color}&color=ffffff&bold=true"
    
    def download_and_cache_logo(self, company_name, logo_url):
        """Download and locally cache logo image.
        
        Args:
            company_name (str): Company name
            logo_url (str): Logo URL
            
        Returns:
            str: Local file path or None
        """
        try:
            response = requests.get(logo_url, timeout=10)
            
            if response.status_code == 200:
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'gif' in content_type:
                    ext = '.gif'
                else:
                    ext = '.png'  # Default
                
                # Create filename
                hash_name = hashlib.md5(company_name.lower().encode()).hexdigest()
                filename = f"{hash_name}{ext}"
                filepath = os.path.join(self.cache_dir, filename)
                
                # Save file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return f"/static/logos/{filename}"
        
        except Exception as e:
            print(f"Error downloading logo for {company_name}: {str(e)}")
        
        return None