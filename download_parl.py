import sys
from bs4 import BeautifulSoup
import os
import requests
import json
import subprocess

xml_filename = "data/parl/printresultlist_%s.xml"
pdf_url = "http://www.europarl.europa.eu/oeil/popups/printficheglobal.pdf?reference=%s"



def iterate_fileinfos(year):
    all_items = []
    filen = xml_filename % year
    with open(filen) as inf:
        bs = BeautifulSoup(inf, "lxml")
        items = bs.find_all(name="item")
        for item in items:
            item_dict = {
                "ref": item.find("reference").text,
                "title": item.find("title").text,
                "year": year
            }
            all_items.append(item_dict)
    print("Found a total of %s documents." % len(all_items))
    return all_items


def download_all(y):
    for i, fi in enumerate(iterate_fileinfos(y)):
        if i % 20 == 0:
            print(i)
        year = fi["year"]
        if not os.path.exists("data/parl/%s/pdf/" % (year, )):
            os.makedirs("data/parl/%s/pdf/" % (year, ))
            os.makedirs("data/parl/%s/metadata/" % (year,))
            os.makedirs("data/parl/%s/plain/" % (year, ))

        response = requests.get(pdf_url % fi["ref"])
        filename = fi["ref"] + "_%s" % i
        filename = filename.replace("/", "_")
        with open('data/parl/%s/pdf/%s.pdf' % (year, filename), 'wb') as f1:
            f1.write(response.content)

        with open('data/parl/%s/metadata/%s.json' % (year, filename), 'w') as f2:
            f2.write(json.dumps(fi, indent=4))


def convert_all(year):
    files = os.listdir("data/parl/%s/pdf" % year)
    for i, filename in enumerate(files):
        print("%s / %s" % (i, len(files)))
        args1 = "'data/parl/%s/pdf/%s'" % (year, filename)
        args2 = "'data/parl/%s/plain/%s.txt'" % (year, filename)
        subprocess.Popen("pdftotext %s %s" % (args1, args2), shell=True)


if __name__ == '__main__':
    y = sys.argv[1]
    # print("downloading %s" % y)
    # download_all(y)
    for y in [2013, 2014, 2015, 2016]:
        print("converting %s" % y)
        convert_all(y)
