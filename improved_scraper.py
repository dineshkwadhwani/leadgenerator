"""
IMPROVED Lead Generator - Better error handling and multiple search strategies
Works with ANY Excel file containing school_name column
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

# Configuration
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

class ImprovedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.found_count = 0
        self.failed_count = 0
    
    def get_page(self, url, timeout=10):
        """Get page with error handling"""
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = self.session.get(url, timeout=timeout, headers=headers)
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
        return None
    
    def extract_phone_email(self, text):
        """Extract phone and email"""
        phone = ''
        email = ''
        
        # Phone
        phone_match = re.search(r'[6-9]\d{9}', text)
        if phone_match:
            phone = phone_match.group(0)
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            email = email_match.group(0)
            if 'noreply' in email.lower() or 'gmail.com' in email:
                email = ''
        
        return phone, email
    
    def search_google(self, school_name):
        """Search using Google"""
        logger.debug(f"Google search: {school_name}")
        result = {'phone': '', 'email': '', 'website': ''}
        
        try:
            # Try Google search via DuckDuckGo HTML
            query = f'"{school_name}" Pune contact phone'
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.get_page(url)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='result__a', limit=5)
            
            for link in links:
                href = link.get('href')
                if not href or not href.startswith('http'):
                    continue
                
                page = self.get_page(href)
                if not page:
                    continue
                
                text = page.text
                phone, email = self.extract_phone_email(text)
                
                if phone:
                    result['phone'] = phone
                if email:
                    result['email'] = email
                
                # Extract website
                website_match = re.search(r'https?://(?:www\.)?[\w\-\.]+\.\w+', text)
                if website_match and 'facebook' not in website_match.group(0):
                    result['website'] = website_match.group(0)
                
                if result['phone'] or result['email']:
                    return result
                
                time.sleep(random.uniform(0.5, 1.5))
        
        except Exception as e:
            logger.debug(f"Google search error: {str(e)}")
        
        return result
    
    def search_justdial(self, school_name):
        """Search JustDial directly"""
        logger.debug(f"JustDial search: {school_name}")
        result = {'phone': '', 'email': '', 'website': ''}
        
        try:
            # Direct JustDial search
            query = f'{school_name} Pune'
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' site:justdial.com')}"
            
            response = self.get_page(url)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            link = soup.find('a', class_='result__a')
            
            if link and link.get('href'):
                page = self.get_page(link['href'])
                if page:
                    text = page.text
                    phone, email = self.extract_phone_email(text)
                    if phone:
                        result['phone'] = phone
                    if email:
                        result['email'] = email
        
        except Exception as e:
            logger.debug(f"JustDial search error: {str(e)}")
        
        return result
    
    def search_schoolmykids(self, school_name):
        """Search SchoolMyKids"""
        logger.debug(f"SchoolMyKids search: {school_name}")
        result = {'phone': '', 'email': '', 'website': ''}
        
        try:
            query = f'{school_name} Pune'
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' site:schoolmykids.com')}"
            
            response = self.get_page(url)
            if not response:
                return result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            link = soup.find('a', class_='result__a')
            
            if link and link.get('href'):
                page = self.get_page(link['href'])
                if page:
                    text = page.text
                    phone, email = self.extract_phone_email(text)
                    if phone:
                        result['phone'] = phone
                    if email:
                        result['email'] = email
        
        except Exception as e:
            logger.debug(f"SchoolMyKids search error: {str(e)}")
        
        return result
    
    def search_school(self, school_name):
        """Main search function - try multiple sources"""
        logger.info(f"Processing: {school_name}")
        
        result = {
            'school_name': school_name,
            'phone': '',
            'email': '',
            'website': '',
            'address': '',
            'lead_source': 'Not Found',
            'data_complete': 0
        }
        
        # Try Google first
        google_result = self.search_google(school_name)
        if google_result['phone'] or google_result['email']:
            result.update(google_result)
            result['lead_source'] = 'Google Search'
            self.found_count += 1
            logger.info(f"✓ Found: {google_result['phone']} {google_result['email']}")
            return result
        
        time.sleep(random.uniform(1, 2))
        
        # Try JustDial
        jd_result = self.search_justdial(school_name)
        if jd_result['phone'] or jd_result['email']:
            result.update(jd_result)
            result['lead_source'] = 'JustDial'
            self.found_count += 1
            logger.info(f"✓ Found on JustDial: {jd_result['phone']}")
            return result
        
        time.sleep(random.uniform(1, 2))
        
        # Try SchoolMyKids
        smk_result = self.search_schoolmykids(school_name)
        if smk_result['phone'] or smk_result['email']:
            result.update(smk_result)
            result['lead_source'] = 'SchoolMyKids'
            self.found_count += 1
            logger.info(f"✓ Found on SchoolMyKids: {smk_result['phone']}")
            return result
        
        self.failed_count += 1
        logger.info(f"✗ Not found: {school_name}")
        return result
    
    def process_schools(self, school_names, max_workers=3):
        """Process multiple schools concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.search_school, name): name for name in school_names}
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    logger.info(f"Progress: {completed}/{len(school_names)}")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
        
        return results

def main():
    """Main execution"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║         IMPROVED LEAD GENERATOR - School Contact Scraper           ║
║                    Better Error Handling & Logging                 ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Get input file
    if len(sys.argv) < 2:
        print("Usage: python script.py YOUR_FILE.xlsx")
        print("Example: python script.py PIMPRI_CHICHWAD_MNP.xlsx")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Load file
    logger.info(f"Loading {input_file}...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        sys.exit(1)
    
    if 'school_name' not in df.columns:
        logger.error("Column 'school_name' not found!")
        logger.error(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)
    
    # Get unique schools
    schools = df['school_name'].dropna().unique().tolist()
    logger.info(f"Found {len(schools)} schools to process")
    
    # Run scraper
    logger.info("Starting scraper...")
    scraper = ImprovedScraper()
    results = scraper.process_schools(schools, max_workers=3)
    
    # Add results to dataframe
    logger.info("Updating dataframe...")
    df['phone'] = df['school_name'].map(lambda x: next((r['phone'] for r in results if r['school_name'] == x), ''))
    df['email'] = df['school_name'].map(lambda x: next((r['email'] for r in results if r['school_name'] == x), ''))
    df['website'] = df['school_name'].map(lambda x: next((r['website'] for r in results if r['school_name'] == x), ''))
    df['lead_source'] = df['school_name'].map(lambda x: next((r['lead_source'] for r in results if r['school_name'] == x), 'Not Found'))
    
    df['data_complete'] = (
        (df['phone'] != '').astype(int) +
        (df['email'] != '').astype(int) +
        (df['website'] != '').astype(int)
    )
    
    # Save results
    output_file = input_file.replace('.xlsx', '_WITH_LEADS.xlsx')
    logger.info(f"Saving to {output_file}...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total schools: {len(df)}")
    print(f"Found: {scraper.found_count}")
    print(f"Not found: {scraper.failed_count}")
    print(f"Phones: {(df['phone'] != '').sum()}")
    print(f"Emails: {(df['email'] != '').sum()}")
    print(f"Websites: {(df['website'] != '').sum()}")
    print(f"\n✓ Saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
