import pandas as pd
import os

curr_dir = os.getcwd()
base_file = os.path.join(curr_dir, "data", "transformed", "consolidated_all_hscodes.xlsx")
mapping_file = os.path.join(curr_dir, "data", "hscodes", "cleaned_HS_Codes_for_processing.xlsx")

try:
    # Load Main Data
    print(f"Loading base file: {base_file}")
    df = pd.read_excel(base_file)
    print(f"✓ Base file loaded: {df.shape}")
    
    df['Date_Parsed'] = pd.to_datetime(df['Date'], format='%b-%Y')
    print(f"✓ Date parsed")
    
    # --- CUTOFF FILTER (Sept 2025) ---
    df = df[df['Date_Parsed'] <= "2025-09-30"]
    print(f"✓ Date filtered: {df.shape}")
    
    # Load Mapping
    print(f"\nLoading mapping file: {mapping_file}")
    map_df = pd.read_excel(mapping_file)
    print(f"✓ Mapping file loaded: {map_df.shape}")
    print(f"  Columns before strip: {map_df.columns.tolist()}")
    
    map_df.columns = map_df.columns.str.strip()
    print(f"  Columns after strip: {map_df.columns.tolist()}")
    
    print(f"\nCreating HS code mapping...")
    print(f"  Checking for 'HSCode' column in mapping file...")
    if 'HSCode' in map_df.columns:
        print(f"  ✓ 'HSCode' column found")
    else:
        print(f"  ✗ 'HSCode' column NOT found!")
        print(f"  Available columns: {map_df.columns.tolist()}")
        raise KeyError("'HSCode'")
    
    if 'Element respective' in map_df.columns:
        print(f"  ✓ 'Element respective' column found")
    else:
        print(f"  ✗ 'Element respective' column NOT found!")
        print(f"  Available columns: {map_df.columns.tolist()}")
        raise KeyError("'Element respective'")
    
    hs_code_map = dict(zip(map_df['HSCode'], map_df['Element respective']))
    print(f"✓ Mapping created: {len(hs_code_map)} entries")
    
    # Apply Map
    print(f"\nApplying mapping to base data...")
    print(f"  Checking for 'HSCode' column in base file...")
    if 'HSCode' in df.columns:
        print(f"  ✓ 'HSCode' column found in base file")
    else:
        print(f"  ✗ 'HSCode' column NOT found in base file!")
        print(f"  Available columns: {df.columns.tolist()}")
        raise KeyError("'HSCode'")
    
    df['Mineral'] = df['HSCode'].map(hs_code_map)
    print(f"✓ Mapping applied")
    
    df = df[df['Mineral'].notna()]
    print(f"✓ Filtered to non-null minerals: {df.shape}")
    
    df = df.sort_values('Date_Parsed')
    print(f"✓ Sorted by date")
    
    print(f"\n✓✓✓ SUCCESS! Data loaded successfully ✓✓✓")
    print(f"\nFinal data shape: {df.shape}")
    print(f"Unique minerals: {df['Mineral'].nunique()}")
    print(f"Date range: {df['Date_Parsed'].min()} to {df['Date_Parsed'].max()}")
    
except Exception as e:
    print(f"\n✗✗✗ ERROR: {e} ✗✗✗")
    import traceback
    traceback.print_exc()
