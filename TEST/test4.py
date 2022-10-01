# import re

# name = "burakhan Şamlıüğğğ^^'!^412424445656867978089*894552(/)=()=&%/+&^+-:;,.?*+$#`"
# name = name.encode('ascii', 'ignore').decode("utf-8")
# filteredName = re.sub(r'\W+', '', name)

# print(name)
# print(filteredName+"son")


import logging
logging.basicConfig(format='%(levelname)s - %(asctime)s => %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.NOTSET)

logging.info("a")