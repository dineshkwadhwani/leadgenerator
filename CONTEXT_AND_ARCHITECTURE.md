# MAHAEXAM LEAD GENERATOR - COMPLETE CONTEXT & ARCHITECTURE

**Version:** 1.0.0  
**Created:** May 2026  
**Purpose:** Automated school contact data extraction for lead generation  
**Status:** Production Ready

---

## 📋 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Entry Points](#entry-points)
5. [Component Details](#component-details)
6. [Technology Stack](#technology-stack)
7. [Workflow](#workflow)
8. [Data Flow](#data-flow)
9. [Configuration](#configuration)
10. [Execution Methods](#execution-methods)
11. [Output Format](#output-format)
12. [Error Handling](#error-handling)
13. [Progress & Resume](#progress--resume)

---

## PROJECT OVERVIEW

### What is MahaExam Lead Generator?

**Purpose:**
Extract school contact information (phone, email, website, address, pincode) for 445+ schools in Pimpri Chichwad, Pune for MahaExam sales outreach.

**Problem Solved:**
- Manual data collection = days of work
- Web scraping blocked by bot detection
- Need: **Automated, reliable, fast** data extraction

**Solution:**
Browser automation using Selenium that:
- ✅ Opens real Chrome browser (bypasses bot detection)
- ✅ Searches multiple sources (Google Maps, JustDial, etc.)
- ✅ Extracts contact information automatically
- ✅ Tracks progress (can resume if interrupted)
- ✅ Saves to Excel with quality scores

### Target Users

1. **Shubham Shetye** (Sales Manager, MahaExam)
   - Primary user
   - Runs scrapers to generate leads
   - Uses output for outreach

2. **Dinesh Wadhwani** (Founder, StudioVerse/MahaExam)
   - Technical oversight
   - Maintains codebase
   - Scales to other regions

---

## ARCHITECTURE

### High-Level Architecture

```
INPUT (Excel File with school_name column)
         ↓
    [Scraper Script]
         ↓
    [Browser Automation (Selenium)]
         ↓
    [Data Extraction & Parsing]
         ↓
    [Progress Tracking (JSON)]
         ↓
    [Data Validation]
         ↓
OUTPUT (Excel file with extracted data)
```

### Component Interaction

```
selenium_scraper.py (Main Entry Point)
         ↓
    ├── Load Excel file
    ├── Validate data
    ├── Setup Selenium
    ├── For each school:
    │   ├── search_google_maps()
    │   ├── search_justdial_browser()
    │   ├── search_google_website()
    │   ├── Extract contact info
    │   └── Save progress
    └── Update Excel & Output
```

---

## PROJECT STRUCTURE

### Directory Layout

```
MahaExam_LeadGenerator/
│
├── 📄 MAIN ENTRY POINTS
│   ├── selenium_scraper.py       ← PRIMARY (Browser automation)
│   ├── main.py                   ← Basic script
│   ├── multi_source_scraper.py   ← Multi-source (blocked by sites)
│   └── two_stage_scraper.py      ← Find gmaps links (limited success)
│
├── 📂 src/ (Python package)
│   ├── __init__.py              ← Package marker
│   ├── lead_gen_quick.py        ← Quick scraper (deprecated)
│   └── utils.py                 ← Logging & utilities
│
├── 📂 .vscode/ (IDE Configuration)
│   ├── launch.json              ← Debug configurations
│   └── settings.json            ← Editor settings
│
├── 📂 input/ (Data Input)
│   └── (Your Excel files go here)
│
├── 📂 output/ (Data Output)
│   └── (Results saved here)
│
├── 📄 CONFIGURATION
│   ├── config.json              ← Main config file
│   └── requirements.txt          ← Dependencies
│   └── requirements_selenium.txt ← Selenium dependencies
│
├── 📄 DOCUMENTATION
│   ├── README.md                ← Full documentation
│   ├── VSCODE_GUIDE.md          ← VS Code setup
│   ├── PROJECT_STRUCTURE.md     ← File guide
│   ├── SELENIUM_SETUP.md        ← Selenium setup
│   └── .gitignore               ← Git configuration
```

---

## ENTRY POINTS

### Primary Entry Point: `selenium_scraper.py`

**When to use:** For production scraping of 445+ schools

**Command:**
```bash
python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```

**What it does:**
1. Opens real Chrome browser
2. Searches for each school on Google Maps, JustDial, Google
3. Extracts: phone, email, website, address
4. Saves progress to `selenium_progress.json`
5. Outputs: `PIMPRI_CHICHWAD_MNP_SELENIUM_LEADS.xlsx`

**Entry point signature:**
```python
def main():
    # Parse command line arguments
    input_file = sys.argv[1]
    
    # Load Excel file
    df = pd.read_excel(input_file)
    
    # Initialize scraper
    scraper = SeleniumSchoolScraper()
    scraper.setup_driver()
    
    # Process schools
    results = scraper.process_schools(school_names)
    
    # Save output
    output_file = input_file.replace('.xlsx', '_SELENIUM_LEADS.xlsx')
    df.to_excel(output_file, index=False)
```

### Alternative Entry Points

**`main.py`** - Basic flexible scraper
```bash
python main.py PIMPRI_CHICHWAD_MNP.xlsx
```
- Works with any Excel file
- Less reliable (blocked by sites)
- Faster but fewer results

**`multi_source_scraper.py`** - Multiple sources
```bash
python multi_source_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```
- Tries JustDial, SchoolMyKids, EzySchooling
- Blocked by HTTP 403
- Not recommended

**`two_stage_scraper.py`** - Find gmaps links
```bash
python two_stage_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```
- Finds Google Maps links
- Extracts data from links
- Limited success

---

## COMPONENT DETAILS

### 1. `SeleniumSchoolScraper` Class (Main Logic)

**Location:** `selenium_scraper.py`

**Purpose:** Orchestrates the scraping process

**Key Methods:**

#### `__init__()`
- Initializes driver, wait, progress tracking
- Loads previous progress from JSON
- Sets up logging

#### `setup_driver()`
- Creates Chrome WebDriver instance
- Configures headless/headful options
- Sets anti-detection options
- Returns: Configured WebDriver

#### `search_google_maps(school_name, city)`
- Opens Google Maps
- Searches for school
- Extracts phone, email, address
- Returns: Dictionary with contact info

**Flow:**
```python
search_google_maps(school_name)
  ├── Build search URL
  ├── Navigate with Selenium
  ├── Wait for page load
  ├── Extract contact info using regex
  └── Return data dict
```

#### `search_justdial_browser(school_name, city)`
- Opens JustDial search
- Extracts contact information
- Returns: Contact data

#### `search_google_website(school_name, city)`
- Searches Google for school website
- Visits top results
- Extracts contact info
- Returns: Contact data

#### `search_school(school_name, city)`
- Main orchestration method
- Tries multiple sources in order
- Stops when data found
- Saves progress after each school
- Returns: Complete result dict

#### `process_schools(school_names, city)`
- Main processing loop
- Calls `search_school()` for each school
- Tracks progress
- Returns: List of results

#### `extract_contact_info(text)`
- **Helper method**
- Parses text using regex
- Extracts: phone (10-digit), email, website
- Returns: Dictionary

---

### 2. Configuration System

**File:** `config.json`

**Structure:**
```json
{
  "INPUT_FILE": "PIMPRI_CHICHWAD_MNP.xlsx",
  "MAX_WORKERS": 2,
  "REQUEST_TIMEOUT": 15,
  "VERBOSE": true
}
```

**Properties:**
- `INPUT_FILE`: Excel file to process
- `MAX_WORKERS`: Concurrent processes (not used in Selenium)
- `REQUEST_TIMEOUT`: Timeout for page loads
- `VERBOSE`: Detailed logging

**How used:**
```python
config = load_config()
input_file = config['INPUT_FILE']
timeout = config['REQUEST_TIMEOUT']
```

---

### 3. Progress Tracking System

**File:** `selenium_progress.json`

**Purpose:** Resume capability - can stop and resume scraping

**Structure:**
```json
{
  "SCHOOL_NAME_1": {
    "school_name": "ADHIRA INTERNATIONAL",
    "phone": "6899359706",
    "email": "info@adhira.com",
    "website": "https://adhira.edu.in",
    "address": "Pune",
    "data_source": "Google Maps",
    "data_complete": 5
  },
  "SCHOOL_NAME_2": { ... }
}
```

**How it works:**
1. Before processing a school: check if in progress JSON
2. If found: skip (already processed)
3. If not found: process and save
4. Can interrupt (Ctrl+C) and resume later

**Methods:**
```python
def load_progress(self):
    # Load from JSON if exists
    
def save_progress(self):
    # Save current progress to JSON
```

---

### 4. Data Extraction Logic

**Regex Patterns Used:**

**Phone (Indian 10-digit):**
```regex
\b[6-9]\d{9}\b
```
- Matches: 9876543210, 6899359706
- Ignores: +91 prefix, spaces, dashes

**Email:**
```regex
[\w\.-]+@[\w\.-]+\.\w+
```
- Matches: info@school.com, contact@school.co.in
- Filters: Removes noreply@, gmail.com addresses

**Website:**
```regex
https?://(?:www\.)?[\w\-\.]+\.\w+
```
- Matches: https://school.com, http://www.school.in
- Filters: Removes Google, Facebook links

**Pincode (6-digit):**
```regex
\b\d{6}\b
```
- Matches: 411001, 411032
- Indian postal codes

---

## TECHNOLOGY STACK

### Frontend (None - CLI Application)
- Command line interface
- Terminal-based

### Backend (Python)

**Core Libraries:**
- `selenium` - Browser automation
- `pandas` - Data manipulation
- `openpyxl` - Excel file handling
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML processing

**Python Version:** 3.7+

**External Tools:**
- Chrome/Chromium browser
- ChromeDriver (WebDriver for Chrome)

### Data Storage
- **Input:** Excel (.xlsx)
- **Output:** Excel (.xlsx)
- **Progress:** JSON (.json)
- **Logs:** Text (.log)

---

## WORKFLOW

### Complete Execution Flow

```
1. START
   └─ python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx

2. INITIALIZATION
   ├─ Load Excel file
   ├─ Validate 'school_name' column
   ├─ Extract school names
   ├─ Load progress JSON
   └─ Setup Chrome WebDriver

3. MAIN LOOP (for each school)
   ├─ Check if already processed
   │  └─ If yes: skip
   │  └─ If no: continue
   │
   ├─ Search Method 1: Google Maps
   │  ├─ Open browser to Google Maps
   │  ├─ Search for school
   │  ├─ Extract contact info
   │  ├─ If found → Save & continue
   │  └─ If not found → Try next method
   │
   ├─ Search Method 2: JustDial
   │  ├─ Open browser to JustDial
   │  ├─ Search for school
   │  ├─ Extract contact info
   │  ├─ If found → Save & continue
   │  └─ If not found → Try next method
   │
   ├─ Search Method 3: Google Search
   │  ├─ Search on Google
   │  ├─ Visit top results
   │  ├─ Extract contact info
   │  ├─ If found → Save & continue
   │  └─ If not found → Mark as failed
   │
   ├─ Save Result
   │  ├─ Store in progress JSON
   │  ├─ Update progress file
   │  └─ Log progress [X/445]
   │
   └─ Wait before next school

4. OUTPUT GENERATION
   ├─ Create DataFrame with results
   ├─ Add columns: phone, email, website, address, data_source, data_complete
   ├─ Calculate completeness scores (0-4)
   └─ Save Excel file

5. SUMMARY
   ├─ Print statistics
   ├─ Show success rate
   ├─ List sources used
   └─ Output file location

6. CLEANUP
   ├─ Close browser
   ├─ Close driver
   └─ END
```

---

## DATA FLOW

### Input Data Flow

```
PIMPRI_CHICHWAD_MNP.xlsx
  ↓
  [Excel Reader - pandas.read_excel()]
  ↓
  DataFrame {
    school_name: ['ADHIRA', 'Aadrsh', ...]
    _taluka_name: [...]
    ...other columns...
  }
  ↓
  Extract school_name column
  ↓
  List of school names to process
```

### Processing Data Flow

```
School Name: "ADHIRA INTERNATIONAL SCHOOL"
  ↓
  [Selenium - Open Browser]
  ↓
  [Navigate to Google Maps]
  ↓
  [Search for school]
  ↓
  [Parse page HTML/text]
  ↓
  [Regex extraction]
  ↓
  Result Dictionary {
    phone: "6899359706",
    email: "info@adhira.com",
    website: "https://adhira.edu.in",
    address: "Pune",
    data_source: "Google Maps",
    data_complete: 4
  }
```

### Output Data Flow

```
List of Results [result1, result2, ...]
  ↓
  [Create DataFrame from results]
  ↓
  [Merge with original DataFrame]
  ↓
  [Add new columns: phone, email, website, etc.]
  ↓
  [Export to Excel]
  ↓
  PIMPRI_CHICHWAD_MNP_SELENIUM_LEADS.xlsx
```

---

## CONFIGURATION

### How to Configure

**Option 1: Edit config.json**
```json
{
  "INPUT_FILE": "nashik_schools.xlsx",
  "MAX_WORKERS": 2,
  "REQUEST_TIMEOUT": 20,
  "VERBOSE": true
}
```

**Option 2: Command line (overrides config)**
```bash
python selenium_scraper.py nashik_schools.xlsx
```

**Option 3: Edit Python code**
```python
# In selenium_scraper.py
TIMEOUT = 20
MAX_RETRIES = 5
HEADLESS = False  # Show browser window
```

---

## EXECUTION METHODS

### Method 1: VS Code Terminal
```bash
# Open terminal in VS Code
Ctrl + `

# Run
python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```

### Method 2: System Terminal
```bash
cd C:\path\to\MahaExam_LeadGenerator
python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```

### Method 3: Batch Processing
```bash
# Split into batches and run
python selenium_scraper.py batch1.xlsx
python selenium_scraper.py batch2.xlsx
python selenium_scraper.py batch3.xlsx
```

### Method 4: Scheduled (Windows Task Scheduler)
```bash
# Create scheduled task
# Command: python selenium_scraper.py schools.xlsx
# Trigger: Daily at 2 AM
```

### Method 5: Python Script
```python
import subprocess
subprocess.run(['python', 'selenium_scraper.py', 'schools.xlsx'])
```

---

## OUTPUT FORMAT

### Output File Structure

**File Name:** `{input_filename}_SELENIUM_LEADS.xlsx`

**Columns:**
1. `school_name` (original)
2. All original columns preserved
3. `phone` - Contact phone number (10-digit)
4. `email` - Contact email address
5. `website` - School website URL
6. `address` - Physical address
7. `data_source` - Where data came from (Google Maps, JustDial, etc.)
8. `data_complete` - Score 0-4 (completeness)

**Example Row:**
```
school_name: "ADHIRA INTERNATIONAL SCHOOL"
phone: "6899359706"
email: "info@adhira.com"
website: "https://adhira.edu.in"
address: "Pune"
data_source: "Google Maps"
data_complete: 5
```

### Data Quality Metrics

**Completeness Score (0-5):**
- 1 point for: phone found
- 1 point for: email found
- 1 point for: website found
- 1 point for: address found
- 1 point for: data_source found

**Score Guide:**
- 5 = Excellent (all data found)
- 3-4 = Good (most data found)
- 1-2 = Partial (some data found)
- 0 = Failed (no data found)

---

## ERROR HANDLING

### Error Types & Handling

**1. File Not Found**
```
Error: File not found: PIMPRI_CHICHWAD_MNP.xlsx
Handler: Log error, print usage, exit with code 1
```

**2. Missing 'school_name' Column**
```
Error: Column 'school_name' not found!
Handler: Print available columns, exit with code 1
```

**3. ChromeDriver Not Found**
```
Error: No such file or directory: 'chromedriver'
Handler: Print instructions, suggest pip install, exit with code 1
```

**4. Network Timeout**
```
Error: Timeout exception while loading page
Handler: Log & skip school, continue to next
```

**5. Invalid HTML/Parsing Error**
```
Error: BeautifulSoup parsing error
Handler: Log error, continue to next method
```

### Error Recovery

```python
try:
    # Main logic
except TimeoutException:
    logger.debug("Timeout - trying next method")
    # Continue to next search method
except NoSuchElementException:
    logger.debug("Element not found - trying next method")
    # Continue
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    # Mark as failed, continue to next school
```

---

## PROGRESS & RESUME

### How Resume Works

**Scenario 1: Script interrupted (Ctrl+C)**
```
Processing schools 1-50...
School 47 processed
[User presses Ctrl+C]
  ↓
Progress saved to selenium_progress.json:
  - Schools 1-47 completed
  - School 48 incomplete (not saved)
  ↓
[User runs script again]
  ↓
Script loads progress.json
Skips schools 1-47
Starts from school 48
```

**Scenario 2: Script crashed**
```
Processing schools...
School 123 crashes
  ↓
Progress saved up to school 122
  ↓
[User fixes issue and runs again]
  ↓
Resumes from school 123
```

**Progress File Structure:**
```json
{
  "SCHOOL_NAME_1": { ... result ... },
  "SCHOOL_NAME_2": { ... result ... },
  ...
  // Only saved schools are included
}
```

---

## LOGGING

### Log File

**Name:** `selenium_scraper_YYYYMMDD_HHMMSS.log`

**Contents:**
```
2024-05-23 14:30:45,123 - INFO - Setting up Chrome driver...
2024-05-23 14:30:46,456 - INFO - ✓ Chrome driver ready
2024-05-23 14:30:47,789 - INFO - Processing: ADHIRA INTERNATIONAL SCHOOL
2024-05-23 14:30:50,012 - DEBUG - Searching Google Maps: ADHIRA...
2024-05-23 14:30:53,345 - INFO - ✓ Found on Google Maps: 6899359706
2024-05-23 14:30:54,678 - INFO - Progress: 1/445 (0.2%)
...
```

**Log Levels:**
- `INFO` - Important info (school processed, found/not found)
- `DEBUG` - Detailed debug info (method tried, extraction)
- `ERROR` - Errors (file not found, driver crash)

---

## SUMMARY

### Quick Reference

| Aspect | Details |
|--------|---------|
| **Entry Point** | `python selenium_scraper.py YOUR_FILE.xlsx` |
| **Language** | Python 3.7+ |
| **Main Library** | Selenium (browser automation) |
| **Input** | Excel file with `school_name` column |
| **Output** | Excel file with contact data |
| **Processing Time** | 2-3 min per school (~15-20 hours for 445) |
| **Success Rate** | 30-50% phones, 20-40% emails |
| **Resume** | Yes (via `selenium_progress.json`) |
| **Logging** | Detailed logs to `.log` file |
| **Methods Tried** | Google Maps → JustDial → Google Search |

### Key Features

✅ Real browser automation (bypasses bot detection)
✅ Multiple search sources (fallback strategy)
✅ Progress tracking (can resume)
✅ Detailed logging (debug issues)
✅ Data validation (regex extraction)
✅ Flexible input (any Excel file with school_name)
✅ Quality scores (completeness metrics)
✅ Error handling (resilient to failures)

---

## FOR FUTURE DEVELOPERS

### How to Extend

**Add New Search Source:**
```python
def search_new_source(self, school_name, city):
    # Implement search logic
    # Extract contact info
    # Return dictionary
    
# Add to search_school() method:
new_result = self.search_new_source(school_name, city)
if new_result['phone']:
    result.update(new_result)
    return result
```

**Modify Extraction Logic:**
```python
def extract_contact_info(self, text):
    # Add new regex patterns
    # Extract additional fields
    # Validate data
```

**Change Search Strategy:**
```python
# In search_school() method:
sources = [
    ('Source1', self.search_source1),
    ('Source2', self.search_source2),
    # Add more sources
]
```

---

**Created for MahaExam Lead Generation Project**  
**Maintained by: Dinesh Wadhwani**  
**Last Updated: May 2026**
