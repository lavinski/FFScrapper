import re
import json
import time

txt = open('response.html', 'r').read()
# with open("response.html") as file:?
    # txt = file

start = time.time()
# x = re.search("^window['__initialState_portal-slices-listing__'] =*",txt)
x = re.search("window\['__initialState_slice-pdp__'\] =(.*?)</script>", txt)
x.group(1)
print("Total scrapping time: ", (time.time() - start))

if x:
    # print(x.group(1))
    # js = json.loads(x.group(1))

    # sizes = js["productViewModel"]["sizes"]

    # print(sizes)

    f = open("sizes.json", "w")
    f.write(x.group(1))
    f.close()

# print(x.string)