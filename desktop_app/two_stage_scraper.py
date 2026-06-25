"""
TWO-STAGE SCHOOL DATA SCRAPER
Stage 1: Find Google Maps link for each school
Stage 2: Extract address, phone, email, website from Google Maps
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from datetime import datetime
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
]

class TwoStageScraper:
    def __init__(self):
        self.session = requests.Session()
        self.found_count = 0
        self.failed_count = 0
    
    def get_page(self, url, timeout=10):
        """Get page with error handling"""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            response = self.session.get(url, timeout=timeout, headers=headers)
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
        return None
    
    def find_gmaps_link(self, school_name, taluka_name=''):
        """
        STAGE 1: Find Google Maps link for school
        """
        logger.debug(f"Finding gmaps link: {school_name}")
        
        try:
            # Build search query
            query = f'"{school_name}"'
            if taluka_name:
                query += f' {taluka_name}'
            query += ' Pune school'
            
            # Search using Google Maps
            search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
            
            response = self.get_page(search_url)
            if not response:
                # Fallback: search via DuckDuckGo for maps links
                return self.find_gmaps_link_duckduckgo(school_name, taluka_name)
            
            # Extract Google Maps link from response
            pattern = r'https://maps\.google\.com[^\s<>]*|https://maps\.app\.goo\.gl/[^\s<>]*'
            match = re.search(pattern, response.text)
            
            if match:
                gmaps_link = match.group(0)
                logger.debug(f"Found gmaps link: {gmaps_link}")
                return gmaps_link
            
            # Fallback to DuckDuckGo
            return self.find_gmaps_link_duckduckgo(school_name, taluka_name)
            
        except Exception as e:
            logger.debug(f"Error finding gmaps link: {str(e)}")
            return None
    
    def find_gmaps_link_duckduckgo(self, school_name, taluka_name=''):
        """Fallback: Find gmaps link via DuckDuckGo"""
        try:
            query = f'"{school_name}" site:google.com/maps'
            if taluka_name:
                query += f' {taluka_name}'
            
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = self.get_page(search_url)
            
            if not response:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='result__a', limit=5)
            
            for link in links:
                href = link.get('href', '')
                if 'maps.app.goo.gl' in href or 'google.com/maps' in href:
                    logger.debug(f"Found via DDG: {href}")
                    return href
            
        except Exception as e:
            logger.debug(f"DuckDuckGo gmaps search error: {str(e)}")
        
        return None
    
    def extract_from_gmaps(self, gmaps_link):
        """
        STAGE 2: Extract data from Google Maps link
        """
        logger.debug(f"Extracting from gmaps: {gmaps_link}")
        
        result = {
            'address': '',
            'phone': '',
            'email': '',
            'website': '',
            'pincode': ''
        }
        
        if not gmaps_link:
            return result
        
        try:
            # Normalize the link
            if 'maps.app.goo.gl' in gmaps_link:
                # Shortened link - need to resolve
                response = self.get_page(gmaps_link, timeout=15)
            else:
                response = self.get_page(gmaps_link, timeout=15)
            
            if not response:
                logger.debug("Could not fetch gmaps page")
                return result
            
            text = response.text
            
            # Extract phone (10-digit Indian format)
            phone_match = re.search(r'\b[6-9]\d{9}\b', text)
            if phone_match:
                result['phone'] = phone_match.group(0)
            
            # Extract email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                email = email_match.group(0)
                if 'noreply' not in email.lower():
                    result['email'] = email
            
            # Extract website
            website_match = re.search(r'https?://(?:www\.)?[\w\-\.]+\.\w+', text)
            if website_match and 'google' not in website_match.group(0):
                result['website'] = website_match.group(0)
            
            # Extract pincode (6 digits)
            pincode_match = re.search(r'\b\d{6}\b', text)
            if pincode_match:
                result['pincode'] = pincode_match.group(0)
            
            # Try to extract address
            # Look for address patterns
            address_pattern = r'(?:Address|Location|Office|Registered)[:\s]+([^,<>]{10,100})'
            address_match = re.search(address_pattern, text, re.IGNORECASE)
            if address_match:
                result['address'] = address_match.group(1).strip()
            
            logger.debug(f"Extracted: phone={result['phone']}, email={result['email']}")
            
        except Exception as e:
            logger.debug(f"Error extracting from gmaps: {str(e)}")
        
        return result
    
    def process_school(self, school_name, taluka_name='', existing_gmaps_link=None):
        """
        Process one school:
        1. Use existing gmaps link if available
        2. Otherwise, search for it
        3. Extract data from gmaps link
        """
        logger.info(f"Processing: {school_name}")
        
        result = {
            'school_name': school_name,
            'gmaps_link': '',
            'address': '',
            'phone': '',
            'email': '',
            'website': '',
            'pincode': '',
            'data_source': 'Not Found',
            'data_complete': 0
        }
        
        # Step 1: Get or find gmaps link
        if existing_gmaps_link and pd.notna(existing_gmaps_link):
            gmaps_link = existing_gmaps_link
            result['gmaps_link'] = gmaps_link
            logger.debug(f"Using existing gmaps link")
        else:
            gmaps_link = self.find_gmaps_link(school_name, taluka_name)
            result['gmaps_link'] = gmaps_link or ''
            
            if not gmaps_link:
                self.failed_count += 1
                logger.info(f"✗ Could not find gmaps link for {school_name}")
                return result
            
            logger.debug(f"✓ Found gmaps link")
        
        # Step 2: Extract data from gmaps
        time.sleep(random.uniform(0.5, 1.5))
        
        gmaps_data = self.extract_from_gmaps(gmaps_link)
        result.update(gmaps_data)
        
        # Determine data source
        if gmaps_data['phone'] or gmaps_data['email']:
            result['data_source'] = 'Google Maps'
            self.found_count += 1
            logger.info(f"✓ Found: {gmaps_data['phone']} {gmaps_data['email']}")
        else:
            logger.info(f"✗ No data extracted from gmaps")
        
        # Calculate completeness
        result['data_complete'] = sum([
            bool(gmaps_data['address']),
            bool(gmaps_data['phone']),
            bool(gmaps_data['email']),
            bool(gmaps_data['website']),
            bool(gmaps_data['pincode'])
        ])
        
        return result
    
    def process_schools(self, schools_data, max_workers=2):
        """
        Process multiple schools concurrently
        schools_data: list of (school_name, taluka_name, gmaps_link) tuples
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_school, name, taluka, link): name
                for name, taluka, link in schools_data
            }
            
            completed = 0
            total = len(schools_data)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    logger.info(f"Progress: {completed}/{total}")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
        
        return results

def main():
    """Main execution"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║             TWO-STAGE SCHOOL DATA SCRAPER                          ║
║   Stage 1: Find Google Maps links                                  ║
║   Stage 2: Extract address, phone, email, website                  ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Get input file
    if len(sys.argv) < 2:
        print("Usage: python script.py YOUR_FILE.xlsx")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Load file
    logger.info(f"Loading {input_file}...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        sys.exit(1)
    
    # Validate
    if 'school_name' not in df.columns:
        logger.error("Column 'school_name' not found!")
        sys.exit(1)
    
    # Prepare data
    schools_data = []
    for idx, row in df.iterrows():
        school_name = row['school_name']
        taluka_name = row.get('_taluka_name', '')
        gmaps_link = row.get('gmaps link', None)
        schools_data.append((school_name, taluka_name, gmaps_link))
    
    logger.info(f"Found {len(schools_data)} schools")
    logger.info(f"Schools with gmaps links: {sum(1 for _, _, link in schools_data if pd.notna(link))}")
    
    # Run scraper
    logger.info("Starting 2-stage scraper...")
    scraper = TwoStageScraper()
    results = scraper.process_schools(schools_data, max_workers=2)
    
    # Update dataframe
    logger.info("Updating dataframe...")
    results_dict = {r['school_name']: r for r in results}
    
    for col in ['gmaps_link', 'address', 'phone', 'email', 'website', 'pincode', 'data_source', 'data_complete']:
        if col not in df.columns:
            df[col] = ''
    
    for idx, row in df.iterrows():
        school_name = row['school_name']
        if school_name in results_dict:
            result = results_dict[school_name]
            df.at[idx, 'gmaps_link'] = result['gmaps_link']
            df.at[idx, 'address'] = result['address']
            df.at[idx, 'phone'] = result['phone']
            df.at[idx, 'email'] = result['email']
            df.at[idx, 'website'] = result['website']
            df.at[idx, 'pincode'] = result['pincode']
            df.at[idx, 'data_source'] = result['data_source']
            df.at[idx, 'data_complete'] = result['data_complete']
    
    # Save
    output_file = input_file.replace('.xlsx', '_WITH_LEADS.xlsx')
    logger.info(f"Saving to {output_file}...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total schools: {len(df)}")
    print(f"Gmaps links found: {scraper.found_count}")
    print(f"Failed: {scraper.failed_count}")
    print(f"Phones: {(df['phone'] != '').sum()}")
    print(f"Emails: {(df['email'] != '').sum()}")
    print(f"Websites: {(df['website'] != '').sum()}")
    print(f"Complete (3+ fields): {(df['data_complete'] >= 3).sum()}")
    print(f"\n✓ Saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
