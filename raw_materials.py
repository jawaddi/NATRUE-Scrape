import time
import os
import json
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from data_saver import save_to_google_sheets

DOWNLOAD_DIRECTORY = os.path.abspath("downloads")
EXCEL_EXTENSION = ".xlsx"
JSON_EXTENSION = ".json"


def setup_download_directory():
    os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)


def configure_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIRECTORY,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def download_excel(driver, url):
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 15)
        export_button = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), 'Export')]")))

        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export')]")))

        try:
            overlay_close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='close-overlay']"))
            )
            overlay_close_button.click()
            print("Closed overlay.")
        except TimeoutException:
            print("No overlay found.")

        driver.execute_script("arguments[0].click();", export_button)
        print("Clicked the export button. Waiting for download...")

        timeout = 30
        start_time = time.time()
        while time.time() - start_time < timeout:
            files = [f for f in os.listdir(DOWNLOAD_DIRECTORY) if f.endswith(EXCEL_EXTENSION)]
            if files:
                print("Download complete.")
                return
            time.sleep(2)

        print("Download failed: No Excel file found.")

    except TimeoutException:
        print("Timed out waiting for the export button.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        driver.quit()

def find_downloaded_file():
    files = [f for f in os.listdir(DOWNLOAD_DIRECTORY) if f.endswith(EXCEL_EXTENSION)]
    if not files:
        print("No Excel file found.")
        sys.exit(1)

    excel_file_path = os.path.join(DOWNLOAD_DIRECTORY, files[0])
    print(f"Found Excel file: {excel_file_path}")
    return excel_file_path


def convert_xlsx_to_json(xlsxfile):
    df = pd.read_excel(xlsxfile, engine="openpyxl")

    json_data = df.to_json(orient="records", indent=4, force_ascii=False)

    os.makedirs("scraped_data", exist_ok=True)
    filepath = os.path.join("scraped_data", "raw_materials1.json")

    # Save to JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_data)

    print(f"Conversion complete!")

def convert_and_save_file():
        excel_file_path = find_downloaded_file()

        if not excel_file_path:
            print("No file found to process. Exiting.")
            return  # Exit the function early if the file is not found.
        
        convert_xlsx_to_json(excel_file_path)
        
        file_path = os.path.join(os.getcwd(), "scraped_data", "raw_materials1.json")

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            print("Data loaded from JSON. Saving to Google Sheets...")
            save_to_google_sheets(data, ["Name", "Manufacturer", "Composition", "INCI", "Status", "Expiration"], "raw_materials")#make sure google sheet is exist before run this function


def raw_materials_scraping():
    setup_download_directory()
    driver = configure_driver()

    try:
        url = "https://natrue.org/our-standard/natrue-certified-world/?database[tab]=raw-materials"
        download_excel(driver, url)
        convert_and_save_file()
    except Exception as e:
        print(f"An error occurred: {e}")


# raw_materials_scraping()
