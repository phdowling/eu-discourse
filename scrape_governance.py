import requests
from bs4 import BeautifulSoup
import json
import os
import subprocess

url = "http://frontex.europa.eu/about-frontex/governance-documents/%s"


def iterate_page_links():
    for p in [2013]: # , 2016, 2015, 2014]:
        print("Getting %s" % (url % p))
        r = requests.get(url % p)
        if r.status_code == 404:
            break

        soup = BeautifulSoup(r.content, "lxml")
        li = soup.find("ul", {"class": "documents-list"})

        children = li.find_all("li", {"class": "blue"}) + li.find_all("li", {"class": "green"})
        for i, child in enumerate(children):
            title = child.find("h3").text
            links = child.find_all("a")
            for link_obj in links:
                link = link_obj["href"]

                di = {
                    "year": p,
                    "title": title + "_" +link.split("/")[-1],
                    "link": "http://frontex.europa.eu" + link
                }
                yield di


def download_all():
    for di in iterate_page_links():
        year = di["year"]

        doctype = "Governance"
        filename = "-".join(di["title"].split())

        if not os.path.exists("data/%s/%s/pdf/" % (year, doctype)):
            os.makedirs("data/%s/%s/pdf/" % (year, doctype))
            os.makedirs("data/%s/%s/metadata/" % (year, doctype))
            os.makedirs("data/%s/%s/plain/" % (year, doctype))

        print("Downloading %s.." % di["link"])
        response = requests.get(di["link"])
        with open('data/%s/%s/pdf/%s' % (year, doctype, filename), 'wb') as f1:
            f1.write(response.content)

        with open('data/%s/%s/metadata/%s.json' % (year, doctype, filename), 'w') as f2:
            f2.write(json.dumps(di, indent=4))
        args1 = 'data/%s/%s/pdf/%s' % (year, doctype, filename)
        args2 = 'data/%s/%s/plain/%s.txt' % (year, doctype, filename)
        subprocess.Popen("pdftotext %s %s" % (args1, args2), shell=True)


if __name__ == '__main__':
    download_all()
