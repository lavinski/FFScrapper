import xlsxwriter
import json
from io import BytesIO
from urllib.request import urlopen
from PIL import Image
import logging

def export_products_to_xlsx(product_info, file_path_name, add_images, stores):
    # Create a workbook and add a worksheet.

    logging.info("Prasidejo produktu xlsx failo generavimas... (Tai gali uztrukti)")
    full_file_path = file_path_name
    if len(file_path_name) > 4 and file_path_name[-4:] != "xlsx":
        full_file_path = '{}.xlsx'.format(file_path_name)

    workbook = xlsxwriter.Workbook(full_file_path)
    worksheet = workbook.add_worksheet()

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})

    # Add a number format for cells with money.
    money = workbook.add_format({'num_format': '$#,##0'})

    # Write some data headers.
    headers = ['FOTO','SKU','FF prekės ID','Statusas','StoreId','Kaina','Savikaina','MarkUP','Valiuta','NAV kolekcija','FF kolekcija','Galutinis likutis','FF likutis','Pard. proc.','FF pradinė kaina','FF nuolaida','Pardavimo kaina','Šalis','Url']

    for index,header in enumerate(headers):
        worksheet.write(0, index, header, bold)

    # Start from the first cell below the headers.
    row = 1

    cell_format = workbook.add_format()
    cell_format.set_shrink()

    # Iterate over the data and write it out row by row.
    for product_id, product in product_info.items():
        if "country_id" in product:
            country_id = product["country_id"]
        else:
            country_id = ""

        try:
            markup = round(float(product["price"])/float(product["lowest_price"]), 2)
        except:
            markup = ""

        if add_images and product["image"]:
            image = Image.open(BytesIO(urlopen(product["image"]).read()))
            image = image.resize((100,100))
            bs = BytesIO()
            image.save(bs, format="JPEG")
            worksheet.insert_image(row,0, product["image"],{'image_data': bs})
            worksheet.set_row(row, 100)

        worksheet.write(row, 1, product["sku"])
        worksheet.write(row, 2, product_id)
        worksheet.write(row, 3, product["status"])
        worksheet.write(row, 4, product["store_id"])
        worksheet.write(row, 5, product["price"])
        worksheet.write(row, 6, product["lowest_price"])
        worksheet.write(row, 7, markup, cell_format)
        worksheet.write(row, 8, product["currency"])
        worksheet.write(row, 9, product["nav_collection"])
        worksheet.write(row, 10, product["ff_season"])
        worksheet.write(row, 11, product["total_quantity"])
        worksheet.write(row, 12, product["stock_total"], cell_format)
        worksheet.write(row, 13, product["pard_proc"], cell_format)
        worksheet.write(row, 14, product["ff_base_price"])
        worksheet.write(row, 15, product["ff_base_discount"])
        worksheet.write(row, 16, product["ff_sale_price"])
        worksheet.write(row, 17, country_id)
        worksheet.write(row, 18, product["url"], cell_format)

        row += 1

    statistics_start_from = len(headers)
    worksheet.write(0, statistics_start_from, 'Statistika', bold)

    worksheet.write(1, statistics_start_from,  'Aktyvus:')
    worksheet.write(1, statistics_start_from+1, '=COUNTIFS(D2:B1048576,"Aktyvus")', None, '')

    worksheet.write(2, statistics_start_from, 'Neaktyvus:')
    worksheet.write(2, statistics_start_from+1, '=COUNTIFS(D2:B1048576,"Neaktyvus")', None, '')

    worksheet.write(3, statistics_start_from, 'Konkurentu:')
    worksheet.write_formula(3, statistics_start_from+1, '=COUNTIFS(D2:B1048576,"Konkurentu")', None, '')

    worksheet.set_column(0, 0, 15)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, len(headers)+5, 15)

    workbook.close()

    logging.info("Produktu xlsx failo generavimas baigtas")

def export_product_sizes_to_xlsx(product_info, file_path_name, stores):
    # get the sizes that are possible
    logging.info("Prasidejo produktu likuciu xlsx failo generavimas... (Tai gali uztrukti)")

    sizes = set()
    products_with_sizes = {}
    for product_id, product in product_info.items():
        if "sizes" in product and "available" in product["sizes"]:
            for size in product["sizes"]["available"].values():
                sizes.add(size["description"])

            products_with_sizes[product_id] = product

    sizes = sorted(list(sizes))
    sizes_index_map = dict((e,i) for (i,e) in enumerate(sizes))

    # Create a workbook and add a worksheet.
    full_file_path = file_path_name
    if len(file_path_name) > 4 and file_path_name[-4:] != "xlsx":
        full_file_path = '{}.xlsx'.format(file_path_name)
    workbook = xlsxwriter.Workbook(full_file_path)
    worksheet = workbook.add_worksheet()

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})

    # Write some data headers.
    worksheet.write('A1', 'SKU', bold)
    worksheet.write('B1', 'FF prekės ID', bold)
    worksheet.write('C1', 'Galutinis likutis', bold)
    worksheet.write('D1', 'Konkurentų likutis', bold)

    # Add a number format for cells with money.
    money = workbook.add_format({'num_format': '$#,##0'})
    storeIDColor = workbook.add_format({'bg_color': '#90EE90'})

    # Size format
    size_format = workbook.add_format({'bold': 1, 'align': 'center',
    'valign': 'vcenter','border': 1,})

    # Add sizes
    for size, index in sizes_index_map.items():
        column = index*2+4
        worksheet.merge_range(0,column,0,column+1, size, size_format)
        worksheet.write(1,column, 'Store ID', bold)
        worksheet.write(1,column+1, 'Kiekis', bold)

    # Start from the first cell below the headers.
    row = 2

    cell_format = workbook.add_format()
    cell_format.set_shrink()

    # Iterate over the data and write it out row by row.
    for product_id, product in products_with_sizes.items():
        worksheet.write(row, 0, product["sku"])
        worksheet.write(row, 1, product_id)
        worksheet.write(row, 2, product["total_quantity"])

        total_competitors_quantity = 0

        for size in product["sizes"]["available"].values():
            column = sizes_index_map[size["description"]]*2+4

            # the store id is ours
            if str(size["storeId"]) in stores:
                worksheet.write(row, column, stores[str(size["storeId"])], storeIDColor)
                
            else:
                worksheet.write(row, column, size["storeId"])
                total_competitors_quantity += size["quantity"]

            worksheet.write(row, column+1, size["quantity"])

        worksheet.write(row, 3, total_competitors_quantity)
           
        row += 1

    worksheet.set_column(0, 0, 25)
    worksheet.set_column(1, 500, 12)

    workbook.close()

    logging.info("Produktu likuciu xlsx failo generavimas baigtas")

if __name__ == "__main__":
    with open("results.json") as f:
        # export_product_sizes_to_xlsx(json.load(f), "rezultatai", {"13040":"TOPS Latvia"})
        export_products_to_xlsx(json.load(f), "rezultatai.xlsx", False, {"13040":"TOPS Latvia"})

    