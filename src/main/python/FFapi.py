import requests
import pandas as pd
from pandas.io.json import json_normalize
import logging

class Api:
    def __init__(self, c_category = None, category = None, region = "de"):
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
        # self.params = '?view=%d&pagetype=%s&pricetype=%s&page=%d&c-category=%s'
        self.params = '?page=%d&c-category=%s'

        self.product_list = None
        self.df = pd.DataFrame()

        self.region = region

    def buildUrl(self):
        self.parameters = self.params % (
            # self.view,
            # self.pagetype,
            # self.pricetype,
            self.page,
            self.c_category
        )

        logging.info("     url: %s", self.baseUrl + self.parameters)

        return self.baseUrl + self.parameters

    def get_listings(self, page=1):
        self.page = page
        self.request = requests.get(self.buildUrl(), headers=self.headers)
        self.response = self.request.json()
        return self.response

    def parse_products(self, response):
        if response['listingItems'] is not None and response['listingItems']['items'] is not None:
            self.product_list = self.response['listingItems']['items']
            return self.product_list
            # if len(self.df) == 0:
            #     self.df = json_normalize(self.product_list)
            # else:
            #     self.df = pd.concat([self.df, json_normalize(self.product_list)])