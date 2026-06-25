"""Quick lead generator - searches for school contact information"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import get_logger

logger = get_logger()

# Configuration
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
]

def get_session():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
    return session

def get_url(url, session=None, timeout=10):
    """Make GET request with error handling"""
    if session is None:
        session = get_session()
    
    try:
        response = session.get(url, timeout=timeout)
        return response if response.status_code == 200 else None
    except:
        return None

def extract_contact_from_text(text):
    """Extract phone, email from text"""
    result = {'phone': '', 'email': ''}
    
    # Extract phone (10-digit Indian format)
    phone_match = re.search(r'[6-9]\d{9}', text)
    if phone_match:
        result['phone'] = phone_match.group(0)
    
    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        email = email_match.group(0)
        if 'noreply' not in email.lower() and 'gmail.com' not in email.lower():
            result['email'] = email
    
    return result

def search_school(school_name):
    """Search for school information"""
    logger.info(f"Searching: {school_name}")
    
    result = {
        'school_name': school_name,
        'address': '',
        'website': '',
        'phone': '',
        'email': '',
        'source': 'Not Found'
    }
    
    # Build search query
    query = f'"{school_name}" Pune school contact'
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    
    session = get_session()
    response = get_url(search_url, session)
    
    if not response:
        logger.debug(f"  No search results")
        return result
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_='result__a', limit=3)
    
    for link in links:
        url = link.get('href')
        if not url or not url.startswith('http'):
            continue
        
        logger.debug(f"  Visiting: {url}")
        page = get_url(url, session)
        
        if not page:
            continue
        
        page_soup = BeautifulSoup(page.text, 'html.parser')
        page_text = page_soup.get_text()
        
        # Extract contact info
        contact_info = extract_contact_from_text(page_text)
        
        if contact_info['phone']:
            result['phone'] = contact_info['phone']
        
        if contact_info['email']:
            result['email'] = contact_info['email']
        
        # Extract website
        if 'facebook' not in url and 'google' not in url:
            website_match = re.search(r'https?://[^\s/$.?#].[^\s]*', page_text)
            if website_match:
                result['website'] = website_match.group(0)
        
        time.sleep(random.uniform(1, 2))
        
        # If we found data, stop
        if result['phone'] or result['email']:
            result['source'] = 'Web Search'
            logger.info(f"  ✓ Found: {result.get('phone', '')} {result.get('email', '')}")
            break
    
    return result

def search_justdial(school_name):
    """Search JustDial for additional information"""
    logger.debug(f"  Checking JustDial: {school_name}")
    
    result = {'phone': '', 'website': ''}
    
    query = f'"{school_name}" site:justdial.com'
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    
    session = get_session()
    response = get_url(search_url, session)
    
    if not response:
        return result
    
    soup = BeautifulSoup(response.text, 'html.parser')
    link = soup.find('a', class_='result__a')
    
    if link and link.get('href'):
        page = get_url(link['href'], session)
        if page:
            text = page.text
            phone_match = re.search(r'[6-9]\d{9}', text)
            if phone_match:
                result['phone'] = phone_match.group(0)
    
    time.sleep(1)
    return result

def process_school_wrapper(args):
    """Wrapper for concurrent processing"""
    school_name, gmaps_url, pincode = args
    
    lead_info = search_school(school_name)
    
    # If phone not found, try JustDial
    if not lead_info['phone']:
        jd_info = search_justdial(school_name)
        if jd_info['phone']:
            lead_info['phone'] = jd_info['phone']
            lead_info['source'] = 'JustDial'
    
    # Add timestamp
    lead_info['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return lead_info

def process_schools_concurrent(schools_data, max_workers=5):
    """Process multiple schools concurrently"""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_school_wrapper, args): args[0] for args in schools_data}
        
        completed = 0
        total = len(schools_data)
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                completed += 1
                logger.info(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)")
            except Exception as e:
                school_name = futures[future]
                logger.error(f"Error processing {school_name}: {str(e)}")
                results.append({
                    'school_name': school_name,
                    'address': 'Error',
                    'website': 'Error',
                    'phone': 'Error',
                    'email': 'Error',
                    'source': 'Error',
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return results
