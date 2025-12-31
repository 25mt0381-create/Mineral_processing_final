"""
Transform Commodity Export Data from Wide Format to Long Format

This script processes monthly commodity export Excel files and transforms them
from wide format (with multiple year columns) to long format with standardized
headers: HSCod, Commodity, Value, Country, Date, Type

Author: Auto-generated
Date: 2025-12-30
"""

import pandas as pd
import os
from pathlib import Path
import re
from datetime import datetime

# Configuration


BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR,"data","export")
LOOKUP_FILE = os.path.join(BASE_DIR, "data","hscodes","cleaned_HS_Codes_for_processing.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "transformed")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_hscode_lookup():
    """Load HS code to commodity name mapping"""
    print("Loading HS code lookup file...")
    df_lookup = pd.read_excel(LOOKUP_FILE)
    
    # Create mapping: HS Code -> Commodity Description
    lookup_dict = {}
    for _, row in df_lookup.iterrows():
        hscode = str(row['Cleaned ITC Code']).strip()
        description = row['Description']
        lookup_dict[hscode] = description
    
    print(f"Loaded {len(lookup_dict)} HS code mappings")
    return lookup_dict


def extract_year_columns(df_header_row):
    """
    Extract year column names from the header row.
    Excludes: S.No., Country, (R), %Growth, and similar metadata columns
    
    Returns: List of tuples (column_index, column_name, year, month)
    """
    year_columns = []
    
    for idx, col_name in enumerate(df_header_row):
        col_str = str(col_name).strip()
        
        # Skip non-year columns
        if col_str in ['S.No.', 'Country', '(R)', '%Growth', 'nan', '']:
            continue
        
        # Match patterns like "Apr-2017", "Apr-Apr2017", etc.
        # Extract the month and year
        match = re.search(r'([A-Za-z]+)-?([A-Za-z]*)?(\d{4})', col_str)
        if match:
            month = match.group(1)
            year = match.group(3)
            year_columns.append((idx, col_str, year, month))
    
    return year_columns


def process_monthly_file(filepath, hscode, commodity_name, data_type="Export"):
    """
    Process a single monthly Excel file and extract data in long format
    
    Returns: DataFrame with columns [HSCod, Commodity, Value, Country, Date, Type]
    """
    try:
        # Read the file without headers first
        df_raw = pd.read_excel(filepath, header=None)
        
        # Skip first 2 rows (metadata), row 2 contains the actual headers
        if len(df_raw) < 3:
            print(f"  Warning: File too short, skipping: {filepath}")
            return None
        
        header_row = df_raw.iloc[2]  # Row index 2 (3rd row)
        data_rows = df_raw.iloc[3:]  # Data starts from row 3 (4th row)
        
        # Extract year columns
        year_columns = extract_year_columns(header_row)
        
        if not year_columns:
            print(f"  Warning: No year columns found in {filepath}")
            return None
        
        # Find the Country column index
        country_col_idx = None
        for idx, col_name in enumerate(header_row):
            if str(col_name).strip().lower() == 'country':
                country_col_idx = idx
                break
        
        if country_col_idx is None:
            print(f"  Warning: Country column not found in {filepath}")
            return None
        
        # Transform to long format
        long_data = []
        
        for _, row in data_rows.iterrows():
            country = str(row.iloc[country_col_idx]).strip()
            
            # Skip empty or invalid countries
            if country in ['', 'nan', 'None']:
                continue
            
            # Extract values for each year column
            for col_idx, col_name, year, month in year_columns:
                value = row.iloc[col_idx]
                
                # Skip if value is empty or invalid
                if pd.isna(value) or value == '':
                    continue
                
                # Convert value to float if possible
                try:
                    value_float = float(value)
                except (ValueError, TypeError):
                    continue
                
                # Create date string in format "MMM-YYYY"
                date_str = f"{month}-{year}"
                
                # Add to long data
                long_data.append({
                    'HSCod': hscode,
                    'Commodity': commodity_name,
                    'Value': value_float,
                    'Country': country,
                    'Date': date_str,
                    'Type': data_type
                })
        
        if long_data:
            return pd.DataFrame(long_data)
        else:
            return None
            
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return None


def process_hscode_directory(hscode_dir, hscode, commodity_name):
    """
    Process all monthly files for a single HS code
    
    Returns: DataFrame with all data for this HS code
    """
    print(f"\nProcessing HS Code: {hscode} - {commodity_name}")
    
    all_data = []
    
    # Get all Excel files in the directory
    excel_files = sorted([f for f in os.listdir(hscode_dir) if f.endswith('.xlsx')])
    
    print(f"  Found {len(excel_files)} monthly files")
    
    for filename in excel_files:
        filepath = os.path.join(hscode_dir, filename)
        print(f"  Processing: {filename}")
        
        df_long = process_monthly_file(filepath, hscode, commodity_name)
        
        if df_long is not None and len(df_long) > 0:
            all_data.append(df_long)
            print(f"    Extracted {len(df_long)} records")
    
    if all_data:
        # Combine all data for this HS code
        df_combined = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates (same HSCod, Country, Date combination)
        df_combined = df_combined.drop_duplicates(subset=['HSCod', 'Country', 'Date'], keep='first')
        
        print(f"  Total records for {hscode}: {len(df_combined)}")
        return df_combined
    else:
        print(f"  No data extracted for {hscode}")
        return None


def main():
    """Main transformation process"""
    print("="*80)
    print("COMMODITY EXPORT DATA TRANSFORMATION")
    print("Wide Format → Long Format")
    print("="*80)
    
    # Load HS code lookup
    hscode_lookup = load_hscode_lookup()
    
    # Get all HS code directories
    hscode_dirs = [d for d in os.listdir(DATA_DIR) 
                   if os.path.isdir(os.path.join(DATA_DIR, d))]
    
    print(f"\nFound {len(hscode_dirs)} HS code directories")
    
    all_transformed_data = []
    processed_count = 0
    skipped_count = 0
    
    for hscode_dir_name in hscode_dirs:
        hscode = hscode_dir_name
        hscode_path = os.path.join(DATA_DIR, hscode_dir_name)
        
        # Get commodity name from lookup
        commodity_name = hscode_lookup.get(hscode, f"Unknown Commodity ({hscode})")
        
        # Process this HS code directory
        df_hscode = process_hscode_directory(hscode_path, hscode, commodity_name)
        
        if df_hscode is not None:
            all_transformed_data.append(df_hscode)
            processed_count += 1
            
            # Save individual HS code file
            
        else:
            skipped_count += 1
    
    # Combine all data and save consolidated file
    if all_transformed_data:
        print("\n" + "="*80)
        print("CREATING CONSOLIDATED FILE")
        print("="*80)
        
        df_consolidated = pd.concat(all_transformed_data, ignore_index=True)
        
        # Sort by HSCod, Date, Country
        df_consolidated = df_consolidated.sort_values(['HSCod', 'Date', 'Country'])
        
        consolidated_file = os.path.join(OUTPUT_DIR, "all_export_data.xlsx")
        df_consolidated.to_excel(consolidated_file, index=False)
        
        print(f"\nConsolidated file saved: {consolidated_file}")
        print(f"Total records: {len(df_consolidated)}")
        print(f"Unique HS Codes: {df_consolidated['HSCod'].nunique()}")
        print(f"Unique Countries: {df_consolidated['Country'].nunique()}")
        print(f"Date range: {df_consolidated['Date'].min()} to {df_consolidated['Date'].max()}")
    
    # Summary
    print("\n" + "="*80)
    print("TRANSFORMATION COMPLETE")
    print("="*80)
    print(f"Processed: {processed_count} HS codes")
    print(f"Skipped: {skipped_count} HS codes")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
