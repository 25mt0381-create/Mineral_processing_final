
import os
import time
import shutil
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import glob

# --- Configuration ---
# Base directory for commodity-wise import data
current_dir = os.getcwd()
BASE_DOWNLOAD_DIR = os.path.join(current_dir,"data","import")

# Temporary download folder (browser downloads here first)
TEMP_DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, "temp_downloads")

# HS Codes file path
HSCODES_FILE = os.path.join(current_dir,"data","hscodes","hscodes.txt")

# Ensure directories exist
if not os.path.exists(TEMP_DOWNLOAD_DIR):
    os.makedirs(TEMP_DOWNLOAD_DIR)

def setup_driver():
    """Sets up the Chrome WebDriver with specific download preferences."""
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": TEMP_DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless=new")
    
    # Setup driver (this will automatically download/update the driver)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Enable downloads in headless mode explicitly
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": TEMP_DOWNLOAD_DIR
    })

    return driver

def get_latest_file(directory):
    """Returns the path of the latest file in the directory."""
    files = glob.glob(os.path.join(directory, "*"))
    files = [f for f in files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
    if not files:
        return None
    return max(files, key=os.path.getctime)

def is_hscode_completed(hscode_dir, start_year, end_year):
    """
    Checks if all expected monthly files for an HS code exist from start_year to end_year.
    Returns True if the HS code is fully downloaded, False otherwise.
    """
    if not os.path.exists(hscode_dir):
        return False

    now = datetime.datetime.now()
    
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Stop if future date
            if year == now.year and month > now.month:
                break
            
            month_name = datetime.date(year, month, 1).strftime('%B')
            target_filename = f"{month_name}_{year}.xlsx"
            target_path = os.path.join(hscode_dir, target_filename)
            
            if not os.path.exists(target_path):
                return False
                
    return True

def read_hscodes_from_file(filepath):
    """Reads HS codes from a text file (one per line)."""
    hscodes = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                code = line.strip()
                if code and not code.startswith('#'):  # Skip empty lines and comments
                    hscodes.append(code)
        print(f"Loaded {len(hscodes)} HS codes from file.")
        return hscodes
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return []

def scrape_commodity_data(hscodes):
    """
    Scrapes commodity-wise import data for the given list of HS codes.
    
    Args:
        hscodes: List of 8-digit HS codes to scrape
    """
    driver = setup_driver()
    url = "https://tradestat.commerce.gov.in/meidb/commodity_wise_all_countries_import"
    
    start_year = 2018
    now = datetime.datetime.now()
    current_year = now.year

    try:
        total_hscodes = len(hscodes)
        print(f"Processing {total_hscodes} HS codes...\n")
        
        # Iterate through HS Codes
        for idx, hscode in enumerate(hscodes, 1):
            print(f"--- Processing HS Code {idx}/{total_hscodes}: {hscode} ---")
            
            # Create HS Code Directory
            hscode_dir = os.path.join(BASE_DOWNLOAD_DIR, str(hscode))
            
            if not os.path.exists(hscode_dir):
                os.makedirs(hscode_dir)
            
            # Check if HS code is already completed
            if is_hscode_completed(hscode_dir, start_year, current_year):
                print(f"  Skipping {hscode} - All files already downloaded.\n")
                continue
            
            # Iterate through Years
            for year in range(start_year, current_year + 1):
                # Iterate through Months
                for month in range(1, 13):
                    
                    # Stop if future date
                    if year == now.year and month > now.month:
                        break
                    
                    # Target Filename: {MonthName}_{Year}.xlsx
                    month_name = datetime.date(year, month, 1).strftime('%B')
                    target_filename = f"{month_name}_{year}.xlsx"
                    target_path = os.path.join(hscode_dir, target_filename)
                    
                    # Skip if file already exists (Resumability logic)
                    if os.path.exists(target_path):
                        continue
                    
                    print(f"  Downloading for {month_name} {year}...")
                
                    try:
                        driver.get(url) 
                        
                        # Wait for page to load
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "cwacimHSCODE"))
                        )
                        
                        # 1. Enter HS Code
                        hscode_input = driver.find_element(By.ID, "cwacimHSCODE")
                        hscode_input.clear()
                        hscode_input.send_keys(str(hscode))
                        
                        # 2. Select Month
                        Select(driver.find_element(By.ID, "cwacimMonth")).select_by_value(str(month))
                        
                        # 3. Select Year
                        Select(driver.find_element(By.ID, "cwacimYear")).select_by_value(str(year))
                        
                        # 4. Submit
                        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        driver.execute_script("arguments[0].click();", submit_btn)
                        
                        # 5. Wait for Excel Button to appear (with delay consideration)
                        try:
                            excel_btn = WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".buttons-excel"))
                            )
                            # Additional wait to ensure button is fully interactive
                            time.sleep(2)
                        except:
                            print(f"    No data/button for {month_name} {year}. Skipping.")
                            continue
                        
                        # 6. Click Download
                        driver.execute_script("arguments[0].click();", excel_btn)
                        
                        # 7. Wait for download to finish
                        timeout = 60
                        start_wait = time.time()
                        new_file = None
                        
                        while time.time() - start_wait < timeout:
                            latest = get_latest_file(TEMP_DOWNLOAD_DIR)
                            if latest:
                                # Check if file was modified after we started waiting
                                if os.path.getmtime(latest) > start_wait:
                                    new_file = latest
                                    break
                            time.sleep(1)
                        
                        if new_file:
                            # Move and Rename
                            # Adding a small buffer for file release
                            time.sleep(1)
                            shutil.move(new_file, target_path)
                            print(f"    Saved: {target_filename}")
                        else:
                            print("    Download timeout.")
                            
                    except Exception as e:
                        print(f"    Error processing {month_name} {year}: {e}")
                        # Ensure we reset for next iteration
                        continue
            
            print()  # Empty line after each HS code

    finally:
        print("Closing driver...")
        driver.quit()
        # Clean up temp dir if empty
        try:
            os.rmdir(TEMP_DOWNLOAD_DIR)
        except:
            pass

if __name__ == "__main__":
    print("=== Commodity-Wise Import Data Scraper ===\n")
    
    # Read HS codes from file
    hscodes = read_hscodes_from_file(HSCODES_FILE)
    
    if not hscodes:
        print("No HS codes found. Please add HS codes to the file and try again.")
    else:
        scrape_commodity_data(hscodes)
        print("\n=== Scraping Completed! ===")
