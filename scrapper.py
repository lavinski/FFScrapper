import xls_generator
import logging
import sys
import copy

from ffscrapper.data_loader import load_store_ids, load_ff_product_table, load_product_table, load_ff_price_product
from FFapi import Api

STATUSES = {
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
        self.store_ids = load_store_ids(self.store_ids_table)
        self.ff_child_to_parent_mapping = load_ff_product_table(self.products_from_ff_table)
        self.product_to_ff_status_map = load_product_table(self.products_table, STATUSES, self.ff_child_to_parent_mapping)
        self.product_to_ff_status_map = load_ff_price_product(self.ff_price_table, self.ff_child_to_parent_mapping, copy.deepcopy(self.product_to_ff_status_map))

    def scrape_with_facet_exploit(self, search_in_sale_page=False):
        start_progress_bar_at = 0
        if search_in_sale_page:
            start_progress_bar_at = 50

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

                            status = STATUSES["competitor_selling"]
                            if store_id in self.store_ids:
                                status = STATUSES["active"]

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
