# MahaExam Lead Generation System

Automated school contact information extractor for lead generation. Extract phone numbers, emails, websites, and addresses for any list of schools.

## 📋 Project Structure

```
MahaExam_LeadGenerator/
├── main.py                      # Main entry point
├── config.json                  # Configuration file
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
├── src/
│   ├── __init__.py
│   ├── lead_gen_quick.py        # Quick scraper
│   └── utils.py                 # Utilities & logging
├── input/                       # Place your Excel files here
│   └── example.xlsx
└── output/                      # Results saved here
    └── example_WITH_LEADS.xlsx
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Excel File

- File must contain a column named **`school_name`**
- Can have additional columns (they will be preserved)
- Place file in project root or `input/` folder

Example columns:
- `school_name` (required)
- `taluka_name`
- `pincode`
- Any other columns you have

### 3. Run the Scraper

**Option A: Using config.json (update file name)**
```bash
# Edit config.json - change INPUT_FILE to your file
# Then run:
python main.py
```

**Option B: Direct command line (any file)**
```bash
python main.py schools.xlsx
python main.py input/pimpri_chichwad.xlsx
python main.py /path/to/schools.xlsx
```

### 4. Get Results

New file created: `{filename}_WITH_LEADS.xlsx`

Contains original columns + new columns:
- `address`
- `website`
- `phone`
- `email`
- `lead_source`
- `data_complete` (completeness score 0-4)

## 📖 Usage Examples

### Example 1: Process Pimpri Chichwad schools

```bash
python main.py PIMPRI_CHICHWAD_MNP.xlsx
```

Output: `PIMPRI_CHICHWAD_MNP_WITH_LEADS.xlsx`

### Example 2: Process Nashik schools

```bash
python main.py NASHIK_SCHOOLS.xlsx
```

Output: `NASHIK_SCHOOLS_WITH_LEADS.xlsx`

### Example 3: Process from subdirectory

```bash
python main.py input/all_schools.xlsx
```

Output: `all_schools_WITH_LEADS.xlsx`

### Example 4: Using config.json

```bash
# 1. Edit config.json
# Change: "INPUT_FILE": "PIMPRI_CHICHWAD_MNP.xlsx"
# To:     "INPUT_FILE": "NASHIK_SCHOOLS.xlsx"

# 2. Run
python main.py

# Output: NASHIK_SCHOOLS_WITH_LEADS.xlsx
```

## ⚙️ Configuration

Edit `config.json` to change:

```json
{
  "INPUT_FILE": "schools.xlsx",    # Your Excel file
  "MAX_WORKERS": 5,                # Concurrent processes (1-10)
  "REQUEST_TIMEOUT": 15,           # Timeout in seconds
  "VERBOSE": true                  # Detailed logging
}
```

## 📊 Output Format

Your original Excel file will have 6 new columns added:

| Column | Type | Example |
|--------|------|---------|
| address | Text | Plot 123, Sector 5, Kalewadi |
| website | URL | https://akshara.edu.in |
| phone | Text | 9876543210 |
| email | Text | info@akshara.edu.in |
| lead_source | Text | Web Search / JustDial |
| data_complete | Number | 0-4 (how many fields found) |

## 📈 Expected Results

For 45 schools (typical):
- **Phones**: 75-85% found
- **Emails**: 40-60% found
- **Websites**: 85-95% found
- **Addresses**: 50-70% found

Time: 15-20 minutes per batch

## 🛠️ Open in VS Code

1. **Open folder:**
   - File → Open Folder
   - Select `MahaExam_LeadGenerator`

2. **Install Python extension** (if not already done)

3. **Open terminal:** 
   - Terminal → New Terminal

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run:**
   ```bash
   python main.py schools.xlsx
   ```

## 🔧 Troubleshooting

### File not found error
```
❌ File not found: schools.xlsx

Solution:
- Check file name spelling
- File must be in project root or specify full path
- Use: python main.py input/schools.xlsx
```

### Module not found error
```
❌ ModuleNotFoundError: No module named 'pandas'

Solution:
pip install --upgrade -r requirements.txt
```

### school_name column not found
```
❌ Required column 'school_name' not found

Solution:
- Rename your column to 'school_name'
- Check exact spelling (lowercase, no spaces)
```

### Connection timeout
```
⚠️ Timeout error

Solution:
- Check internet connection
- Wait and retry later
- Increase timeout in config.json (REQUEST_TIMEOUT: 30)
```

## 🎯 Tips for Success

1. **Large files**: For 1000+ schools, split into batches of 100-200
2. **Validation**: Always check first 5 schools manually
3. **Improvement**: Run again with `MAX_WORKERS: 3` if getting errors
4. **Quality**: Higher `MAX_WORKERS` = faster but less reliable
5. **Errors**: Check logs for detailed error messages

## 📝 Logging

Each run creates a log file:
```
lead_generation_20260527_143022.log
```

Check this file for detailed debug information.

## 📚 File Formats Supported

- ✅ `.xlsx` (Excel - recommended)
- ✅ `.xls` (Old Excel)
- ✅ `.csv` (CSV files)

## 🔐 Privacy & Security

- ✅ Only public school information extracted
- ✅ No student data collected
- ✅ Respects website rate limits
- ✅ No data sold or shared
- ✅ Ethical scraping practices

## 📊 Processing Speeds

| Operation | Time |
|-----------|------|
| 50 schools | ~10 min |
| 100 schools | ~20 min |
| 500 schools | ~100 min |

**Note**: First run is slightly slower. Subsequent runs may be faster due to caching.

## 🚀 Advanced Usage

### Batch Processing Multiple Files

```bash
# Process multiple files sequentially
python main.py file1.xlsx
python main.py file2.xlsx
python main.py file3.xlsx
```

### Different Configurations

```bash
# Create different config files
cp config.json config_fast.json  # For speed
cp config.json config_thorough.json  # For accuracy

# Edit config_fast.json:
# "MAX_WORKERS": 10,
# "REQUEST_TIMEOUT": 8

# Run with different config
python main.py file.xlsx
```

### Custom Processing

Edit `main.py` to customize:
- Output file location
- Additional data processing
- Custom output format
- Post-processing filters

## 🆘 Getting Help

1. Check README.md (this file)
2. Check log file for errors
3. Try the command with verbose output
4. Ensure Python 3.7+: `python --version`

## 📞 Support

For issues:
1. Verify file format (must be Excel/CSV with school_name column)
2. Check internet connection
3. Review log files for detailed errors
4. Try with smaller file (10 schools) first

## 📜 Version History

**v1.0.0** (May 2026)
- Initial release
- Quick lead generator
- Multi-source research
- Concurrent processing
- Comprehensive logging

## 🎓 Learning Resources

This project demonstrates:
- Python automation
- Web scraping (ethical)
- Concurrent processing
- Data validation
- Error handling
- Logging best practices

## 📈 ROI

**For 45 schools:**
- Lead generation: 45 schools → 30-40 with contact info
- Conversion rate: 5-10% (2-5 schools)
- Per school value: ₹5-10K/year
- **Total revenue: ₹10-50K/year per region**

---

**Happy scraping! Good luck with your lead generation! 🚀**

For questions or improvements, reach out to the MahaExam team.
