import requests
import pandas as pd
from pandas.io.json import json_normalize
import logging
import sys
import time

class Api:
    def __init__(self, c_category = None, category = None, region = "de", designer_id = None, search_in_sale_page=False):
        self.baseUrl = 'https://www.farfetch.com/'+region+'/plpslice/listing-api/products-facets'
        self.headers = {
            'Origin': 'https://www.farfetch.com'
            , 'Referer': 'https://www.farfetch.com/shopping/m/items.aspx'
            , 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                            ' Chrome/75.0.3770.100 Safari/537.36'
            }
        self.view = 180
        self.category = category
        self.c_category = c_category
        self.pagetype = 'Shopping'
        self.gender = None
        self.pricetype = 'FullPrice'
        self.page = None
        self.params = '?page=%d&c-category=%s'
        self.designer_id = designer_id
        self.search_in_sale_page = search_in_sale_page

        self.product_list = None
        self.df = pd.DataFrame()

        self.region = region

    def buildUrl(self):
        parameters = f"?page={self.page}"

        if self.designer_id:
            parameters = parameters + f"&designer={self.designer_id}"
        
        if self.c_category:
            parameters = parameters + f"&c_category={self.c_category}"

        if self.search_in_sale_page:
            parameters = parameters + f"&pricetype=Sale"

        logging.info("     url: %s", self.baseUrl + parameters)

        return self.baseUrl + parameters

    def get_listings(self, page=1):
        self.page = page

        for attempt_counter in range(1, 21):
            try:
                self.request = requests.get(self.buildUrl(), headers=self.headers)
                self.response = self.request.json()
                # not to get caught by FF
                # if attempt_counter<5:
                #     raise requests.exceptions.ConnectionError()
                time.sleep(3)
                return self.response
            except:
                logging.error("Klaida nuskaitant duomenis is ff API: " + str(sys.exc_info()))
                logging.info("Bandymas nr.{}. Sistema bandys darkarta po 30s".format(attempt_counter))
                time.sleep(30)

        raise Exception("Klaida nuskaitant duomenis is ff API: " + str(sys.exc_info()))

    def parse_products(self, response):
        if response and response['listingItems'] is not None and response['listingItems']['items'] is not None:
            self.product_list = self.response['listingItems']['items']
            return self.product_list

        return []