import json
import os

import requests
import sys
from bs4 import BeautifulSoup
url = "http://eur-lex.europa.eu/search.html?LP_INTER_CODE_YEAR=%s&DTS_DOM=LEGAL_PROCEDURE&type=advanced&lang=en&SUBDOM_INIT=LEGAL_PROCEDURE&DTS_SUBDOM=LEGAL_PROCEDURE&page=%s"

YEARS = [2013, 2014, 2015, 2016]

def get_links(year):
    found = 0
    with open("data/lex/links_%s.txt" % year, "w") as of:
        for page in range(1, 100):
            print("%s, page %s, found %s docs" % (year, page, found))
            get = url % (str(year), str(page))
            r = requests.get(get)
            if "cannot be higher than the maximum number of pages (" in r.content.decode("utf-8"):
                break
            bs = BeautifulSoup(r.content, "lxml")
            lis = bs.find_all("li")
            for li in lis:
                if li.text.startswith("Initiating document"):
                    link = "http://eur-lex.europa.eu/" + li.find("a")["href"][1:]
                    of.write(link + "\n")
                    found += 1


def download_all(year):
    got = 0
    with open("data/lex/links_%s.txt" % year, "r") as inf:
        lines = list(inf.readlines())
        for i, line in enumerate(lines):
            if i % 10 == 0:
                print("Got %s / %s" % (i, len(lines)))
            url = line.strip()
            if not os.path.exists("data/lex/%s/plain/" % (year, )):
                os.makedirs("data/lex/%s/html/" % (year,))
                os.makedirs("data/lex/%s/metadata/" % (year,))
                os.makedirs("data/lex/%s/plain/" % (year, ))
            celex = url.split(":")[-1]
            response = requests.get(url)

            filename = celex
            bs = BeautifulSoup(response.content, "lxml")
            boxes = bs.find_all("div", {"class": "box"})
            title = ""
            for box in boxes:
                if box.text.strip().startswith("Title"):
                    title = box.text
                if box.text.strip().startswith("Text"):
                    t = box.text
                    got += 1
                    with open('data/lex/%s/html/%s.html' % (year, filename), 'wb') as f1:
                        f1.write(response.content)
                    with open('data/lex/%s/metadata/%s.html' % (year, filename), 'w') as f2:
                        f2.write(json.dumps({"link": url, "title": title}))
                    with open('data/lex/%s/plain/%s.txt' % (year, filename), 'w') as f3:
                        f3.write(json.dumps(t, indent=4))
                    break
            print(i, got)

if __name__ == '__main__':
    y = sys.argv[1]
    print("downloading %s" % y)
    download_all(y)
