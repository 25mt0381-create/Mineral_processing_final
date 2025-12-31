import pandas as pd
import os

# Mimic Streamlit's caching behavior
def load_data():
    curr_dir = os.getcwd()
    base_file = os.path.join(curr_dir, "data", "transformed", "consolidated_all_hscodes.xlsx")
    mapping_file = os.path.join(curr_dir, "data", "hscodes", "cleaned_HS_Codes_for_processing.xlsx")
    
    try:
        # Load Main Data
        print(base_file)
        df = pd.read_excel(base_file)
        df['Date_Parsed'] = pd.to_datetime(df['Date'], format='%b-%Y')
        print("failed base file load")  # This is line 37 - misleading message!
        
        # --- CUTOFF FILTER (Sept 2025) ---
        df = df[df['Date_Parsed'] <= "2025-09-30"]
        
        # Load Mapping
        map_df = pd.read_excel(mapping_file)
        map_df.columns = map_df.columns.str.strip()
        
        print(f"\nMapping file columns after strip:")
        for i, col in enumerate(map_df.columns):
            print(f"  {i}: '{col}'")
        
        print(f"\nChecking for required columns...")
        if 'HSCode' not in map_df.columns:
            print(f"ERROR: 'HSCode' column not found!")
            print(f"Available columns: {list(map_df.columns)}")
            raise KeyError("'HSCode'")
        
        if 'Element respective' not in map_df.columns:
            print(f"ERROR: 'Element respective' column not found!")
            print(f"Available columns: {list(map_df.columns)}")
            raise KeyError("'Element respective'")
        
        hs_code_map = dict(zip(map_df['HSCode'], map_df['Element respective']))
        
        # Apply Map
        df['Mineral'] = df['HSCode'].map(hs_code_map)
        df = df[df['Mineral'].notna()]
        
        return df.sort_values('Date_Parsed')
    except Exception as e:
        print(f"Error loading files: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# Call the function
print("=" * 60)
print("TESTING LOAD_DATA FUNCTION")
print("=" * 60)
df = load_data()

if not df.empty:
    print(f"\n✓ SUCCESS!")
    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Unique minerals: {df['Mineral'].nunique()}")
else:
    print(f"\n✗ FAILED - Empty DataFrame returned")
