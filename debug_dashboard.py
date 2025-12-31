import pandas as pd
import os

curr_dir = os.getcwd()
base_file = os.path.join(curr_dir, "data", "transformed", "consolidated_all_hscodes.xlsx")
mapping_file = os.path.join(curr_dir, "data", "hscodes", "cleaned_HS_Codes_for_processing.xlsx")

# Load Main Data
print("Loading base file...")
df = pd.read_excel(base_file)
print(f"Base file columns: {df.columns.tolist()}")
print(f"Base file shape: {df.shape}")
print(f"\nFirst few HSCode values from base file:")
print(df['HSCode'].head(10))
print(f"HSCode dtype: {df['HSCode'].dtype}")

# Load Mapping
print("\n" + "="*50)
print("Loading mapping file...")
map_df = pd.read_excel(mapping_file)
print(f"Mapping file columns (before strip): {map_df.columns.tolist()}")

map_df.columns = map_df.columns.str.strip()
print(f"Mapping file columns (after strip): {map_df.columns.tolist()}")
print(f"Mapping file shape: {map_df.shape}")
print(f"\nFirst few HSCode values from mapping file:")
print(map_df['HSCode'].head(10))
print(f"HSCode dtype: {map_df['HSCode'].dtype}")

# Try to create the mapping
print("\n" + "="*50)
print("Creating HS code mapping...")
try:
    hs_code_map = dict(zip(map_df['HSCode'], map_df['Element respective']))
    print(f"Mapping created successfully with {len(hs_code_map)} entries")
    print(f"\nSample mappings:")
    for i, (k, v) in enumerate(list(hs_code_map.items())[:5]):
        print(f"  {k} -> {v}")
    
    # Try to apply the mapping
    print("\n" + "="*50)
    print("Applying mapping to base data...")
    df['Mineral'] = df['HSCode'].map(hs_code_map)
    print(f"Mapping applied successfully")
    print(f"Non-null minerals: {df['Mineral'].notna().sum()}")
    print(f"Null minerals: {df['Mineral'].isna().sum()}")
    print(f"\nSample mapped data:")
    print(df[['HSCode', 'Mineral']].head(10))
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
