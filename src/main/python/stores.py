import json
import requests
import re
import os 

class StoreInformation:
    # mapping from store_id to location
    stores = {}
    is_quantity_needed = True

    def __init__(self, is_quantity_needed):
        self.load_store_information()
        self.is_quantity_needed = is_quantity_needed
        print(self.stores)

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
            page = requests.get(product_page_url)
            
            # js = page.text.split("window['__initialState_slice-pdp__'] = ")

            # with open('response.html', 'w') as file:
                    # json.dump(page.text,file)

            js = re.search("window\['__initialState_slice-pdp__'\] =(.*?)</script>", page.text)

            if js:
                print("Js")
                js = json.loads(js.group(1))

                # with open('stores_t.json', 'w') as file:
                    # json.dump(js,file)

                country_code = js["productViewModel"]["shippingInformations"]["details"]["default"]["countryCode"]

                sizes = js["productViewModel"]["sizes"]

                # with open('sizes.json', 'w') as outfile:
                    # json.dump(sizes, outfile)

                if store_id not in self.stores:
                    self.stores[store_id] = country_code

                    self.write_store_information()

                # quantity = 

            else:
                print("No js")

        return {"country_id": country_code, "sizes":sizes}


    def load_store_information(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/stores.json', 'r') as file:
            self.stores = json.load(file)

    def write_store_information(self):
        with open(dir_path + '/stores.json', 'w') as file:
            json.dump(self.stores,file)

if __name__ == "__main__":
    storeInformation = StoreInformation()
    storeInformation.get_store_location(123, "https://www.farfetch.com/uk/shopping/men/tommy-hilfiger-stripe-detail-sneakers-item-16461341.aspx?q=16461341")