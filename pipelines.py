# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
import json
import w3lib.html
from scrapy.exceptions import DropItem
        
class KeywordFilterPipeline:
    keywords = ['agriculture']
    def process_item(self, item, spider):
        if any(key in item['text'] for key in self.keywords):
            return item
        else:
            return None
        
class DuplicateFilterPipeline:
    def __init__(self):
        self.seen_texts = set()

    def process_item(self, item, spider):
        if item is not None:
            text = item['text']
            if text not in self.seen_texts:
                self.seen_texts.add(text)
                return item
            else:
                return None
        else:
            pass

class UrlExportPipeline:
    def open_spider(self, spider):
        self.file = open("/Users/sean/Library/CloudStorage/OneDrive-DemeterPublishingLimited/Google maps scraper/.venv/business_scraper/scraped_data.csv", "w")
        self.writer = csv.writer(self.file)

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        if item is not None:
            row = [item.get(field, '') for field in item.keys()]
            self.writer.writerow(row)
        print(item)


