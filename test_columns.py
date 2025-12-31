import pandas as pd
import os

curr_dir = os.getcwd()
mapping_file = os.path.join(curr_dir, "data", "hscodes", "cleaned_HS_Codes_for_processing.xlsx")

map_df = pd.read_excel(mapping_file)

print("Original columns:")
for i, col in enumerate(map_df.columns):
    print(f"{i}: {repr(col)}")

map_df.columns = map_df.columns.str.strip()

print("\nAfter strip:")
for i, col in enumerate(map_df.columns):
    print(f"{i}: {repr(col)}")

print("\nFirst few rows:")
print(map_df.head())
