import json
import os 
import requests
import getpass
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import csv

def openai_query_general(query_type,search_info,api_key):
    model = ChatOpenAI(model="gpt-4o-mini",temperature=0,openai_api_key=api_key,max_tokens=3)
    messages = [
    SystemMessage("Based on the following text information, is this business a"+f'{query_type}'+"?. Print a Yes or No"),
    HumanMessage(f'{search_info}'),
    ]

    answer=model.invoke(messages)
    text_content=answer.content
    return text_content

def openai_query_advanced(advanced_query_question,search_info,api_key):
    model = ChatOpenAI(model="gpt-4o-mini",temperature=0,openai_api_key=api_key,max_tokens=3)
    messages = [
    SystemMessage("Based on the following text information,"+f'{advanced_query_question}'+"Print a Yes or No"),
    HumanMessage(f'{search_info}'),
    ]

    answer=model.invoke(messages)
    text_content=answer.content
    return text_content

def search_bing(query,mkt,subscription_key):

    url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count=5"
    headers = { 'Ocp-Apim-Subscription-Key': subscription_key }
    params = { 'q': query, 'mkt': mkt }
    response = requests.get(url, headers=headers,params=params)
    response.raise_for_status()

    results = json.loads(response.text)["webPages"]["value"]
    business_desc=[]
    for result in results:
        business_desc.append({result['snippet']})
    return business_desc

def scrapercsv_to_variable():
    advanced_scraper_data = []  # empty list
    with open("/Users/sean/Library/CloudStorage/OneDrive-DemeterPublishingLimited/Google maps scraper/.venv/business_scraper/scraped_data.csv") as file:
        reader = csv.reader(file)
        for line in reader:
            advanced_scraper_data.append(line)
    return advanced_scraper_data