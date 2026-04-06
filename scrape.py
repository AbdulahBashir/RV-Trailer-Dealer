import pandas as pd
import time
import csv
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options 
import os 

# --- 1. Configurations ---
EXCEL_FILE = 'data.xlsx'
URL_COLUMN_NAME = 'URL' 
CSV_FILE = 'scraped_data.csv'
XML_FILE = 'scraped_data.xml'
ELEMENT_WAIT_SECONDS = 20 

HARDCODED_DEALER_INFO = {
    'Dealer_Name': 'RV & Trailer Dealer', 
    'Parent_Company': 'N/A' 
}

# --- 2. FIELD NAMES (Updated for RV/Trailer Technical Specs) ---
FIELD_NAMES_ORDERED = [
    'Source_URL', 'Dealer_Name', 'Title', 'Address_Phone', 'Price', 'Stock_Number', 
    'Year', 'Make', 'Model', 'Condition', 'Status', 'Class', 'Length_FT', 
    'Hitch_Weight_LBS', 'Dry_Weight_LBS', 'Sub_Class', 'Shop_By_Length', 
    'Shop_By_Weight', 'Fresh_Water_Capacity', 'Gray_Water_Capacity', 
    'Black_Water_Capacity', 'Propane_Capacity', 'Gross_Weight_Rating', 
    'VIN', 'Description', 'Images_List', 'Parent_Company'
]

# --- 3. XPATHS (Latest Provided XPaths) ---
XPATH_CONFIG = {
    'Title': '//*[@id="row-1"]/div/div[1]/h1',
    'Address_Phone': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[2]/td[2]',
    'Price': '//*[@id="price-sale"]/div[2]',
    'Stock_Number': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[1]/td[2]',
    'Year': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[3]/td[2]',
    'Make': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[4]/td[2]',
    'Model': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[5]/td[2]',
    'Condition': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[6]/td[2]',
    'Status': '//*[@id="row-1"]/div/div[2]/table/tbody/tr[7]/td[2]',
    'Class': '//*[@id="c-2"]/tbody/tr[1]/td[2]',
    'Length_FT': '//*[@id="c-2"]/tbody/tr[2]/td[2]',
    'Hitch_Weight_LBS': '//*[@id="c-2"]/tbody/tr[3]/td[2]',
    'Dry_Weight_LBS': '//*[@id="c-2"]/tbody/tr[4]/td[2]',
    'Sub_Class': '//*[@id="c-2"]/tbody/tr[5]/td[2]',
    'Shop_By_Length': '//*[@id="c-2"]/tbody/tr[6]/td[2]',
    'Shop_By_Weight': '//*[@id="c-2"]/tbody/tr[7]/td[2]',
    'Fresh_Water_Capacity': '//*[@id="c-2"]/tbody/tr[8]/td[2]',
    'Gray_Water_Capacity': '//*[@id="c-2"]/tbody/tr[9]/td[2]',
    'Black_Water_Capacity': '//*[@id="c-2"]/tbody/tr[10]/td[2]',
    'Propane_Capacity': '//*[@id="c-2"]/tbody/tr[11]/td[2]',
    'Gross_Weight_Rating': '//*[@id="c-2"]/tbody/tr[12]/td[2]',
    'VIN': '//*[@id="c-2"]/tbody/tr[13]/td[2]',
    'Description': '//*[@id="row-1"]/div/div[1]/div[2]',
    
    # Image Container
    'Image_Container_XPath': '//*[@id="gallery-7"]/div[2]'
}

ALL_SCRAPED_DATA = [] 

def load_existing_data():
    global ALL_SCRAPED_DATA
    if os.path.exists(CSV_FILE):
        try:
            df_existing = pd.read_csv(CSV_FILE)
            existing_data = df_existing.to_dict('records')
            for item in existing_data:
                item['Images_List'] = item.get('Images_List', '').split('|') if isinstance(item.get('Images_List'), str) and item['Images_List'] else []
            ALL_SCRAPED_DATA.extend(existing_data)
        except Exception: pass

def save_xml_file(data_list):
    try:
        root = etree.Element("Root") 
        for item in data_list:
            node = etree.SubElement(root, "RV_Unit") 
            for key, value in item.items():
                str_val = str(value).strip()
                if str_val == 'N/A' or not str_val or key == 'Parent_Company': continue 
                if key == 'Images_List':
                    imgs = etree.SubElement(node, "Images")
                    for url in [str(u) for u in value if str(u).startswith('http')]:
                        etree.SubElement(imgs, "Image").text = url
                    if not list(imgs): node.remove(imgs)
                else:
                    etree.SubElement(node, key).text = str_val
        tree = etree.ElementTree(root)
        tree.write(XML_FILE, pretty_print=True, xml_declaration=True, encoding='utf-8')
    except Exception: pass

if __name__ == '__main__':
    load_existing_data()
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options) 

    try:
        df = pd.read_excel(EXCEL_FILE)
        urls_list = [url for url in df[URL_COLUMN_NAME].tolist() if url not in {item.get('Source_URL') for item in ALL_SCRAPED_DATA}]
        if not urls_list:
            print("ℹ️ No new URLs."); driver.quit(); exit()
    except Exception as e:
        print(f"❌ Excel Error: {e}"); driver.quit(); exit()

    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=FIELD_NAMES_ORDERED).writeheader()

    for index, url in enumerate(urls_list):
        print(f"\n[{index + 1}/{len(urls_list)}] Scraping: {url}")
        page_data = {field: 'N/A' for field in FIELD_NAMES_ORDERED}
        page_data.update({'Source_URL': url, 'Dealer_Name': HARDCODED_DEALER_INFO['Dealer_Name'], 'Parent_Company': HARDCODED_DEALER_INFO['Parent_Company']})
        
        try:
            driver.get(url)
            
            # Smart Wait for Title
            WebDriverWait(driver, ELEMENT_WAIT_SECONDS).until(
                EC.presence_of_element_located((By.XPATH, XPATH_CONFIG['Title']))
            )
            time.sleep(1.5) 

            # Scrape Text Fields
            for field, xpath in XPATH_CONFIG.items():
                if field == 'Image_Container_XPath': continue
                try:
                    page_data[field] = driver.find_element(By.XPATH, xpath).text.strip()
                except: pass

            # Scrape Images from gallery-7
            try:
                container = XPATH_CONFIG['Image_Container_XPath']
                imgs = driver.find_elements(By.XPATH, f"{container}//img")
                page_data['Images_List'] = list(set([i.get_attribute('src') for i in imgs if i.get_attribute('src') and 'http' in i.get_attribute('src')]))
                print(f"  🖼️ Images found: {len(page_data['Images_List'])}")
            except: pass

            # Save data
            csv_row = page_data.copy()
            csv_row['Images_List'] = '|'.join(page_data['Images_List'])
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=FIELD_NAMES_ORDERED).writerow(csv_row)
            
            ALL_SCRAPED_DATA.append(page_data)
            save_xml_file(ALL_SCRAPED_DATA)
            print(f"  ✅ Saved: {page_data['Title'][:25]}...")

        except TimeoutException:
            print(f"  ⚠️ Timeout: Skipping this URL.")
        except Exception:
            print(f"  ❌ Error: Skipping URL.")

    driver.quit()
    print("\n🏁 Process Complete.")