import xlsxwriter
import json
from io import BytesIO
from urllib.request import urlopen
from PIL import Image
import logging
import requests
import sys

REQUEST_HEADERS = {
    "authority": "cdn-images.farfetch-contents.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,lt;q=0.7",
    "cache-control": "max-age=0",
    "sec-ch-ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def export_products_to_xlsx(product_info, file_path_name, add_images):
    # Create a workbook and add a worksheet.
    logging.info("Prasidejo produktu xlsx failo generavimas... (Tai gali uztrukti)")
    full_file_path = file_path_name
    if len(file_path_name) > 4 and file_path_name[-4:] != "xlsx":
        full_file_path = "{}.xlsx".format(file_path_name)

    workbook = xlsxwriter.Workbook(full_file_path)
    worksheet = workbook.add_worksheet()

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({"bold": True})

    # Write some data headers.
    headers = [
        "FOTO",
        "SKU",
        "FF prekės ID",
        "Kategorija",
        "Statusas",
        "StoreId",
        "Kaina",
        "Savikaina",
        "MarkUP",
        "Valiuta",
        "NAV kolekcija",
        "FF kolekcija",
        "Galutinis likutis",
        "FF likutis",
        "Pard. proc.",
        "FF pradinė kaina",
        "FF nuolaida",
        "Pardavimo kaina",
        "Šalis",
        "Url",
    ]

    for index, header in enumerate(headers):
        worksheet.write(0, index, header, bold)

    # Start from the first cell below the headers.
    row = 1

    cell_format = workbook.add_format()
    cell_format.set_shrink()

    percent_format = workbook.add_format({"num_format": "0.00%"})

    custom_number_format = workbook.add_format()
    custom_number_format.set_num_format("#,##0.00")
    custom_number_format.set_shrink()

    # Iterate over the data and write it out row by row.
    for product_id, product in product_info.items():
        if "country_id" in product:
            country_id = product["country_id"]
        else:
            country_id = ""

        try:
            markup = round(float(product["price"]) / float(product["lowest_price"]), 2)
        except:
            markup = ""

        if add_images and product["image"]:
            url = product["image"]
            response = requests.get(url, headers=REQUEST_HEADERS)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                image = image.resize((100, 100))
                bs = BytesIO()
                image.save(bs, format="JPEG")
                worksheet.insert_image(row, 0, product["image"], {"image_data": bs})
                worksheet.set_row(row, 100)
            else:
                logging.info(
                    f"Nepavyko atsiusti produkto paveiksliuko {product['sku']}. Status code: {product['sku']}"
                )

        # transform 30.00% into float and then it will be formatted to number
        ff_base_discount = str(product["ff_base_discount"]).replace("%", "")
        if ff_base_discount != "":
            ff_base_discount = float(ff_base_discount) / 100

        worksheet.write(row, 1, product["sku"])
        worksheet.write(row, 2, product_id)
        worksheet.write(row, 3, product["category"])
        worksheet.write(row, 4, product["gender"])
        worksheet.write(row, 5, product["status"])
        worksheet.write(row, 6, product["store_id"])
        worksheet.write(
            row,
            7,
            float(product["price"]) if product["price"] != "" else "",
            custom_number_format,
        )
        worksheet.write(
            row,
            8,
            float(product["lowest_price"]) if product["lowest_price"] != "" else "",
            custom_number_format,
        )
        worksheet.write(row, 9, float(markup) if markup != "" else "", cell_format)
        worksheet.write(row, 10, product["currency"])
        worksheet.write(row, 11, product["nav_collection"])
        worksheet.write(row, 12, product["ff_season"])
        worksheet.write(
            row,
            13,
            int(product["total_quantity"]) if product["total_quantity"] != "" else "",
            custom_number_format,
        )
        worksheet.write(
            row,
            14,
            int(product["stock_total"]) if product["stock_total"] != "" else "",
            custom_number_format,
        )
        worksheet.write(
            row,
            15,
            float(product["pard_proc"]) if product["pard_proc"] != "" else "",
            percent_format,
        )
        worksheet.write(
            row,
            16,
            float(product["ff_base_price"]) if product["ff_base_price"] != "" else "",
            custom_number_format,
        )
        worksheet.write(
            row,
            17,
            float(ff_base_discount) if ff_base_discount != "" else "",
            percent_format,
        )
        worksheet.write(
            row,
            18,
            float(product["ff_sale_price"]) if product["ff_sale_price"] != "" else "",
            custom_number_format,
        )
        worksheet.write(row, 19, country_id)
        worksheet.write(row, 20, product["url"], cell_format)

        row += 1

    statistics_start_from = len(headers)
    worksheet.write(0, statistics_start_from, "Statistika", bold)

    worksheet.write(1, statistics_start_from, "Aktyvus:")
    worksheet.write(
        1, statistics_start_from + 1, '=COUNTIFS(F2:F1048576,"Aktyvus")', None, ""
    )

    worksheet.write(2, statistics_start_from, "Neaktyvus:")
    worksheet.write(
        2, statistics_start_from + 1, '=COUNTIFS(F2:F1048576,"Neaktyvus")', None, ""
    )

    worksheet.write(3, statistics_start_from, "Konkurentu:")
    worksheet.write_formula(
        3, statistics_start_from + 1, '=COUNTIFS(F2:F1048576,"Konkurentu")', None, ""
    )

    worksheet.set_column(0, 0, 15)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, len(headers) + 5, 15)

    workbook.close()

    logging.info("Produktu xlsx failo generavimas baigtas")


if __name__ == "__main__":
    with open("results.json") as f:
        export_products_to_xlsx(
            json.load(f), "rezultatai.xlsx", False, {"13040": "TOPS Latvia"}
        )
