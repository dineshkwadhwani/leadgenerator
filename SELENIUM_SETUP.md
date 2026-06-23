# SELENIUM SCRAPER - SETUP GUIDE

## 🚀 What This Does

Opens a **real Chrome browser** and:
- ✅ Searches Google Maps for schools
- ✅ Searches JustDial for contact info
- ✅ Searches Google websites
- ✅ Extracts phone, email, website, address
- ✅ **Bypasses all bot detection** (uses real browser)
- ✅ Saves progress (can resume if interrupted)

**Speed:** ~2-3 minutes per school = 15-20 hours for 445 schools

---

## 📋 SETUP STEPS

### Step 1: Install Selenium
```bash
pip install -r requirements_selenium.txt
```

Or individually:
```bash
pip install selenium
```

### Step 2: Download ChromeDriver

**Option A: Automatic (Easiest)**
```bash
pip install chromedriver-autoinstaller
```

**Option B: Manual (Recommended)**

1. Check your Chrome version:
   - Open Chrome
   - Menu → Help → About Google Chrome
   - Note your version (e.g., 120.0.1234.56)

2. Download matching ChromeDriver:
   - Go to: https://googlechromelabs.github.io/chrome-for-testing/ OR
   - Go to: https://chromedriver.chromium.org/
   - Download ChromeDriver matching your version

3. Place ChromeDriver in your project folder:
   ```
   MahaExam_LeadGenerator/
   ├── selenium_scraper.py
   ├── chromedriver.exe    ← (Windows)
   ├── chromedriver        ← (Mac/Linux)
   └── ... other files
   ```

**Option C: Add to PATH (Windows)**
1. Download ChromeDriver
2. Add to System PATH environment variable
3. Restart terminal

---

## 🚀 RUNNING THE SCRAPER

### Basic Command
```bash
python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx
```

### Output
```
PIMPRI_CHICHWAD_MNP_SELENIUM_LEADS.xlsx
```

### What Happens
1. Chrome browser opens (you'll see it working)
2. Searches for each school
3. Extracts data automatically
4. Saves progress after each school
5. Can resume if interrupted

---

## ⏱️ TIME ESTIMATES

| Schools | Time |
|---------|------|
| 10 | ~25 min |
| 50 | ~2-3 hours |
| 100 | ~4-5 hours |
| 445 | ~15-20 hours |

**Recommendation:** Run overnight or in batches

---

## 💡 TIPS

### Run in Headless Mode (Faster)
Open `selenium_scraper.py` and uncomment:
```python
# chrome_options.add_argument('--headless')
```

This hides the browser window and runs ~20% faster.

### Run in Batches
Split your file into multiple files and run separately:
```bash
python selenium_scraper.py batch1.xlsx
python selenium_scraper.py batch2.xlsx
```

Each will resume where it left off.

### Check Progress
The script creates:
- `selenium_progress.json` - Which schools processed
- `selenium_scraper_YYYYMMDD_HHMMSS.log` - Detailed log

---

## 🔧 TROUBLESHOOTING

### "ChromeDriver not found"
**Fix:**
```bash
pip install chromedriver-autoinstaller
```

Or download manually: https://chromedriver.chromium.org/

### "Chrome version mismatch"
**Fix:**
Make sure ChromeDriver version matches your Chrome version exactly (first 2-3 digits)

### "Port 9515 already in use"
**Fix:**
```bash
# Windows: kill process
taskkill /IM chromedriver.exe /F

# Mac/Linux: kill process
pkill chromedriver
```

### Browser takes too long to load
**Fix:**
Increase timeout in the script (search for `timeout=10` and change to `timeout=20`)

### Network timeout
**Fix:**
Increase delay between requests in script:
```python
time.sleep(1)  # Change to time.sleep(3)
```

---

## 📊 EXPECTED RESULTS

For 445 schools, expect:
- **Phones found:** 30-50% (150-225 schools)
- **Emails found:** 20-40% (90-180 schools)
- **Websites found:** 40-60% (180-270 schools)
- **Addresses found:** 10-30% (45-135 schools)

**Real browser = much better results than scraping!** ✅

---

## ✨ KEY ADVANTAGES

✅ **Real browser** - Bypasses all bot detection
✅ **Handles JavaScript** - Can load dynamic content
✅ **Progress tracking** - Resume if interrupted
✅ **Detailed logging** - See exactly what's happening
✅ **Multiple sources** - Tries Google, JustDial, etc.
✅ **Contact extraction** - Gets phone, email, website, address

---

## 🎯 READY TO USE!

1. Install ChromeDriver
2. Run: `python selenium_scraper.py PIMPRI_CHICHWAD_MNP.xlsx`
3. Let it work overnight
4. Get results in the morning! ✅

**Let's go!** 🚀
