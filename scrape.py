import requests
from bs4 import BeautifulSoup
import json
import os
import subprocess

url = "http://frontex.europa.eu/publications/?p=%s"


def iterate_page_links():
    p = 1
    while True:
        print("Getting %s" % (url % p))
        r = requests.get(url % p)
        if r.status_code == 404:
            break

        soup = BeautifulSoup(r.content, "lxml")
        li = soup.find("ul", {"class": "publications-list"})
        children = li.find_all("li")
        for i, child in enumerate(children):
            doctype = child.find("a", {"class": "type"}).text
            time = child.find("time").text
            title = child.find("h3").text
            detail = child.find("p").text
            link = child.find("div", {"class": "publications-downloads"}).find("a")["href"]
            di = {
                "type": doctype,
                "date": time,
                "title": title,
                "detail": detail,
                "link": "http://frontex.europa.eu" + link
            }
            yield di
        p += 1


def filter_all():
    pl = list(iterate_page_links())
    print("TOTAL: %s" % len(pl))
    fil = [p for p in pl if p["link"].endswith(".pdf")]
    print("PDF: %s" % len(fil))
    fil2 = [p for p in pl if p["date"].split("-")[0] in ["2013", "2014", "2015", "2016"]]
    print("2013 - 2016: %s" % len(fil2))
    return fil2


def download_all():
    for di in filter_all():
        year = di["date"].split("-")[0]

        doctype = "-".join(di["type"].split())
        filename = "-".join(di["title"].split())

        filename += "_" + di["date"]

        print("Downloading %s.." % di["link"])
        response = requests.get(di["link"])
        filename = filename.replace("(", "").replace(")", "")

        if not os.path.exists("data/%s/%s/pdf/" % (year, doctype)):
            os.makedirs("data/%s/%s/pdf/" % (year, doctype))
            os.makedirs("data/%s/%s/metadata/" % (year, doctype))
            os.makedirs("data/%s/%s/plain/" % (year, doctype))

        with open('data/%s/%s/pdf/%s.pdf' % (year, doctype, filename), 'wb') as f1:
            f1.write(response.content)

        with open('data/%s/%s/metadata/%s.json' % (year, doctype, filename), 'w') as f2:
            f2.write(json.dumps(di, indent=4))

        args1 = 'data/%s/%s/pdf/%s.pdf' % (year, doctype, filename)
        args2 = 'data/%s/%s/plain/%s.txt' % (year, doctype, filename)
        subprocess.Popen("pdftotext %s %s" % (args1, args2), shell=True)


if __name__ == '__main__':
    download_all()
