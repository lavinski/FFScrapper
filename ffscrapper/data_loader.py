from FFapi import Api

import pandas as pd
import numpy
import math
import xls_generator
import os.path
import logging
import sys


def load_store_ids(store_ids_table):
    """
    Load data from store file (Parduotuviu lentele)
    """

    extension = os.path.splitext(store_ids_table)[1]

    if extension != ".xls":
        raise Exception(
            "Netinkamas lenteles formatas",
            "Parduotuviu lentele {}".format(store_ids_table),
        )

    xls = pd.ExcelFile(store_ids_table)
    sheet = xls.parse(0)

    store_ids = set(
        [int(site_id) for site_id in sheet["SiteId"] if not math.isnan(site_id)]
    )

    return store_ids


def load_ff_product_table(products_from_ff_table):
    """
    Load data from FF product table (FF produktu lentele)
    """

    ff_child_to_parent_mapping = {}
    extension = os.path.splitext(products_from_ff_table)[1]
    if extension != ".xls":
        raise Exception("Netinkamas lenteles formatas", "FF produktu lentele")

    xls = pd.ExcelFile(products_from_ff_table)
    sheet = xls.parse(0)

    for index in sheet.index:
        # if child id exists
        child_id = sheet["Parent product ID"][index]
        item_id = sheet["Product ID"][index]

        if not pd.isnull(child_id):
            ff_child_to_parent_mapping[str(int(child_id))] = str(int(item_id))
        ff_child_to_parent_mapping[str(int(item_id))] = str(int(item_id))

    return ff_child_to_parent_mapping

def load_product_table(products_table, statuses, ff_child_to_parent_mapping):
    """
    Load data from product table (Produktu lentele)
    """

    product_to_ff_status_map = {}

    extension = os.path.splitext(products_table)[1]
    if extension != ".xls":
        raise Exception("Netinkamas lenteles formatas", "Produktu lentele")

    xls = pd.ExcelFile(products_table)
    product_table_sheet = xls.parse(0)

    for index in product_table_sheet.index:
        if numpy.isnan(product_table_sheet["FF prekės iD"][index]):
            product_table_sheet["FF prekės iD"][index] = numpy.nan_to_num(
                product_table_sheet["FF prekės iD"][index]
            )

        product_id = str(int(product_table_sheet["FF prekės iD"][index]))

        status = statuses["not_in_ff"]
        if product_id in ff_child_to_parent_mapping:
            product_id = ff_child_to_parent_mapping[product_id]
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

        product_to_ff_status_map[product_id] = product_info

    return product_to_ff_status_map

def load_ff_price_product(ff_price_table, ff_child_to_parent_mapping, product_to_ff_status_map):
    """
    Load data from FF price table (FF kainodaros lentele)
    """
    extension = os.path.splitext(ff_price_table)[1]
    if extension != ".xls":
        raise Exception("Netinkamas lenteles formatas", "FF kainodaros lentele")

    xls = pd.ExcelFile(ff_price_table)
    sheet = xls.parse(
        0, converters={"Base Discount": lambda value: "{}%".format(value * 100)}
    )

    for index in sheet.index:
        product_id = str(sheet["Item ID"][index])
        if product_id in ff_child_to_parent_mapping:
            product_id = ff_child_to_parent_mapping[product_id]

        if product_id in product_to_ff_status_map:
            product_to_ff_status_map[product_id]["ff_base_price"] = str(
                sheet["Base Price(ā‚¬)"][index]
            )
            product_to_ff_status_map[product_id]["ff_season"] = str(
                sheet["Season"][index]
            )
            product_to_ff_status_map[product_id]["ff_base_discount"] = str(
                sheet["Base Discount"][index]
            )
            product_to_ff_status_map[product_id]["ff_sale_price"] = str(
                sheet["Sale Price(ā‚¬)"][index]
            )
            product_to_ff_status_map[product_id]["category"] = str(
                sheet["Category"][index]
            )
            product_to_ff_status_map[product_id]["gender"] = str(
                sheet["Gender"][index]
            )

    return product_to_ff_status_map