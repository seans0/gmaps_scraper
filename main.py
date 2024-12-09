from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import googlemaps
import json
import os 
import requests
import sys
from scraper_functions import search_bing
from scraper_functions import openai_query_general
from scraper_functions import openai_query_advanced
from scraper_functions import scrapercsv_to_variable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import API_KEYS



######## APIS #########################
gmaps = googlemaps.Client(key=API_KEYS.gmaps_key)
bing_subscription_key = API_KEYS.bing_key
os.environ[API_KEYS.bing_key] = bing_subscription_key
assert bing_subscription_key
openai_key=API_KEYS.gpt_key

########### USER INPUTS ###############

introduction=print("Welcome to the Google Maps Scraper which keeping on theme with the namings, I've decided to name 'Merlin'. I've embedded the flowchart above so you can see how this is working, which will hopefully help you in your query choices. An advanced query would be where you are searching for information within the company, not just information on the company itself such as location. E.g. You want to know investment companies which also invest in agriculture, or seed suppliers which definitely supply canaryseed, then put keywords accordingly. The scraper runs to find matching keywords within a website, takes the body of the text where the keyword is found, and feeds it into chatgpt using your advanced query question to validate it. With that in mind, be smart about the keywords you put, don't be too vague and don't be too specific. If you don't need an advanced query, leave the field blank! Even though you will watch google maps scroll to the bottom of the list, the scraper is currently limited to only scrape 10 results so that we don't rinse our credits from all the API'S. Here's an example of an entire search you could run: Query input: \"investment companies\", Query location: \"london\",Location codes: \"en-GB\",Advanced query:\"agriculture\",\"farm\",\"irrigation\", Advanced query question: \"Does this investment company also invest in agriculture?\"")

query_input = input("Input your search query here (Without location):")
query_location = input("Input your location here: ")
mkt = input("In what language+country? (In this format [en-CA], language code then country code):")
advanced_query=input("Advanced query keywords:").replace(" ", "").split(",")
advanced_query_question=input("Advanced query question:")
############ INITIALISING DICTIONARIES AND OTHER ###################

@dataclass
class Business:
        name: str=None
        type: str=None
        website: str=None
        address: str=None
        phone_number: str=None
        plus_code: str=None
        latitude: float=None
        longitude: float=None
        validation: str=None
        advanced_info: str=None

@dataclass
class businessList:
        business_list : list[Business] = field(default_factory=list)

        def dataframe(self):
                return pd.json_normalize((asdict(business) for business in self.business_list), sep='')
        
        def save_to_csv(self, filename):
                self.dataframe().to_csv(f'{filename}.csv',index=False)
        def save_to_excel(self, filename):
                self.dataframe().to_excel(f'{filename}.xlsx',index=False)


############# MAIN FUNCTION: PLAYWRIGHT SCRAPE GOOGLE MAPS --> SCRAPY SCRAPE IF NEEDED --> CHATGPT VALIDATION ################
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page=browser.new_page()
        
        page.goto('https://www.google.com/maps', timeout=20000)
        page.mouse.wheel(0,5000)

        #accept_button=page.locator('//[button[contains(@aria-label,"Accept all")]')
        #accept_button.click()
           
        page.locator('//input[@id="searchboxinput"]').fill(f'{query_input}' f'{query_location}')

        page.keyboard.press('Enter')


        page.hover('//div[@tabindex="-1" and @style="position: relative;"]')
        
        if page.locator('//*[text()="You\'ve reached the end of the list."]').is_visible() is True:
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place") and not(contains(@aria-label,"Sponsored"))]').all()
        else:
            while page.locator('//*[text()="You\'ve reached the end of the list."]').is_visible() is False:
                page.mouse.wheel(0,100)
                listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place") and not(contains(@aria-label,"Sponsored"))]').all()
        

        business_list = businessList()
           
        for listing in listings[:1]:
            website_url=[]

            listing.click() 
            page.wait_for_timeout(3000)
            
            name_xpath = '//div[@role="main" and contains(@jslog, "mutable:true;metadata:")]//h1[not(contains(@aria-label, "Sponsored"))]'
            type_xpath = '//div[@class="fontBodyMedium"]//button[contains(@jsaction, "category")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            plus_code_xpath = '//button[contains(@data-item-id, "oloc")]//div[contains(@class, "fontBodyMedium")]'

            business=Business()
            if page.locator(name_xpath).count()>0:
                business.name = page.locator(name_xpath).inner_text()
            else:
                business.name = ''
            if page.locator(type_xpath).count()>0:
                business.type = page.locator(type_xpath).inner_text()
            else:
                business.type = ''
            if page.locator(website_xpath).count()>0:
                business.website = page.locator(website_xpath).inner_text()
                website_url.append(business.website)
            else:
                business.website = ''
            if page.locator(address_xpath).count()>0:
                business.address = page.locator(address_xpath).inner_text()
            else:
                business.address = ''
            if page.locator(phone_number_xpath).count()>0:
                business.phone_number = page.locator(phone_number_xpath).inner_text()
            else:
                business.phone_number = ''
            if page.locator(plus_code_xpath).count()>0:
                business.plus_code = page.locator(plus_code_xpath).inner_text()
                geocode_result = gmaps.geocode(business.plus_code)
                location = geocode_result[0]['geometry']['location']
                business.latitude = location['lat']
                business.longitude = location['lng']
            else:
                  business.plus_code = ''

            business_list.business_list.append(business)

        browser.close()

    if advanced_query_question=='':
        for business in business_list.business_list:
            business_info = f'{business.name} - {business.address}'
            site=business.website
            search_info=search_bing(business_info,mkt,bing_subscription_key)

            answer=openai_query_general(query_input,search_info,openai_key)
            business.validation=answer
    else:
        from spiders.business_spider import BusinessSpider
        for business in business_list.business_list:
            
            process = CrawlerProcess(get_project_settings())
            
            process.crawl(BusinessSpider)
            process.start()

            business.advanced_info=scrapercsv_to_variable()

            answer=openai_query_advanced(advanced_query,business.advanced_info,openai_key)
            business.validation=answer
             

    business_list.save_to_csv('google_maps_data')
    business_list.save_to_excel('google_maps_data')

if __name__ == "__main__":
        main()