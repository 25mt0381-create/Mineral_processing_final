"""
Merge All Transformed Excel Files into One Consolidated File

This script reads all individual HS code transformed Excel files from the
Transformed directory and merges them into a single consolidated Excel file.

Author: Auto-generated
Date: 2025-12-30
"""

import pandas as pd
import os
from pathlib import Path

# Configuration
BASE_DIR = os.getcwd()
TRANSFORMED_DIR = os.path.join(BASE_DIR, "data", "transformed")
OUTPUT_FILE = os.path.join(TRANSFORMED_DIR, "consolidated_all_hscodes.xlsx")

def merge_excel_files():
    """Merge all transformed Excel files into one consolidated file"""
    
    print("="*80)
    print("MERGING TRANSFORMED EXCEL FILES")
    print("="*80)
    print(f"\nSource directory: {TRANSFORMED_DIR}")
    
    # Get all Excel files except the consolidated one
    excel_files = [f for f in os.listdir(TRANSFORMED_DIR) 
                   if f.endswith('.xlsx') and 'consolidated' not in f.lower()]
    
    if not excel_files:
        print("\n❌ No Excel files found to merge!")
        return
    
    print(f"\nFound {len(excel_files)} Excel files to merge")
    
    all_dataframes = []
    total_records = 0
    processed_count = 0
    error_count = 0
    
    # Read each Excel file
    for idx, filename in enumerate(excel_files, 1):
        filepath = os.path.join(TRANSFORMED_DIR, filename)
        
        try:
            print(f"\n[{idx}/{len(excel_files)}] Reading: {filename}")
            df = pd.read_excel(filepath)
            
            # Verify expected columns exist
            expected_columns = ['HSCod', 'Commodity', 'Value', 'Country', 'Date', 'Type']
            if not all(col in df.columns for col in expected_columns):
                print(f"  ⚠️  Warning: Missing expected columns, skipping...")
                error_count += 1
                continue
            
            records = len(df)
            print(f"  ✓ Loaded {records:,} records")
            
            all_dataframes.append(df)
            total_records += records
            processed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error reading {filename}: {e}")
            error_count += 1
            continue
    
    if not all_dataframes:
        print("\n❌ No valid data to merge!")
        return
    
    # Merge all dataframes
    print("\n" + "="*80)
    print("CONSOLIDATING DATA")
    print("="*80)
    
    df_consolidated = pd.concat(all_dataframes, ignore_index=True)
    
    # Remove duplicates based on HSCod, Country, Date
    print(f"\nTotal records before deduplication: {len(df_consolidated):,}")
    df_consolidated = df_consolidated.drop_duplicates(
        subset=['HSCod', 'Country', 'Date'], 
        keep='first'
    )
    print(f"Total records after deduplication: {len(df_consolidated):,}")
    
    # Sort by HSCod, Date, Country
    print("\nSorting data...")
    df_consolidated = df_consolidated.sort_values(['HSCod', 'Date', 'Country'])
    
    # Save consolidated file
    print(f"\nSaving consolidated file...")
    df_consolidated.to_excel(OUTPUT_FILE, index=False)
    
    # Summary statistics
    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"\n📊 Summary Statistics:")
    print(f"  Files processed: {processed_count}")
    print(f"  Files with errors: {error_count}")
    print(f"  Total records: {len(df_consolidated):,}")
    print(f"  Unique HS Codes: {df_consolidated['HSCod'].nunique()}")
    print(f"  Unique Countries: {df_consolidated['Country'].nunique()}")
    print(f"  Unique Dates: {df_consolidated['Date'].nunique()}")
    print(f"  Date range: {df_consolidated['Date'].min()} to {df_consolidated['Date'].max()}")
    print(f"  Value range: ${df_consolidated['Value'].min():.2f}M to ${df_consolidated['Value'].max():.2f}M")
    
    print(f"\n✅ Consolidated file saved to:")
    print(f"   {OUTPUT_FILE}")
    
    # Show breakdown by HS Code
    print(f"\n📈 Records per HS Code:")
    hscode_counts = df_consolidated['HSCod'].value_counts().sort_index()
    for hscode, count in hscode_counts.items():
        commodity = df_consolidated[df_consolidated['HSCod'] == hscode]['Commodity'].iloc[0]
        print(f"  {hscode}: {count:,} records - {commodity}")


if __name__ == "__main__":
    merge_excel_files()
