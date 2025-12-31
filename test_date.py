import pandas as pd
import os

curr_dir = os.getcwd()
base_file = os.path.join(curr_dir, "data", "transformed", "consolidated_all_hscodes.xlsx")

# Load Main Data
print("Loading base file...")
df = pd.read_excel(base_file)

print(f"\nColumn names (repr):")
for col in df.columns:
    print(f"  {repr(col)}")

print(f"\nTrying to parse Date column...")
try:
    df['Date_Parsed'] = pd.to_datetime(df['Date'], format='%b-%Y')
    print("SUCCESS: Date parsing worked")
    print(f"Sample dates: {df['Date_Parsed'].head()}")
except Exception as e:
    print(f"ERROR: {e}")
    print(f"\nSample Date values:")
    print(df['Date'].head(20))
