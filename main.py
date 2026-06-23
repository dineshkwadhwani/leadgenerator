"""
MAHAEXAM LEAD GENERATION - Main Entry Point
Run with any Excel file containing school_name column

Usage:
    python main.py                          (uses config.json file setting)
    python main.py schools.xlsx             (specify file as argument)
    python main.py data/schools.xlsx        (from subdirectory)
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lead_gen_quick import process_schools_concurrent
from utils import logger, setup_logging

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / 'config.json'
    
    default_config = {
        'INPUT_FILE': 'PIMPRI_CHICHWAD_MNP.xlsx',
        'MAX_WORKERS': 5,
        'REQUEST_TIMEOUT': 15,
        'VERBOSE': True
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config.json: {str(e)}")
            return default_config
    
    return default_config

def get_input_file():
    """Get input file from command line or config"""
    
    # Check command line argument first
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        logger.info(f"Using input file from command line: {input_file}")
        return input_file
    
    # Check config file
    config = load_config()
    input_file = config.get('INPUT_FILE', 'PIMPRI_CHICHWAD_MNP.xlsx')
    logger.info(f"Using input file from config: {input_file}")
    return input_file

def validate_input_file(input_file):
    """Validate that input file exists and has school_name column"""
    
    # Check if file exists
    if not os.path.exists(input_file):
        logger.error(f"❌ File not found: {input_file}")
        logger.info("\nUsage:")
        logger.info("  python main.py                    (uses config.json)")
        logger.info("  python main.py schools.xlsx       (specify file)")
        logger.info("  python main.py data/schools.xlsx  (from subdirectory)")
        return False
    
    # Check if it's an Excel file
    if not input_file.lower().endswith(('.xlsx', '.xls', '.csv')):
        logger.error(f"❌ File must be Excel (.xlsx/.xls) or CSV (.csv): {input_file}")
        return False
    
    # Try to read and check columns
    try:
        df = pd.read_excel(input_file) if input_file.endswith(('.xlsx', '.xls')) else pd.read_csv(input_file)
        
        if 'school_name' not in df.columns:
            logger.error(f"❌ Required column 'school_name' not found in {input_file}")
            logger.info(f"\nAvailable columns: {', '.join(df.columns)}")
            logger.info("\nPlease rename a column to 'school_name' or edit config.json")
            return False
        
        logger.info(f"✓ File valid: {len(df)} schools found")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reading file: {str(e)}")
        return False

def generate_output_filename(input_file):
    """Generate output filename based on input"""
    base = Path(input_file).stem
    ext = Path(input_file).suffix
    return f"{base}_WITH_LEADS{ext}"

def main():
    """Main execution"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║       MAHAEXAM LEAD GENERATION SYSTEM                              ║
║          School Contact Information Extractor                      ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Get input file
    input_file = get_input_file()
    
    # Validate
    if not validate_input_file(input_file):
        sys.exit(1)
    
    # Generate output filename
    output_file = generate_output_filename(input_file)
    
    logger.info(f"Input file:  {input_file}")
    logger.info(f"Output file: {output_file}")
    
    # Load data
    logger.info("\nLoading data...")
    try:
        df = pd.read_excel(input_file) if input_file.endswith(('.xlsx', '.xls')) else pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        sys.exit(1)
    
    total_schools = len(df)
    logger.info(f"✓ Loaded {total_schools} schools")
    
    # Get unique school names
    schools_data = []
    for idx, row in df.iterrows():
        school_name = row['school_name']
        gmaps_url = row.get('gmaps link', '') if 'gmaps link' in df.columns else ''
        pincode = row.get('pincode', None) if 'pincode' in df.columns else None
        schools_data.append((school_name, gmaps_url, pincode))
    
    # Process schools
    logger.info(f"\nStarting lead extraction...")
    print("\n" + "="*70)
    
    leads = process_schools_concurrent(schools_data)
    
    print("="*70 + "\n")
    
    # Add results to dataframe
    df['address'] = [lead['address'] if 'address' in lead else '' for lead in leads]
    df['website'] = [lead['website'] if 'website' in lead else '' for lead in leads]
    df['phone'] = [lead['phone'] if 'phone' in lead else '' for lead in leads]
    df['email'] = [lead['email'] if 'email' in lead else '' for lead in leads]
    df['lead_source'] = [lead.get('source', 'Not Found') for lead in leads]
    
    # Calculate completeness
    df['data_complete'] = (
        (df['address'] != '').astype(int) +
        (df['website'] != '').astype(int) +
        (df['phone'] != '').astype(int) +
        (df['email'] != '').astype(int)
    )
    
    # Save results
    logger.info(f"Saving results to {output_file}...")
    try:
        df.to_excel(output_file, index=False, engine='openpyxl')
        logger.info(f"✓ Results saved successfully!")
    except Exception as e:
        try:
            csv_file = output_file.replace('.xlsx', '.csv')
            df.to_csv(csv_file, index=False)
            logger.info(f"✓ Results saved as CSV: {csv_file}")
        except Exception as e2:
            logger.error(f"Error saving results: {str(e2)}")
            sys.exit(1)
    
    # Print summary
    print("\n" + "="*70)
    print("LEAD GENERATION SUMMARY")
    print("="*70)
    print(f"Total Schools: {len(df)}")
    print(f"Phones Found: {(df['phone'] != '').sum()}/{len(df)} ({(df['phone'] != '').sum()/len(df)*100:.1f}%)")
    print(f"Emails Found: {(df['email'] != '').sum()}/{len(df)} ({(df['email'] != '').sum()/len(df)*100:.1f}%)")
    print(f"Websites Found: {(df['website'] != '').sum()}/{len(df)} ({(df['website'] != '').sum()/len(df)*100:.1f}%)")
    
    print("\n✓ Process complete!")
    print(f"✓ Output file: {output_file}")
    print("="*70)

if __name__ == "__main__":
    setup_logging()
    main()
