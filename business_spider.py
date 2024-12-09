from pathlib import Path
import scrapy
import time
import csv
import w3lib
import mechanize
from urllib.parse import urlparse


class BusinessSpider(scrapy.Spider):
    name = "bspider"
    start_urls = ["https://www.rohatyngroup.com"]
    allowed_domains = [urlparse(start_urls[0]).netloc]

    def parse(self, response):
        self.seen_urls = set()
        for url in response.xpath('//a/@href').extract():
            full_url = response.urljoin(url)
            if full_url not in self.seen_urls:
                self.seen_urls.add(full_url)
                yield scrapy.Request(full_url, callback=self.text_response) 

    
    def text_response(self, response):
        self.seen_text = set()
        for text in response.xpath('//p').extract():
            stripped = w3lib.html.remove_tags(text)
            if stripped not in self.seen_text:
                yield {'text':stripped}



