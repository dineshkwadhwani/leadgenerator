# VS Code Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Open in VS Code

```
1. Open VS Code
2. File → Open Folder
3. Select: MahaExam_LeadGenerator
```

### Step 2: Install Dependencies

```
1. Open Terminal: Ctrl+` (or View → Terminal)
2. Run: pip install -r requirements.txt
3. Wait for installation to complete
```

### Step 3: Run the Scraper

#### Option A: Using Terminal
```bash
# Update config.json file path, then:
python main.py

# Or specify file:
python main.py PIMPRI_CHICHWAD_MNP.xlsx
python main.py input/schools.xlsx
```

#### Option B: Using VS Code Debug
```
1. Click on "Run and Debug" (left sidebar)
2. Choose configuration:
   - "Run with config.json" (uses config.json setting)
   - "Run with specific file" (specify file as argument)
3. Press F5 or click Play button
```

## 📁 File Structure

After opening in VS Code, you'll see:

```
MahaExam_LeadGenerator/
├── .vscode/              ← VS Code settings
├── src/                  ← Python source code
├── input/                ← Place Excel files here
├── output/               ← Results saved here
├── main.py              ← Main entry point
├── config.json          ← Configuration
├── requirements.txt     ← Dependencies
└── README.md            ← Full documentation
```

## 🔧 Configuration Methods

### Method 1: Edit config.json (Recommended)
```json
{
  "INPUT_FILE": "PIMPRI_CHICHWAD_MNP.xlsx",
  ...
}
```
Then run: `python main.py`

### Method 2: Command Line Argument
```bash
python main.py schools.xlsx
python main.py input/pimpri_chichwad.xlsx
python main.py /full/path/to/schools.xlsx
```

### Method 3: Place in input/ folder
```bash
# Put file in input/ folder, then:
python main.py input/schools.xlsx
```

## 📊 Running Examples

### Example 1: Process Pimpri Chichwad
```bash
python main.py PIMPRI_CHICHWAD_MNP.xlsx
```

### Example 2: Process from input folder
```bash
python main.py input/nashik_schools.xlsx
```

### Example 3: Using config
```bash
# Edit config.json:
# "INPUT_FILE": "NASHIK_SCHOOLS.xlsx"
# Then run:
python main.py
```

### Example 4: Batch processing
```bash
python main.py file1.xlsx
python main.py file2.xlsx
python main.py file3.xlsx
```

## 🖥️ VS Code Features Used

✅ **Integrated Terminal**
- Open: Ctrl+`
- Run Python directly

✅ **Debug Mode**
- F5 to run with debugging
- Set breakpoints
- Watch variables

✅ **Explorer View**
- See all project files
- Right-click to create files
- Drag-drop files

✅ **Problems Panel**
- Shows Python errors
- Linting suggestions

## 🆘 Troubleshooting in VS Code

### Python not found
```
Error: python not found in PATH

Solution:
1. Install Python from python.org
2. Check: python --version
3. Restart VS Code
```

### Module not found
```
Error: ModuleNotFoundError: No module named 'pandas'

Solution:
1. Open Terminal
2. Run: pip install -r requirements.txt
3. Wait for completion
4. Try again
```

### File not found
```
Error: File not found: PIMPRI_CHICHWAD_MNP.xlsx

Solution:
1. Check file name exactly
2. Put file in project root or input/ folder
3. Use full path if in different directory
```

## 💡 VS Code Tips

### Keyboard Shortcuts
- `Ctrl+``: Open Terminal
- `F5`: Run with debugging
- `Ctrl+F`: Find in file
- `Ctrl+H`: Find and replace
- `Ctrl+B`: Toggle sidebar
- `Ctrl+K Ctrl+0`: Fold all
- `Ctrl+Shift+P`: Command palette

### Useful Extensions
- Python (Microsoft)
- Pylance (Microsoft)
- Better Comments
- Excel Viewer

### Running in Terminal vs Debug
- **Terminal**: Faster, less overhead
- **Debug**: Can set breakpoints, watch variables

## 📝 Example Workflow

```
1. Open Terminal (Ctrl+`)
2. Check requirements installed:
   pip list | grep pandas

3. Place Excel file in input/ folder

4. Run scraper:
   python main.py input/schools.xlsx

5. Check output/ folder for results

6. Open results in Excel:
   Double-click: schools_WITH_LEADS.xlsx
```

## 🎯 Next Steps After Running

1. ✅ Results saved to `schools_WITH_LEADS.xlsx`
2. ✅ Open file in Excel or Sheets
3. ✅ Review phone/email/website columns
4. ✅ Sort by `data_complete` score
5. ✅ Start contacting schools!

## 📊 Batch Processing

Process multiple files:
```bash
python main.py input/file1.xlsx
python main.py input/file2.xlsx
python main.py input/file3.xlsx
```

Results will be saved as:
- `file1_WITH_LEADS.xlsx`
- `file2_WITH_LEADS.xlsx`
- `file3_WITH_LEADS.xlsx`

## 🚀 You're Ready!

Everything is set up and ready to use. Just:

1. **Open the folder** in VS Code
2. **Install dependencies** (one time: `pip install -r requirements.txt`)
3. **Run**: `python main.py your_file.xlsx`
4. **Get results** in seconds!

---

**Questions? Check README.md for complete documentation.**

Happy lead generation! 🎉
