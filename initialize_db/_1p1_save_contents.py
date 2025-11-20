
from unstructured.documents.elements import NarrativeText
from unstructured.partition.text_type import sentence_count
###############################################################################################
# Code to extract url from sitemap.xml
###############################################################################################
import requests, re, os, json
from unstructured.partition.html import partition_html
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup



urls = [
    "https://www.propertyguru.com.sg/listing/for-sale-interterrace-along-macpherson-road-25232097",
    "https://www.propertyguru.com.sg/listing/for-sale-8-raja-25232113",
    "https://www.propertyguru.com.sg/listing/hdb-for-rent-188-pasir-ris-street-12-25376778",
    "https://www.propertyguru.com.sg/listing/for-rent-hillion-residences-25385495"
]


# Fetch the HTML contents of the target pages
contents = []
for url in urls:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        contents.append(page.content())
        browser.close()





# Extract the relevant information from the HTML contents
property_info = property_info = [None] * len(urls)
print("contents",contents)
for i in range(len(contents)):

    print(f"Currently processing: {i+1} of {len(contents)}")

    soup = BeautifulSoup(contents[i], 'html.parser')

    property_overview = soup.find('div', class_='property-overview-section')
    # property_title = property_overview.find('h1', class_='title')
    # property_address = property_overview.find('div', class_='full-address')
    property_description = soup.find('div', class_='description')
    property_more_details = soup.find('section', class_='details-section')
    property_amenities = soup.find('section', class_='property-amenities-section')

    lst_property_overview = [text.strip() for text in property_overview.stripped_strings if text.strip()]
    lst_property_description = [text.strip() for text in property_description.stripped_strings if text.strip()]
    lst_property_more_details = [text.strip() for text in property_more_details.stripped_strings if text.strip()]
    lst_property_amenities = [text.strip() for text in property_amenities.stripped_strings if text.strip()]


    property_info[i] = "# **Property Overview**\n\n " + "; ".join(lst_property_overview) + "\n\n " \
        + "# **Property Description**\n\n " + "; ".join(lst_property_description) + "\n\n " \
        + "# **Property Details**\n\n " + "; ".join(lst_property_more_details) + "\n\n " \
        + "# **Property Amenities**\n\n " + "; ".join(lst_property_amenities) + "\n\n "


# Save the extracted information to a JSON file
property_info_json = []
for i, info in enumerate(property_info):
    property_info_json.append({
        'id': i + 1,
        'url': urls[i],
        'category': 'Rental' if urls[i].count("for-rent")>0 else 'Sale',
        'extracted_data': property_info[i]
    })

# Save the JSON file
with open('./data/property_info.json', 'w', encoding='utf-8') as f:
        json.dump(property_info_json, f, indent=4, ensure_ascii=False)