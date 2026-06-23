"""
AUTOMATED SCHOOL DATA SCRAPER - Multi-Source Approach
Searches: JustDial, SchoolMyKids, Ezyschooling, Careers360
Extracts: Phone, Email, Website, Address, Pincode
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'multi_source_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

class MultiSourceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.found_count = 0
        self.failed_count = 0
        self.sources_used = {}
    
    def get_page(self, url, timeout=10):
        """Get page with error handling"""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = self.session.get(url, timeout=timeout, headers=headers)
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
        return None
    
    def extract_contact_info(self, text):
        """Extract phone, email, website from text"""
        result = {'phone': '', 'email': '', 'website': ''}
        
        # Phone (Indian 10-digit)
        phone_match = re.search(r'\b[6-9]\d{9}\b', text)
        if phone_match:
            result['phone'] = phone_match.group(0)
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            email = email_match.group(0)
            if 'noreply' not in email.lower() and 'gmail.com' not in email.lower():
                result['email'] = email
        
        # Website
        website_match = re.search(r'https?://(?:www\.)?[\w\-\.]+\.\w+', text)
        if website_match:
            url = website_match.group(0)
            if 'google' not in url.lower() and 'facebook' not in url.lower():
                result['website'] = url
        
        return result
    
    def search_justdial(self, school_name, city='Pune'):
        """Search JustDial for school"""
        logger.debug(f"JustDial: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'source': ''}
        
        try:
            # JustDial search
            query = f"{school_name} {city}"
            search_url = f"https://www.justdial.com/search?kw={quote_plus(query)}&ctg=catid_1262819570313344"
            
            response = self.get_page(search_url, timeout=15)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find listing with phone
            listings = soup.find_all('div', class_='listing-box')
            
            for listing in listings[:3]:  # Check first 3 listings
                listing_text = listing.get_text()
                
                # Extract phone from listing
                phone_match = re.search(r'\b[6-9]\d{9}\b', listing_text)
                if phone_match:
                    result['phone'] = phone_match.group(0)
                
                # Try to get website link
                website_link = listing.find('a', {'data-val': 'website'})
                if website_link and website_link.get('href'):
                    result['website'] = website_link['href']
                
                if result['phone']:
                    result['source'] = 'JustDial'
                    return result
            
        except Exception as e:
            logger.debug(f"JustDial error: {str(e)}")
        
        return result
    
    def search_schoolmykids(self, school_name, city='Pune'):
        """Search SchoolMyKids for school"""
        logger.debug(f"SchoolMyKids: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'source': ''}
        
        try:
            # SchoolMyKids search
            search_url = f"https://www.schoolmykids.com/find/schools?query={quote_plus(school_name)}&city=pune"
            
            response = self.get_page(search_url, timeout=15)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find school listings
            schools = soup.find_all('div', class_='school-item')
            
            for school in schools[:2]:
                school_text = school.get_text()
                
                # Extract contact info
                contact = self.extract_contact_info(school_text)
                if contact['phone']:
                    result['phone'] = contact['phone']
                    result['email'] = contact['email']
                    result['website'] = contact['website']
                    result['source'] = 'SchoolMyKids'
                    return result
            
        except Exception as e:
            logger.debug(f"SchoolMyKids error: {str(e)}")
        
        return result
    
    def search_ezyschooling(self, school_name, city='Pune'):
        """Search EzySchooling for school"""
        logger.debug(f"EzySchooling: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'source': ''}
        
        try:
            search_url = f"https://www.ezyschooling.com/schools/search?query={quote_plus(school_name)}&location=pune"
            
            response = self.get_page(search_url, timeout=15)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            
            # Extract contact info from page
            contact = self.extract_contact_info(page_text)
            if contact['phone']:
                result.update(contact)
                result['source'] = 'EzySchooling'
                return result
            
        except Exception as e:
            logger.debug(f"EzySchooling error: {str(e)}")
        
        return result
    
    def search_careers360(self, school_name, city='Pune'):
        """Search Careers360 for school"""
        logger.debug(f"Careers360: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'source': ''}
        
        try:
            search_url = f"https://school.careers360.com/search?query={quote_plus(school_name)}&location=pune"
            
            response = self.get_page(search_url, timeout=15)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            
            # Extract contact info
            contact = self.extract_contact_info(page_text)
            if contact['phone'] or contact['email']:
                result.update(contact)
                result['source'] = 'Careers360'
                return result
            
        except Exception as e:
            logger.debug(f"Careers360 error: {str(e)}")
        
        return result
    
    def search_google_direct(self, school_name, city='Pune'):
        """Direct Google search for school contact info"""
        logger.debug(f"Google Search: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'source': ''}
        
        try:
            # Search via DuckDuckGo (more reliable for scraping)
            query = f'"{school_name}" {city} school phone email contact'
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.get_page(search_url, timeout=15)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='result__a', limit=5)
            
            for link in links:
                href = link.get('href')
                if not href or not href.startswith('http'):
                    continue
                
                page = self.get_page(href, timeout=12)
                if not page:
                    continue
                
                # Extract contact info from page
                contact = self.extract_contact_info(page.text)
                
                if contact['phone']:
                    result.update(contact)
                    result['source'] = 'Google Search'
                    return result
                
                time.sleep(0.5)
            
        except Exception as e:
            logger.debug(f"Google search error: {str(e)}")
        
        return result
    
    def search_school(self, school_name, city='Pune'):
        """Search multiple sources for school data"""
        logger.info(f"Searching: {school_name}")
        
        result = {
            'school_name': school_name,
            'phone': '',
            'email': '',
            'website': '',
            'data_source': 'Not Found',
            'data_complete': 0
        }
        
        # Try sources in order of reliability
        sources = [
            ('JustDial', self.search_justdial),
            ('SchoolMyKids', self.search_schoolmykids),
            ('EzySchooling', self.search_ezyschooling),
            ('Careers360', self.search_careers360),
            ('Google', self.search_google_direct),
        ]
        
        for source_name, search_func in sources:
            try:
                data = search_func(school_name, city)
                
                if data['phone'] or data['email']:
                    result['phone'] = data['phone']
                    result['email'] = data['email']
                    result['website'] = data['website']
                    result['data_source'] = source_name
                    result['data_complete'] = sum([
                        bool(data['phone']),
                        bool(data['email']),
                        bool(data['website'])
                    ])
                    
                    self.found_count += 1
                    self.sources_used[source_name] = self.sources_used.get(source_name, 0) + 1
                    logger.info(f"✓ Found on {source_name}: {data['phone']}")
                    return result
                
            except Exception as e:
                logger.debug(f"Error with {source_name}: {str(e)}")
                continue
            
            # Rate limiting between sources
            time.sleep(random.uniform(1, 2))
        
        self.failed_count += 1
        logger.info(f"✗ Not found: {school_name}")
        return result
    
    def process_schools(self, schools_data, max_workers=2):
        """Process multiple schools concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.search_school, name, city): name
                for name, city in schools_data
            }
            
            completed = 0
            total = len(schools_data)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    if completed % 10 == 0:
                        logger.info(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
        
        return results

def main():
    """Main execution"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║         AUTOMATED MULTI-SOURCE SCHOOL DATA SCRAPER                ║
║    Searches: JustDial, SchoolMyKids, EzySchooling, Careers360     ║
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
        city = 'Pune'  # You can customize this
        schools_data.append((school_name, city))
    
    logger.info(f"Found {len(schools_data)} schools to process")
    
    # Run scraper
    logger.info("Starting multi-source scraper...")
    scraper = MultiSourceScraper()
    results = scraper.process_schools(schools_data, max_workers=2)
    
    # Update dataframe
    logger.info("Updating dataframe...")
    results_dict = {r['school_name']: r for r in results}
    
    for col in ['phone', 'email', 'website', 'data_source', 'data_complete']:
        if col not in df.columns:
            df[col] = ''
    
    for idx, row in df.iterrows():
        school_name = row['school_name']
        if school_name in results_dict:
            result = results_dict[school_name]
            df.at[idx, 'phone'] = result['phone']
            df.at[idx, 'email'] = result['email']
            df.at[idx, 'website'] = result['website']
            df.at[idx, 'data_source'] = result['data_source']
            df.at[idx, 'data_complete'] = result['data_complete']
    
    # Save
    output_file = input_file.replace('.xlsx', '_LEADS.xlsx')
    logger.info(f"Saving to {output_file}...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total schools: {len(df)}")
    print(f"Found: {scraper.found_count}")
    print(f"Failed: {scraper.failed_count}")
    print(f"Success rate: {scraper.found_count/len(df)*100:.1f}%")
    print(f"\nPhones found: {(df['phone'] != '').sum()}")
    print(f"Emails found: {(df['email'] != '').sum()}")
    print(f"Websites found: {(df['website'] != '').sum()}")
    print(f"\nSources used:")
    for source, count in scraper.sources_used.items():
        print(f"  {source}: {count}")
    print(f"\n✓ Saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
