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
import logging
import time
import sys

# GLOBAL VARIABLES
statuses = {
    "not_active": "Neaktyvus",
    "active": "Aktyvus",
    "competitor_selling": "Konkurentu",
    "not_in_ff": "Nenurodyta FF faile",
    "active_found_with_sku": "Aktyvus (Surasta su SKU)",
    "competitor_selling_found_with_sku": "Konkurentu (Surasta su SKU)",
}

CATEGORY_TOTAL_PERCENTAGE = 85

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


class Scrapper:
    def __init__(
        self,
        store_ids_table,
        products_table,
        products_from_ff_table,
        ff_price_table,
        main_table_save_path,
        quantity_table_save_path,
        categories_to_scrape=[],
        scrape_quantity=False,
        add_images=False,
        region="gb",
        progress_bar_update_func=None,
        designer_id=None,
    ):
        self.product_to_ff_status_map = {}
        self.store_ids = set()
        self.stores_to_name_mapping = {}

        # key -> child_id
        # value -> parent_id
        self.ff_child_to_parent_mapping = {}

        self.products_from_ff_table = products_from_ff_table
        self.store_ids_table = store_ids_table
        self.products_table = products_table
        self.ff_price_table = ff_price_table
        self.designer_id = designer_id

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

            self.store_ids = set(
                [int(site_id) for site_id in sheet["SiteId"] if not math.isnan(site_id)]
            )

            for index in sheet.index:
                self.stores_to_name_mapping[str(sheet["SiteId"][index])] = sheet[
                    "Store Name"
                ][index]
        else:
            raise Exception(
                "Netinkamas lenteles formatas",
                "Parduotuviu lentele {}".format(self.store_ids_table),
            )

        extension = os.path.splitext(self.products_from_ff_table)[1]
        if extension == ".xls":
            # load product ids
            xls = pd.ExcelFile(self.products_from_ff_table)
            sheet = xls.parse(0)

            for index in sheet.index:
                # if child id exists
                child_id = sheet["Child"][index]
                item_id = sheet["Item id"][index]

                if not pd.isnull(child_id):
                    self.ff_child_to_parent_mapping[str(int(child_id))] = str(
                        int(item_id)
                    )

                self.ff_child_to_parent_mapping[str(int(item_id))] = str(int(item_id))
        else:
            raise Exception("Netinkamas lenteles formatas", "FF produktu lentele")

        extension = os.path.splitext(self.products_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.products_table)
            product_table_sheet = xls.parse(0)

            for index in product_table_sheet.index:
                if numpy.isnan(product_table_sheet["FF prekės iD"][index]):
                    product_table_sheet["FF prekės iD"][index] = numpy.nan_to_num(
                        product_table_sheet["FF prekės iD"][index]
                    )

                product_id = str(int(product_table_sheet["FF prekės iD"][index]))

                status = statuses["not_in_ff"]
                if product_id in self.ff_child_to_parent_mapping:
                    product_id = self.ff_child_to_parent_mapping[product_id]
                    status = statuses["not_active"]

                # Galutiniu likucio laukas gali tureti data. Pvz "Galutinis likutis 2022-07-03"
                # Tad mum reikia gauti lauko pavadinima kuris prasidedad Galutinis likutis
                total_quantity_key_name = next(
                    key
                    for key in product_table_sheet
                    if key.startswith("Galutinis likutis")
                )

                # add to the list only if exist in pricing table
                product_info = {
                    "sku": str(product_table_sheet["Prekės nr."][index]),
                    "lowest_price": str(
                        product_table_sheet["Vieneto savikaina"][index]
                    ),
                    "image": "",
                    "status": status,
                    "store_id": "",
                    "nav_collection": str(product_table_sheet["Kolekcija"][index]),
                    "total_quantity": str(
                        product_table_sheet[total_quantity_key_name][index]
                    ),
                    "pard_proc": str(product_table_sheet["Pard. %"][index]),
                    "url": "",
                    "price": "",
                    "currency": "",
                    "sizes": {},
                    "stock_total": 0,
                    "ff_base_price": "Nenurodyta",
                    "ff_season": "Nenurodyta",
                    "ff_base_discount": "Nenurodyta",
                    "ff_sale_price": "Nenurodyta",
                    "country_id": "",
                }

                self.product_to_ff_status_map[product_id] = product_info
        else:
            raise Exception("Netinkamas lenteles formatas", "Produktu lentele")

        extension = os.path.splitext(self.ff_price_table)[1]
        if extension == ".xls":
            xls = pd.ExcelFile(self.ff_price_table)
            sheet = xls.parse(
                0, converters={"Base Discount": lambda value: "{}%".format(value * 100)}
            )

            for index in sheet.index:
                product_id = str(sheet["Item ID"][index])
                if product_id in self.ff_child_to_parent_mapping:
                    product_id = self.ff_child_to_parent_mapping[product_id]

                if product_id in self.product_to_ff_status_map:
                    self.product_to_ff_status_map[product_id]["ff_base_price"] = str(
                        sheet["Base Price(ā‚¬)"][index]
                    )
                    self.product_to_ff_status_map[product_id]["ff_season"] = str(
                        sheet["Season"][index]
                    )
                    self.product_to_ff_status_map[product_id]["ff_base_discount"] = str(
                        sheet["Base Discount"][index]
                    )
                    self.product_to_ff_status_map[product_id]["ff_sale_price"] = str(
                        sheet["Sale Price(ā‚¬)"][index]
                    )

        else:
            raise Exception("Netinkamas lenteles formatas", "FF kainodaros lentele")

    def scrape_with_facet_exploit(self, search_in_sale_page=False):
        start_progress_bar_at = 0
        if search_in_sale_page:
            start_progress_bar_at = 50

        # scrape just womens and mens shoes
        from_the_child_counter = 0

        total_progress_bar_persentage_for_category = int(
            CATEGORY_TOTAL_PERCENTAGE / len(self.get_category_ids_to_scrape()) / 2
        )

        for index, c in enumerate(self.get_category_ids_to_scrape()):
            api = Api(
                c_category=c,
                region=self.region,
                designer_id=self.designer_id,
                search_in_sale_page=search_in_sale_page,
            )

            data = api.get_listings()
            total_pages = data["listingPagination"]["totalPages"]

            logging.info("Total pages: {}".format(total_pages))

            total_products = []

            for page in range(1, total_pages + 1):
                products = api.parse_products(api.get_listings(page=page))

                total_products.append(products)

                # update progress bar in gui
                progress = (
                    start_progress_bar_at
                    + index * total_progress_bar_persentage_for_category
                    + int(
                        (page * total_progress_bar_persentage_for_category)
                        / total_pages
                    )
                )
                self.progress_bar_update_func(progress)

                logging.info("     Product count: {}".format(len(products)))
                logging.info("     Progress: {}".format(progress))

                for product in products:
                    if "merchantId" in product and "id" in product:
                        store_id = product["merchantId"]
                        item_id = str(product["id"])

                        if item_id in self.ff_child_to_parent_mapping:
                            item_id = self.ff_child_to_parent_mapping[item_id]
                            from_the_child_counter += 1

                        if item_id in self.product_to_ff_status_map:
                            product["url"] = (
                                "https://www.farfetch.com/" + product["url"]
                            )

                            status = statuses["competitor_selling"]
                            if store_id in self.store_ids:
                                status = statuses["active"]

                            self.product_to_ff_status_map[item_id]["status"] = status
                            self.product_to_ff_status_map[item_id][
                                "store_id"
                            ] = store_id
                            self.product_to_ff_status_map[item_id]["url"] = product[
                                "url"
                            ]
                            self.product_to_ff_status_map[item_id]["price"] = product[
                                "priceInfo"
                            ]["finalPrice"]
                            self.product_to_ff_status_map[item_id][
                                "currency"
                            ] = product["priceInfo"]["currencyCode"]
                            self.product_to_ff_status_map[item_id][
                                "stock_total"
                            ] = product["stockTotal"]
                            self.product_to_ff_status_map[item_id]["image"] = product[
                                "images"
                            ]["cutOut"]

        logging.info(
            "Total products filtered by child id {}".format(from_the_child_counter)
        )

    def get_category_ids_to_scrape(self):
        return self.categories_to_scrape if self.categories_to_scrape else [None]

    def scrape(self):
        self.load_data_from_files()

        logging.info(self.main_table_save_path)
        logging.info(self.quantity_table_save_path)

        self.scrape_with_facet_exploit()
        self.scrape_with_facet_exploit(search_in_sale_page=True)

        xls_generator.export_products_to_xlsx(
            self.product_to_ff_status_map,
            self.main_table_save_path,
            self.add_images,
            self.stores_to_name_mapping,
        )

        self.progress_bar_update_func(100)


def outputTest(message):
    logging.info("Output test {}".format(message))


if __name__ == "__main__":
    path_to_the_forlder = "/Users/lavinskit/Programming/Projects/python/lenteles/naujos"
    scrapper = Scrapper(
        store_ids_table=path_to_the_forlder + "/parduotuviu_lentele 1.xls",
        products_table=path_to_the_forlder + "/PREKES ELEVENTY.xls",
        products_from_ff_table=path_to_the_forlder + "/FF PREKES ELEVENTY.xls",
        ff_price_table=path_to_the_forlder + "/FF KAINOS ELEVENTY.xls",
        main_table_save_path=path_to_the_forlder + "/rez.xls",
        quantity_table_save_path=path_to_the_forlder + "/rez2.xls",
        progress_bar_update_func=outputTest,
        scrape_quantity=True,
        designer_id=195900,
    )

    scrapper.scrape()
