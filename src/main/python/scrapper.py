from FFapi import Api

import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
import time
import xls_generator
import csv

from stores import StoreInformation

# GLOBAL VARIABLES
statuses = {
    "not_active": "Neaktyvus",
    "active": "Aktyvus",
    "competitor_selling": "Konkurentu",
    "not_in_ff": "Nenurodyta FF faile"
}

class Scrapper():

    def __init__(self,store_ids_table,products_table,products_from_ff_table,price_table,main_table_save_path,quantity_table_save_path,scrape_mens_shoes=False,scrape_womens_shoes=False,scrape_quantity=False,add_images=False,region="de",progress_bar_update_func = None):
        self.product_to_ff_status_map = {}
        self.store_ids = set()

        # key -> child_id 
        # value -> parent_id
        self.ff_child_to_parent_mapping = {}

        self.products_from_ff_table = products_from_ff_table
        self.store_ids_table = store_ids_table
        self.products_table = products_table
        self.price_table = price_table

        self.scrape_mens_shoes = scrape_mens_shoes
        self.scrape_womens_shoes = scrape_womens_shoes

        self.region = region

        self.scrape_quantity = scrape_quantity

        self.add_images = add_images

        self.main_table_save_path = main_table_save_path
        self.quantity_table_save_path = quantity_table_save_path

        self.progress_bar_update_func = progress_bar_update_func

    def load_data_from_files(self):
        # load the store_ids
        xls = pd.ExcelFile(self.store_ids_table) 
        sheet = xls.parse(0)

        self.store_ids = set([int(site_id) for site_id in sheet["SiteId"] if not math.isnan(site_id)])

        # open price table to determine the lowest price
        product_sku_to_lowest_price = {}
        xls = pd.ExcelFile(self.price_table) 
        sheet = xls.parse(0)

        for index in sheet.index:
            product_sku_to_lowest_price[sheet["Prekės Nr."][index]] = sheet["Vieneto savikaina"][index]

        # load ff file to determine if product ids that are in
        # product file are child or parent
        with open(self.products_from_ff_table) as csvfile:
            ff_data = csv.reader(csvfile,delimiter=";")
            for row in ff_data:
                # if child id exists
                if row[1]:
                    if row[1].isdigit():
                        self.ff_child_to_parent_mapping[str(row[1])] = str(row[0])
                else:
                    self.ff_child_to_parent_mapping[str(row[0])] = str(row[0])

        # load product ids
        xls = pd.ExcelFile(self.products_table) 
        sheet = xls.parse(0)

        for index in sheet.index:
            product_id = str(sheet["FF prekės ID"][index])

            status = statuses["not_in_ff"]
            if product_id in self.ff_child_to_parent_mapping:
                product_id = self.ff_child_to_parent_mapping[product_id]
                status = statuses["not_active"]

            lowest_price = ""
            if sheet["Nr."][index] in product_sku_to_lowest_price: 
                 lowest_price = product_sku_to_lowest_price[sheet["Nr."][index]]

            self.product_to_ff_status_map[product_id] = {
                                "sku": str(sheet["Nr."][index]),
                                "lowest_price": lowest_price,
                                "image": "",
                                "status": status,
                                "store_id": "",
                                "url": "",
                                "price": "",
                                "currency": "",
                                "sizes": {}
                        }


    def scrape_with_facet_exploit(self):

        store_information = StoreInformation(self.scrape_quantity)

        # scrape just womens and mens shoes
        from_the_child_counter = 0

        total_progress_bar_persentage_for_category = int(95 / len(self.get_category_ids_to_scrape()))

        for c in self.get_category_ids_to_scrape():
            api = Api(c_category=c,region=self.region)

            total_pages = api.get_listings()['listingPagination']['totalPages']

            with open('total_pages.json', 'w') as outfile:
                json.dump(api.get_listings(), outfile)

            print("Total pages:", total_pages)

            for page in range(1, total_pages+1):
                # print("Scrapping page: ",page)
                products = api.parse_products(
                    api.get_listings(page=page)
                )

                # update progress bar in gui
                self.progress_bar_update_func(int((page * total_progress_bar_persentage_for_category) / total_pages))

                print("     Product count:", len(products)) 

                for product in products:
                    # print(product)
                    if "merchantId" in product and "id" in product:
                        store_id = product["merchantId"]
                        item_id = str(product["id"])

                        if item_id in self.ff_child_to_parent_mapping:
                            item_id = self.ff_child_to_parent_mapping[item_id]
                            from_the_child_counter += 1

                        if item_id in self.product_to_ff_status_map:
                            product["url"] = "https://www.farfetch.com/" + product["url"]

                            if store_id in self.store_ids:
                                status = statuses["active"]
                                country_id = ""
                                sizes = {}
                            else:
                                status = statuses["competitor_selling"]
                                information = store_information.get_information(store_id, product["url"])

                                country_id = information["country_id"]
                                sizes = information["sizes"]

                            self.product_to_ff_status_map[item_id]["status"] = status
                            self.product_to_ff_status_map[item_id]["store_id"] = store_id
                            self.product_to_ff_status_map[item_id]["url"] = product["url"]
                            self.product_to_ff_status_map[item_id]["price"] = product["priceInfo"]["finalPrice"]
                            self.product_to_ff_status_map[item_id]["currency"] = product["priceInfo"]["currencyCode"]
                            self.product_to_ff_status_map[item_id]["country_id"] = country_id
                            self.product_to_ff_status_map[item_id]["sizes"] = sizes
                            self.product_to_ff_status_map[item_id]["image"] = product["images"]["cutOut"]

                # print(self.product_to_ff_status_map)
                # exit()

        
        print("Total products filtered by child id {}".format(from_the_child_counter))

    def get_category_ids_to_scrape(self):
        ids_to_scrape = []
        if self.scrape_mens_shoes:
            ids_to_scrape.append("135968")

        if self.scrape_womens_shoes:
            ids_to_scrape.append("136301")

        return ids_to_scrape

    def scrape(self):
        # prideti cia reiksmes is mygtuku
        self.load_data_from_files()

        print(self.main_table_save_path)
        print(self.quantity_table_save_path)

        start = time.time()

        self.scrape_with_facet_exploit()

        print("Total scrapping time: ", (time.time() - start))

        print(self.product_to_ff_status_map)

        with open('results.json', 'w') as outfile:
            json.dump(self.product_to_ff_status_map, outfile)

        # generate xls file
        xls_generator.export_products_to_xlsx(self.product_to_ff_status_map, self.main_table_save_path, self.add_images)
        xls_generator.export_product_sizes_to_xlsx(self.product_to_ff_status_map, self.quantity_table_save_path)

        self.progress_bar_update_func(100)

if __name__ == "__main__":
    scrapper = Scrapper("store_ids.xls","products.xls",'products_from_ff.csv',"kainodaros_lentele.xls",True,False,False)

    scrapper.scrape()