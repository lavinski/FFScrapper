import json
import requests
import re
import os 
import os.path
import logging

class StoreInformation:
    # mapping from store_id to location
    stores = {}
    is_quantity_needed = True

    def __init__(self, is_quantity_needed):
        self.load_store_information()
        self.is_quantity_needed = is_quantity_needed

    def get_information(self, store_id, product_page_url):
        country_code = ""
        sizes = {}
        store_id = str(store_id)

        if not self.is_quantity_needed and store_id in self.stores:
            # program already know were store_id is located
            # su just return
            country_code = self.stores[store_id]

        else:
            # scrape the product page to determine the stores location
            try:
                page = requests.get(product_page_url)
            except Exception:
                logging.error("Klaida nuskaitant duomenis is produkto puslapio: " + str(sys.exc_info()))

            # js = page.text.split("window['__initialState_slice-pdp__'] = ")

            # with open('response.html', 'w') as file:
                    # json.dump(page.text,file)

            # js = re.search("window\['__initialState_slice-pdp__'\] =(.*?)</script>", page.text)

            js = re.search("window.__HYDRATION_STATE__=(.*?)</script>", page.text)

            if js:
                logging.info("Js analysis started")

                js = json.loads(js.group(1))
                js = json.loads(js)

                with open('stores_t.json', 'w') as file:
                    json.dump(js,file)
            
                # senas
                # country_code = js["productViewModel"]["shippingInformations"]["details"]["default"]["countryCode"]

                if "initialStates" in js and "slice-product" in js["initialStates"] and "productViewModel" in js["initialStates"]["slice-product"]:
                    country_code = js["initialStates"]["slice-product"]["productViewModel"]["shippingInformations"]["details"]["default"]["countryCode"]

                    sizes = js["initialStates"]["slice-product"]["productViewModel"]["sizes"]

                    # with open('sizes.json', 'w') as outfile:
                        # json.dump(sizes, outfile)

                    if store_id not in self.stores:
                        self.stores[store_id] = country_code

                        self.write_store_information()

                    logging.info("Js analysis is done")
                else:
                    logging.error("ERROR reading js - initialStates not set")
                    country_code = "FF klaida"

            else:
                logging.info("Js was not found on this page")

        return {"country_id": country_code, "sizes":sizes}


    def load_store_information(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.exists('/stores.json'):
            with open(dir_path + '/stores.json', 'r') as file:
                self.stores = json.load(file)

    def write_store_information(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/stores.json', 'w') as file:
            json.dump(self.stores,file)

if __name__ == "__main__":
    storeInformation = StoreInformation(True)
    storeInformation.get_information(123, "https://www.farfetch.com/uk/shopping/men/tommy-hilfiger-stripe-detail-sneakers-item-16461341.aspx?q=16461341")