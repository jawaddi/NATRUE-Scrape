from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from driver_setup import setup_driver
import time
import re
from data_saver import save_to_json,save_to_google_sheets


#  extract the detials from the description
def extract_sections(text):
    if not text:
        return {"Ingredients": None, "Description": None, "Usage": None}
    
    # More flexible regex pattern
    pattern = r"Ingredients\s*(.*?)\s*(?:Description\s*(.*?)\s*)?(?:Usage\s*(.*))?$"

    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        ingredients = match.group(1).strip() if match.group(1) and match.group(1).strip() else None
        description = match.group(2).strip() if match.group(2) and match.group(2).strip() else None
        usage = match.group(3).strip() if match.group(3) and match.group(3).strip() else None

        # Remove new lines and extra spaces
        def clean_text(value):
            return " ".join(value.split()) if value else None

        return {
            "Ingredients": clean_text(ingredients),
            "Description": clean_text(description),
            "Usage": clean_text(usage)
        }

    return {"Ingredients": None, "Description": None, "Usage": None}



#Function to Extract Product Details
def extract_product_details(product):
    """Extracts name, brand, and image from the product listing."""
    try:
        name = product.find_element(By.CLASS_NAME, "product-list__item__name").text
    except NoSuchElementException:
        name = None

    try:
        brand = product.find_element(By.CLASS_NAME, "product-list__item__brand").text
    except NoSuchElementException:
        brand = None

    try:
        image = product.find_element(By.TAG_NAME, "img").get_attribute("src")
    except NoSuchElementException:
        image = None

    return name, brand, image

#Function to Extract Pop-up Details

def extract_popup_details(driver):
    """Extracts product details from the pop-up dialog."""
    try:
        certification_level = driver.find_element(By.CLASS_NAME, "dialog-product__certification__level").text
    except NoSuchElementException:
        certification_level = None

    try:
        dialog_product = driver.find_element(By.CLASS_NAME, "dialog-product__certification__description").text
    except NoSuchElementException:
        dialog_product = None

    try:
        manufacturer = driver.find_element(By.XPATH, "//div[@class='dialog-product__info__content']").text
    except NoSuchElementException:
        manufacturer = None

    try:
        description = driver.find_element(By.CLASS_NAME, "dialog-product__description").text
    except NoSuchElementException:
        description = None

    return certification_level, dialog_product, manufacturer, description

# Function to Scrape a Single Page

def scrape_page(driver, url):
    driver.get(url)
    
    # Wait for product list to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-list__item"))
        )
    except TimeoutException:
        print(f"❌ No products found or page did not load: {url}")
        return None

    products = driver.find_elements(By.CLASS_NAME, "product-list__item")
    if not products:
        print(f"❌ No products found on {url}. Stopping pagination.")
        return None

    scraped_data = []
    actions = ActionChains(driver)

    for i, product in enumerate(products):
        try:
           
            name, brand, image = extract_product_details(product)

           
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product)
            time.sleep(1)

            
            driver.execute_script("arguments[0].click();", product)

            # Wait for pop-up
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "dialog-product"))
                )
            except TimeoutException:
                print(f"⚠️ Pop-up did not appear for product {i + 1}. Skipping...")
                continue  

            # Extract pop-up details
            certification_level, dialog_product, manufacturer, description = extract_popup_details(driver)

            
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)

            # Store scraped data
            scraped_data.append({
                "Name": name,
                "Brand": brand,
                "Image URL": image,
                "Certification": certification_level,
                "Dialog Product": dialog_product,
                "Manufacturer": manufacturer,
                **extract_sections(description)
            })

        except Exception as e:
            print(f"❌ Error scraping product {i + 1}: {e}")

    return scraped_data


# Function to Scrape Multiple Pages
def scrape_all_pages(driver, base_url, max_pages=3):
    all_data = []
    page = 1

    while page <= max_pages:
        print(f"📄 Scraping Page {page}...")
        page_url = f"{base_url}&prod[pageIndex]={page}&prod[search]="
        scraped_data = scrape_page(driver, page_url)

        if not scraped_data:  # If no products found, stop
            break
        
        all_data.extend(scraped_data)
        page += 1

    return all_data



def products_scraping():
    base_url = "https://natrue.org/our-standard/natrue-certified-world/?database[tab]=products"
    driver = setup_driver()

    try:
        scraped_data = scrape_all_pages(driver, base_url, max_pages=150)#this could be dynamic number just and it could be scraped from the website
        save_to_json(scraped_data, "products.json")
        save_to_google_sheets(scraped_data,["Name", "Brand", "Image URL", "Certification", "Dialog Product", "Manufacturer", "Ingredients", "Description", "Usage"],"Products_sheet",) #make sure google sheet is exist before run this function
    finally:
        driver.quit()  # Ensure driver quits even if there's an error

# products_scraping()
