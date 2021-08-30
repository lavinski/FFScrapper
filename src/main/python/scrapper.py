from FFapi import Api

import json
import pandas as pd
import numpy
import requests
from bs4 import BeautifulSoup
import math
import time
import xls_generator
import csv
import os.path

from stores import StoreInformation

# GLOBAL VARIABLES
statuses = {
    "not_active": "Neaktyvus",
    "active": "Aktyvus",
    "competitor_selling": "Konkurentu",
    "not_in_ff": "Nenurodyta FF faile"
}

class Scrapper():

    def __init__(self,store_ids_table,products_table,products_from_ff_table,price_table,ff_price_table,main_table_save_path,quantity_table_save_path,categories_to_scrape=[],scrape_quantity=False,add_images=False,region="de",progress_bar_update_func = None):
        self.product_to_ff_status_map = {}
        self.store_ids = set()
        self.stores_to_name_mapping = {}

        # key -> child_id 
        # value -> parent_id
        self.ff_child_to_parent_mapping = {}

        self.products_from_ff_table = products_from_ff_table
        self.store_ids_table = store_ids_table
        self.products_table = products_table
        self.price_table = price_table
        self.ff_price_table = ff_price_table

        self.categories_to_scrape = categories_to_scrape

        self.region = region

        self.scrape_quantity = scrape_quantity

        self.add_images = add_images

        self.main_table_save_path = main_table_save_path
        self.quantity_table_save_path = quantity_table_save_path

        self.progress_bar_update_func = progress_bar_update_func

    def load_data_from_files(self):
        # load the store_ids

        extension = os.path.splitext(self.store_ids_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.store_ids_table) 
            sheet = xls.parse(0)

            self.store_ids = set([int(site_id) for site_id in sheet["SiteId"] if not math.isnan(site_id)])

            for index in sheet.index:
                self.stores_to_name_mapping[str(sheet["SiteId"][index])] = sheet["Store Name"][index]
        else:
            raise Exception("Netinkamas lenteles formatas", "Parduotuviu lentele {}".format(self.store_ids_table))

        # open price table to get more info
        product_sku_to_info = {}

        extension = os.path.splitext(self.price_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.price_table) 
            sheet = xls.parse(0)

            for index in sheet.index:
                product_sku_to_info[sheet["Prekės Nr."][index]] = {
                    "lowest_price": sheet["Vieneto savikaina"][index], 
                    "nav_collection": sheet["Kolekcija"][index],
                    "total_quantity": sheet["Galutinis likutis"][index],
                    "pard_proc": sheet["Pard. Proc."][index]
                }
        else:
            raise Exception("Netinkamas lenteles formatas", "Kainodaros lentele {}".format(self.price_table))
            
        # load ff file to determine if product ids that are in
        # product file are child or parentl

        extension = os.path.splitext(self.products_from_ff_table)[1]
        # if extension[1] == ".csv":
        #     with open(self.products_from_ff_table) as csvfile:
        #         ff_data = csv.reader(csvfile,delimiter=";")
        #         for row in ff_data:
        #             # if child id exists
        #             if row[1]:
        #                 if row[1].isdigit():
        #                     self.ff_child_to_parent_mapping[str(row[1])] = str(row[0])
        #             else:
        #                 self.ff_child_to_parent_mapping[str(row[0])] = str(row[0])
        # el
        if extension == ".xls":
            # load product ids
            xls = pd.ExcelFile(self.products_from_ff_table) 
            sheet = xls.parse(0)

            for index in sheet.index:
                # if child id exists
                child_id = sheet["Child"][index]
                item_id = sheet["Item id"][index]

                if not pd.isnull(child_id):
                    self.ff_child_to_parent_mapping[str(int(child_id))] = str(int(item_id))
            
                self.ff_child_to_parent_mapping[str(int(item_id))] = str(int(item_id))
        else:
            raise Exception("Netinkamas lenteles formatas", "FF produktu lentele")

        # load product ids
        extension = os.path.splitext(self.price_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.products_table) 
            sheet = xls.parse(0)

            for index in sheet.index:
                product_id = str(sheet["FF prekės ID"][index])

                status = statuses["not_in_ff"]
                if product_id in self.ff_child_to_parent_mapping:
                    product_id = self.ff_child_to_parent_mapping[product_id]
                    status = statuses["not_active"]

                
                # add to the list only if exist in pricing table
                if sheet["Nr."][index] in product_sku_to_info: 
                    product_info = {
                            "sku": str(sheet["Nr."][index]),
                            "lowest_price": str(product_sku_to_info[sheet["Nr."][index]]["lowest_price"]),
                            "image": "",
                            "status": status,
                            "store_id": "",
                            "nav_collection": str(product_sku_to_info[sheet["Nr."][index]]["nav_collection"]),
                            "total_quantity": str(product_sku_to_info[sheet["Nr."][index]]["total_quantity"]),
                            "pard_proc": str(product_sku_to_info[sheet["Nr."][index]]["pard_proc"]),
                            "url": "",
                            "price": "",
                            "currency": "",
                            "sizes": {},
                            "ff_base_price": "Nenurodyta",
                            "ff_season": "Nenurodyta",
                            "ff_base_discount": "Nenurodyta",
                            "ff_sale_price": "Nenurodyta",
                            "country_id": ""
                    }

                    self.product_to_ff_status_map[product_id] = product_info
        else:
            raise Exception("Netinkamas lenteles formatas", "Produktu lentele")


        extension = os.path.splitext(self.ff_price_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.ff_price_table) 
            sheet = xls.parse(0, converters={'Base Discount': lambda value: '{}%'.format(value * 100)})

            for index in sheet.index:
                product_id = str(sheet["Item ID"][index])
                if product_id in self.ff_child_to_parent_mapping:
                    product_id = self.ff_child_to_parent_mapping[product_id]

                if product_id in self.product_to_ff_status_map:
                    self.product_to_ff_status_map[product_id]["ff_base_price"] = str(sheet["Base Price(ā‚¬)"][index])
                    self.product_to_ff_status_map[product_id]["ff_season"] = str(sheet["Season"][index])
                    self.product_to_ff_status_map[product_id]["ff_base_discount"] = str(sheet["Base Discount"][index])
                    self.product_to_ff_status_map[product_id]["ff_sale_price"] = str(sheet["Sale Price(ā‚¬)"][index])

        else:
            raise Exception("Netinkamas lenteles formatas", "FF kainodaros lentele")



    def scrape_with_facet_exploit(self):

        store_information = StoreInformation(self.scrape_quantity)

        # scrape just womens and mens shoes
        from_the_child_counter = 0

        total_progress_bar_persentage_for_category = int(95 / len(self.get_category_ids_to_scrape()))

        for index,c in enumerate(self.get_category_ids_to_scrape()):
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
                self.progress_bar_update_func(index*total_progress_bar_persentage_for_category + int((page * total_progress_bar_persentage_for_category) / total_pages))

                print("     Product count:", len(products)) 
                print("     Progress:", index*total_progress_bar_persentage_for_category + int((page * total_progress_bar_persentage_for_category) / total_pages))

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

        
        print("Total products filtered by child id {}".format(from_the_child_counter))

    def get_category_ids_to_scrape(self):
        return self.categories_to_scrape

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
        xls_generator.export_products_to_xlsx(self.product_to_ff_status_map, self.main_table_save_path, self.add_images, self.stores_to_name_mapping)
        xls_generator.export_product_sizes_to_xlsx(self.product_to_ff_status_map, self.quantity_table_save_path, self.stores_to_name_mapping)

        self.progress_bar_update_func(100)

def outputTest(message):
    print("Output test", message)

if __name__ == "__main__":
    path_to_the_forlder = "/home/tomas/Projects/FFScannerWindows/src/main/python/lenteles"
    scrapper = Scrapper(path_to_the_forlder+"/parduotuviu_lentele (2).xls",path_to_the_forlder+"/produktu_lentele (1).xls",path_to_the_forlder+'/FF likuciu_lentele.xls',path_to_the_forlder+"/kainodaros lentele (1).xls",path_to_the_forlder+"/FF kainodaros lentele.xls",path_to_the_forlder+"/rez.xls",path_to_the_forlder+"/rez2.xls",["136301"],progress_bar_update_func=outputTest,scrape_quantity=True)

    scrapper.scrape()
