import re
import requests
import pandas as pd

# ==============================
# Configuration
# ==============================
# Atlanta Marine ka main sitemap
SITEMAP_URL = "https://www.arrkannrv.com/sitemap.xml"

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def get_sitemap_urls(url):
    print(f"Fetching sitemap from: {url}")
    try:
        # Session use karne se block hone ke chance kam hote hain
        session = requests.Session()
        resp = session.get(url, headers=DEFAULT_HEADERS, timeout=30)
        
        # Agar 403 aaye to bypass ki koshish (lekin ye aksar block hi rehta hai bina browser ke)
        resp.raise_for_status()

        all_links = []
        
        # XML loc tags nikalna
        found_locs = re.findall(r'<loc>(.*?)</loc>', resp.text)
        
        for loc in found_locs:
            # --- CLEANUP CDATA TAGS (Added Fix) ---
            loc = loc.replace("<![CDATA[", "").replace("]]>", "").strip()
            
            loc = loc.strip().replace("&amp;", "&")
            
            # 1. Check if it's a sub-sitemap (xml file)
            if ".xml" in loc.lower() or "sitemap" in loc.lower():
                # Sirf kaam ke sub-sitemaps follow karein
                if any(x in loc.lower() for x in ["inventory", "unit", "vehicle", "product", "listing"]):
                    print(f"Found sub-sitemap: {loc}")
                    try:
                        sub_resp = session.get(loc, headers=DEFAULT_HEADERS, timeout=30)
                        # --- CLEANUP CDATA TAGS in sub-sitemap links ---
                        sub_locs_raw = re.findall(r'<loc>(.*?)</loc>', sub_resp.text)
                        sub_links = [s.replace("<![CDATA[", "").replace("]]>", "").strip() for s in sub_locs_raw]
                        all_links.extend(sub_links)
                    except:
                        continue
            else:
                all_links.append(loc)

        # --- REFINED FILTERING FOR ATLANTA MARINE & OTHERS ---
        filtered_links = []
        # Atlanta Marine ke links mein aksar '/vdp/' ya '/inventory/' aata hai
        boat_patterns = ["-detail", "/inventory/", "/vdp/", "new-20", "used-20", "/view-details/"]
        
        for link in all_links:
            link = link.strip().replace("&amp;", "&")
            
            # Agar link in patterns mein se kisi ko follow kare
            if any(p in link.lower() for p in boat_patterns):
                # Faltu social media ya privacy links nikalna
                if not any(bad in link.lower() for bad in ["facebook", "twitter", "instagram", "google", "pinterest", "youtube"]):
                    filtered_links.append(link)

        return list(set(filtered_links))

    except Exception as e:
        print(f"Error occurred: {e}")
        return []

def save_to_excel(links_list):
    if not links_list:
        print("No links found to save.")
        return

    df = pd.DataFrame(links_list, columns=["URL"])
    file_name = "data.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n✅ Success! {len(links_list)} links have been saved to '{file_name}'.")

def process():
    print("Job: Starting link collection...")
    product_links = get_sitemap_urls(SITEMAP_URL)
    
    print(f"\nTOTAL VALID LINKS FOUND: {len(product_links)}")
    
    for i, link in enumerate(product_links, 1):
        print(f"{i}: {link}")

    save_to_excel(product_links)

if __name__ == "__main__":
    process()