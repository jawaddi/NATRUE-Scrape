import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from driver_setup import setup_driver
from data_saver import save_to_json, save_to_google_sheets

#Function to Extract Brand Details
#
def extract_brand_details(product):
    """Extracts name and image from the product listing."""
    try:
        name = product.find_element(By.CLASS_NAME, "brand-list__item__name").text
    except NoSuchElementException:
        name = None
    try:
        image = product.find_element(By.TAG_NAME, "img").get_attribute("src")
    except NoSuchElementException:
        image = None
    return name, image

#Function to Extract Pop-up Details

def extract_popup_details(driver):
    """Extracts product details from the pop-up dialog."""
    try:
        brand_description = driver.find_element(By.CLASS_NAME, "dialog-brand__description").text
    except NoSuchElementException:
        brand_description = None
    return brand_description


#Function to Get Max Pages for a Letter
def get_max_pages(driver, letter, base_url):
    """Extracts the maximum number of pages for the given letter."""
    page_url = f"{base_url}&brands[filters][letter]={letter}"
    driver.get(page_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "brand-list__item"))
        )
    except TimeoutException:
        print(f"❌ No products found or page did not load for letter {letter}.")
        return 0
    try:
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, "ul.el-pager li.number")
        max_page = int(pagination_elements[-1].text)
    except (NoSuchElementException, IndexError, ValueError):
        max_page = 1 

    return max_page


#Function to Scrape a Single Page
def scrape_page(driver, url):
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "brand-list__item"))
        )
    except TimeoutException:
        print(f"❌ No products found or page did not load: {url}")
        return None

    brands = driver.find_elements(By.CLASS_NAME, "brand-list__item")
    if not brands:
        print(f"❌ No products found on {url}. Stopping pagination.")
        return None

    scraped_data = []
    actions = ActionChains(driver)

    for i, brand in enumerate(brands):
        try:
            name, image = extract_brand_details(brand)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", brand)
            time.sleep(1)

            driver.execute_script("arguments[0].click();", brand)

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "dialog-brand__description"))
                )
            except TimeoutException:
                print(f"⚠️ Pop-up did not appear for product {i + 1}. Skipping...")
                continue

            brand_description = extract_popup_details(driver)

            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)

            scraped_data.append({
                "Name": name,
                "Image URL": image,
                "Brand Description": brand_description
            })

        except Exception as e:
            print(f"❌ Error scraping product {i + 1}: {e}")

    return scraped_data

#Function to Scrape Pages for a Letter
def scrape_pages_for_letter(driver, base_url, letter):
    all_data = []
    max_pages = get_max_pages(driver, letter, base_url)

    if max_pages == 0:
        return all_data

    for page in range(1, max_pages + 1):
        print(f"Scraping Brands starting with {letter} (Page {page})...")
        page_url = f"{base_url}&brands[pageNumber]={page}&brands[filters][letter]={letter}"
        scraped_data = scrape_page(driver, page_url)

        if not scraped_data:
            break
        
        all_data.extend(scraped_data)

    return all_data

#Function to Scrape All Letters
def scrape_all_letters(driver, base_url):
    all_data = []
    
    # Loop over A-Z and the special '#' character
    characters = [chr(letter) for letter in range(ord('A'), ord('Z') + 1)] + ['#']
    
    for char in characters:
        print(f"Starting to scrape brands for {char}...")
        scraped_data = scrape_pages_for_letter(driver, base_url, char)
        if scraped_data:
            all_data.extend(scraped_data)

    return all_data

def brand_scraping():
    base_url = "https://natrue.org/our-standard/natrue-certified-world/?database[tab]=brands"
    driver = setup_driver()
   
    try:
        
        # Scrape brands for all letters A-Z
        scraped_data = scrape_all_letters(driver, base_url)
        save_to_json(scraped_data, "Brands.json")
        save_to_google_sheets(scraped_data, ["Name", "Image URL", "Brand Description"], "Brands_sheet")#make sure google sheet is exist before run this function
    finally:
        driver.quit()

# if we want to run only this piece of codde
# brand_scraping()


