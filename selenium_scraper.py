"""
SELENIUM-BASED SCHOOL DATA SCRAPER
Opens real browser → Searches for schools → Extracts phone, email, website, address
Bypasses bot detection | Handles JavaScript | Progress tracking | Resume capability
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import time
import json
import logging
from datetime import datetime
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'selenium_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeleniumSchoolScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.found_count = 0
        self.failed_count = 0
        self.progress_file = 'selenium_progress.json'
        self.progress = self.load_progress()
    
    def setup_driver(self):
        """Setup Chrome driver with headless option"""
        logger.info("Setting up Chrome driver...")
        
        chrome_options = Options()
        # Uncomment to run headless (no browser window)
        # chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("✓ Chrome driver ready")
        except Exception as e:
            logger.error(f"Failed to setup driver: {str(e)}")
            logger.error("Make sure ChromeDriver is installed: https://chromedriver.chromium.org/")
            sys.exit(1)
    
    def load_progress(self):
        """Load progress from previous run"""
        if Path(self.progress_file).exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    logger.info(f"Loaded progress: {len(progress)} schools already processed")
                    return progress
            except:
                pass
        return {}
    
    def save_progress(self):
        """Save progress to resume later"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
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
    
    def search_google_maps(self, school_name, city='Pune'):
        """Search school on Google Maps"""
        logger.debug(f"Searching Google Maps: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'address': '', 'source': ''}
        
        try:
            # Navigate to Google Maps
            search_query = f"{school_name} {city} Pune school"
            maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            
            self.driver.get(maps_url)
            time.sleep(3)  # Wait for page to load
            
            # Get page source
            page_text = self.driver.page_source
            
            # Extract contact info
            contact = self.extract_contact_info(page_text)
            result.update(contact)
            
            # Try to get address from page
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-item-id="address"]')
                if address_elem:
                    result['address'] = address_elem.text
            except:
                pass
            
            # Try to find phone in visible text
            try:
                info_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-item-id="phone"]')
                if info_elem:
                    phone_text = info_elem.text
                    phone_match = re.search(r'\b[6-9]\d{9}\b', phone_text)
                    if phone_match:
                        result['phone'] = phone_match.group(0)
            except:
                pass
            
            if result['phone'] or result['email']:
                result['source'] = 'Google Maps'
                return result
            
        except Exception as e:
            logger.debug(f"Google Maps error: {str(e)}")
        
        return result
    
    def search_google_website(self, school_name, city='Pune'):
        """Search for school website on Google"""
        logger.debug(f"Searching Google: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'address': '', 'source': ''}
        
        try:
            # Search on Google
            search_query = f"{school_name} {city} school contact phone website"
            google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            self.driver.get(google_url)
            time.sleep(2)
            
            # Try to find school website link
            try:
                # Look for knowledge panel or search results
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                
                for link in links[:10]:
                    href = link.get_attribute('href')
                    link_text = link.text
                    
                    if href and 'google' not in href and 'facebook' not in href:
                        # Visit this link
                        try:
                            self.driver.execute_script(f"window.open('{href}', '_blank');")
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            time.sleep(2)
                            
                            page_text = self.driver.page_source
                            contact = self.extract_contact_info(page_text)
                            
                            if contact['phone'] or contact['email']:
                                result.update(contact)
                                result['source'] = 'Google Search'
                                
                                # Close this tab and return to main
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                return result
                            
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                            
                        except:
                            pass
            
            except Exception as e:
                logger.debug(f"Error browsing results: {str(e)}")
        
        except Exception as e:
            logger.debug(f"Google search error: {str(e)}")
        
        return result
    
    def search_justdial_browser(self, school_name, city='Pune'):
        """Search JustDial using browser (bypasses bot detection)"""
        logger.debug(f"Searching JustDial: {school_name}")
        result = {'phone': '', 'email': '', 'website': '', 'address': '', 'source': ''}
        
        try:
            # Navigate to JustDial
            search_query = f"{school_name} {city}"
            jd_url = f"https://www.justdial.com/search?kw={search_query.replace(' ', '+')}"
            
            self.driver.get(jd_url)
            time.sleep(3)
            
            # Get page source
            page_text = self.driver.page_source
            
            # Extract phone and email
            contact = self.extract_contact_info(page_text)
            result.update(contact)
            
            if result['phone']:
                result['source'] = 'JustDial'
                return result
            
        except Exception as e:
            logger.debug(f"JustDial error: {str(e)}")
        
        return result
    
    def search_school(self, school_name, city='Pune'):
        """Search school using multiple browser-based methods"""
        logger.info(f"Processing: {school_name}")
        
        # Check if already processed
        if school_name in self.progress:
            logger.info(f"  (cached) {school_name}")
            return self.progress[school_name]
        
        result = {
            'school_name': school_name,
            'phone': '',
            'email': '',
            'website': '',
            'address': '',
            'data_source': 'Not Found',
            'data_complete': 0
        }
        
        try:
            # Try Google Maps first
            maps_result = self.search_google_maps(school_name, city)
            if maps_result['phone'] or maps_result['email']:
                result['phone'] = maps_result['phone']
                result['email'] = maps_result['email']
                result['website'] = maps_result['website']
                result['address'] = maps_result['address']
                result['data_source'] = maps_result['source']
                self.found_count += 1
                logger.info(f"✓ Found on {maps_result['source']}")
                
                # Save progress
                self.progress[school_name] = result
                self.save_progress()
                return result
            
            time.sleep(2)
            
            # Try JustDial
            jd_result = self.search_justdial_browser(school_name, city)
            if jd_result['phone'] or jd_result['email']:
                result['phone'] = jd_result['phone']
                result['email'] = jd_result['email']
                result['website'] = jd_result['website']
                result['address'] = jd_result['address']
                result['data_source'] = jd_result['source']
                self.found_count += 1
                logger.info(f"✓ Found on {jd_result['source']}")
                
                # Save progress
                self.progress[school_name] = result
                self.save_progress()
                return result
            
            time.sleep(2)
            
            # Try Google Search
            google_result = self.search_google_website(school_name, city)
            if google_result['phone'] or google_result['email']:
                result['phone'] = google_result['phone']
                result['email'] = google_result['email']
                result['website'] = google_result['website']
                result['address'] = google_result['address']
                result['data_source'] = google_result['source']
                self.found_count += 1
                logger.info(f"✓ Found on {google_result['source']}")
                
                # Save progress
                self.progress[school_name] = result
                self.save_progress()
                return result
            
        except Exception as e:
            logger.error(f"Error processing {school_name}: {str(e)}")
        
        self.failed_count += 1
        logger.info(f"✗ Not found: {school_name}")
        
        # Save progress
        self.progress[school_name] = result
        self.save_progress()
        return result
    
    def process_schools(self, school_names, city='Pune'):
        """Process schools one by one"""
        results = []
        
        for idx, school_name in enumerate(school_names):
            logger.info(f"\n[{idx+1}/{len(school_names)}] Processing...")
            
            result = self.search_school(school_name, city)
            results.append(result)
            
            # Calculate completeness
            result['data_complete'] = sum([
                bool(result['phone']),
                bool(result['email']),
                bool(result['website']),
                bool(result['address'])
            ])
            
            # Small delay between searches
            time.sleep(1)
        
        return results
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

def main():
    """Main execution"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║              SELENIUM SCHOOL DATA SCRAPER                          ║
║         Opens Real Browser → Extracts Phone/Email/Website         ║
║              Bypasses Bot Detection ✓                              ║
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
    
    # Validate
    if 'school_name' not in df.columns:
        logger.error("Column 'school_name' not found!")
        sys.exit(1)
    
    school_names = df['school_name'].dropna().unique().tolist()
    logger.info(f"Found {len(school_names)} schools")
    
    # Initialize scraper
    scraper = SeleniumSchoolScraper()
    
    try:
        scraper.setup_driver()
        
        # Process schools
        logger.info("Starting selenium scraper...")
        results = scraper.process_schools(school_names)
        
        # Update dataframe
        logger.info("Updating dataframe...")
        results_dict = {r['school_name']: r for r in results}
        
        for col in ['phone', 'email', 'website', 'address', 'data_source', 'data_complete']:
            if col not in df.columns:
                df[col] = ''
        
        for idx, row in df.iterrows():
            school_name = row['school_name']
            if school_name in results_dict:
                result = results_dict[school_name]
                df.at[idx, 'phone'] = result['phone']
                df.at[idx, 'email'] = result['email']
                df.at[idx, 'website'] = result['website']
                df.at[idx, 'address'] = result['address']
                df.at[idx, 'data_source'] = result['data_source']
                df.at[idx, 'data_complete'] = result['data_complete']
        
        # Save
        output_file = input_file.replace('.xlsx', '_SELENIUM_LEADS.xlsx')
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
        print(f"Addresses found: {(df['address'] != '').sum()}")
        print(f"\n✓ Saved to: {output_file}")
        print(f"✓ Progress saved to: {scraper.progress_file}")
        print("="*70)
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
