# Project Structure Guide

## 📁 Complete Project Layout

```
MahaExam_LeadGenerator/
│
├── 📄 main.py                      # Entry point - Run this!
├── 📄 README.md                    # Full documentation (READ THIS FIRST)
├── 📄 VSCODE_GUIDE.md             # VS Code quick start
├── 📄 config.json                 # Configuration file (edit for your needs)
├── 📄 requirements.txt            # Python dependencies
├── 📄 .gitignore                  # Git ignore rules
│
├── 🗂️  src/                        # Source code
│   ├── __init__.py               # Package marker
│   ├── lead_gen_quick.py         # Quick scraper (main logic)
│   └── utils.py                  # Utilities & logging
│
├── 🗂️  .vscode/                   # VS Code configuration
│   ├── launch.json               # Debug configurations
│   └── settings.json             # Editor settings
│
├── 🗂️  input/                     # Place your Excel files here
│   └── (your_file.xlsx)
│
└── 🗂️  output/                    # Results saved here
    └── (your_file_WITH_LEADS.xlsx)
```

## 📝 File Descriptions

### Root Files

| File | Purpose | Edit? |
|------|---------|-------|
| `main.py` | Main entry point | No |
| `README.md` | Full documentation | No |
| `VSCODE_GUIDE.md` | VS Code setup | No |
| `config.json` | Configuration | **Yes** |
| `requirements.txt` | Dependencies | No |
| `.gitignore` | Git rules | No |

### src/ Folder

| File | Purpose |
|------|---------|
| `__init__.py` | Makes src a Python package |
| `lead_gen_quick.py` | Main scraping logic |
| `utils.py` | Logging and utilities |

### .vscode/ Folder

| File | Purpose |
|------|---------|
| `launch.json` | Debug launch configurations |
| `settings.json` | VS Code editor settings |

### Folders for Data

| Folder | Purpose |
|--------|---------|
| `input/` | Place your Excel files here |
| `output/` | Results automatically saved here |

## 🚀 How to Use Each File

### 1. README.md
- **When**: First time setup
- **What**: Complete documentation
- **How**: Open and read in VS Code

### 2. VSCODE_GUIDE.md
- **When**: Setting up in VS Code
- **What**: VS Code specific instructions
- **How**: Open and follow steps

### 3. config.json
- **When**: Want to change default settings
- **What**: Configuration options
- **How**: Edit with VS Code, change INPUT_FILE value

### 4. main.py
- **When**: Ready to run scraper
- **What**: Main executable
- **How**: `python main.py` or `python main.py file.xlsx`

### 5. requirements.txt
- **When**: First setup
- **What**: All Python libraries needed
- **How**: `pip install -r requirements.txt`

### 6. src/lead_gen_quick.py
- **When**: Want to understand code
- **What**: Scraping logic
- **How**: Read code, modify if needed

## 💻 Usage Flows

### Flow 1: Using config.json (Recommended for fixed file)

```
1. Edit config.json
   Change: "INPUT_FILE": "PIMPRI_CHICHWAD_MNP.xlsx"
   
2. Run: python main.py
   
3. Results: PIMPRI_CHICHWAD_MNP_WITH_LEADS.xlsx
```

### Flow 2: Command line argument (For flexibility)

```
1. Run: python main.py schools.xlsx
   
2. Results: schools_WITH_LEADS.xlsx
```

### Flow 3: Using input/ folder

```
1. Put file in: input/schools.xlsx

2. Run: python main.py input/schools.xlsx
   
3. Results: schools_WITH_LEADS.xlsx
```

### Flow 4: VS Code Debug

```
1. Open main.py
2. Click "Run and Debug" sidebar
3. Choose configuration
4. Press F5
5. Monitor in terminal
```

## 🔧 Customization

### Change Default File
Edit `config.json`:
```json
{
  "INPUT_FILE": "YOUR_FILE.xlsx"
}
```

### Change Performance
Edit `config.json`:
```json
{
  "MAX_WORKERS": 3   # Slower but more reliable
  "MAX_WORKERS": 10  # Faster but less reliable
}
```

### Change Timeout
Edit `config.json`:
```json
{
  "REQUEST_TIMEOUT": 30  # More time for slow servers
}
```

## 📊 Input/Output

### Input Requirements
- Excel file (.xlsx, .xls) or CSV
- Must have column named: `school_name`
- Can have other columns (preserved in output)

### Output File
- Name: `{original_name}_WITH_LEADS.xlsx`
- Location: Same folder as input file
- Contains: All original columns + 6 new columns

### New Columns Added
- `address` - School address
- `website` - School website
- `phone` - Contact phone number
- `email` - Contact email
- `lead_source` - Where data came from
- `data_complete` - Completeness score (0-4)

## 🎯 When to Edit Each File

### config.json
- ✅ Change input file
- ✅ Change performance settings
- ✅ Change timeout values

### main.py
- ❌ Don't edit (unless you know Python)
- Can read to understand flow

### src/lead_gen_quick.py
- ❌ Don't edit normally
- Can modify search logic if needed

### requirements.txt
- ❌ Don't edit normally
- Only if you need different versions

## 🚀 Running in VS Code

### Terminal Method
```
1. Ctrl+` (open terminal)
2. python main.py schools.xlsx
3. Enter
```

### Debug Method
```
1. F5 (or click Run button)
2. Choose configuration
3. Monitor output
```

## 📈 Expected Output

For 45 schools, expect:
- ✅ 35-40 phone numbers (78-89%)
- ✅ 20-25 emails (44-56%)
- ✅ 40-45 websites (89-100%)
- ⏱️ Time: 15-20 minutes

## 🆘 Quick Troubleshooting

| Problem | File to Check | Solution |
|---------|---------------|----------|
| File not found | config.json | Check INPUT_FILE path |
| Module error | requirements.txt | Run: pip install -r requirements.txt |
| slow | config.json | Increase MAX_WORKERS |
| No results | main.py | Check school_name column exists |
| VS Code issue | VSCODE_GUIDE.md | Follow VS Code setup guide |

## 📚 Reading Order

1. **README.md** - Understand what it does
2. **VSCODE_GUIDE.md** - Set up VS Code
3. **config.json** - Configure for your files
4. **main.py** - Run the scraper
5. **Check output** - Review results

## 🎁 Bonus Files

All these files are included:
- ✅ Example config
- ✅ VS Code settings
- ✅ Git configuration
- ✅ Complete documentation
- ✅ Debug configurations

## 🚀 You're All Set!

Everything needed is here. Just:
1. Open folder in VS Code
2. Install dependencies
3. Run: `python main.py your_file.xlsx`
4. Get results!

---

Questions? See **README.md** for complete documentation.

