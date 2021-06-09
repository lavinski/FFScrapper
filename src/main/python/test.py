import sys
try:
    with open("/home/tomas/Dowloands") as csvfile:
        ff_data = csv.reader(csvfile,delimiter=";")
        for row in ff_data:
            # if child id exists
            if row[1]:
                pass

except:
    print(str(sys.exc_info()))
