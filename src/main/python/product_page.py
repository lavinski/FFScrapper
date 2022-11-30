import json
import requests
import re
import os 
import os.path
import logging
import sys
import time

def get_product_page(sku):
    search_url = f'https://www.farfetch.com/de/search?q={sku}'

    # scrape the product page to determine the stores location
    for attempt_counter in range(1, 21):
        try:
            headers={
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            }
            page = requests.get(search_url, headers=headers)
            time.sleep(5)
            break
        except:
            logging.error("Produkto puslapio duomenu gavimas. Klaida nuskaitant duomenis is produkto puslapio: " + str(sys.exc_info()))
            logging.info("Produkto puslapio duomenu gavimas. Bandymas nr.{}. Sistema bandys darkarta po 30s".format(attempt_counter))
            time.sleep(30)

    return page


def get_dict_keys_starting_with(string, dictionary):
    for key, obj in dictionary.items():
        if key.startswith(string):
            return obj

    raise Exception(f'{string} nerasta js objekte')

def get_quantity(page, sku):
    js = re.search("window.__HYDRATION_STATE__=(.*?)</script>", page.text)

    if not js:
        logging.info("Js was not found on this page")
        return 

    logging.info("Js analysis started")

    js = json.loads(js.group(1))
    js = json.loads(js)

    with open('product_page_data.json', 'w') as file:
        json.dump(js,file)

    # get quantity
    quantity = 0
    try:
        js = js["apolloInitialState"]
        js = get_dict_keys_starting_with("Product:", js)

        with open('product_page_data.json', 'w') as file:
            json.dump(js,file)

        quantity = js["variations"]["totalQuantity"] 
    except:
        logging.error("Produkto puslapio duomenu gavimas. Klaida nuskaitant duomenis is produkto puslapio, js objekto: " + str(sys.exc_info()))

    return quantity

def is_not_competitors(page):
    # Assumption
    has_store_name_in_the_page = re.search('TOPS!', page.text)

    return has_store_name_in_the_page is not None


def get_price(page, sku):
    price_obj = re.search('<meta property="og:price:amount" content="(.*?)" />', page.text)
    price = 0
    try:
        if not price_obj:
            logging.info("Price was not found on this page")
            return 
    
        price = float(price_obj.group(1))

    except:
        logging.error("Produkto puslapio duomenu gavimas. Klaida gaunant kaina" + str(sys.exc_info()))

    return price
    
def get_product_information(sku):
    page = get_product_page(sku)

    # check if page that was returned is indeed item page
    if "item-" not in page.url:
        logging.error(f'Produkto puslapio duomenu gavimas. Produktas nerastas. Sku: {sku}')
        return None, None, None

    with open('product.html', 'w') as file:
        file.write(page.text)

    quantity=get_quantity(page, sku)
    price=get_price(page, sku)
    is_not_competitors_bool=is_not_competitors(page)

    return price, quantity, is_not_competitors_bool

if __name__ == "__main__":
    # get_product_information("MKO40R5MKFA1B-150", {})
    get_product_information("1224041STLRCNLAURELCANYON", {})