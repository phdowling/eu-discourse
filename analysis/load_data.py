import json
import os


def check_line(line):
    if len(line) >= 20:
        return True
    return False


def load_frontex_raw():
    all_data = []
    for year in [2013, 2014, 2015, 2016]:
        for subdir in os.listdir("data/frontex/%s/" % year):
            pdf_directory = "data/frontex/%s/%s/pdf" % (year, subdir)
            plain_directory = "data/frontex/%s/%s/plain" % (year, subdir)
            meta_directory = "data/frontex/%s/%s/metadata" % (year, subdir)
            for filename in os.listdir(pdf_directory):
                file_lines = []
                if os.path.exists(plain_directory+ "/" + filename + ".txt"):
                    plainpath = plain_directory+ "/" + filename + ".txt"
                    metapath = meta_directory + "/" + filename + ".json"
                else:
                    plainpath = plain_directory + "/" + filename[:-4] + ".txt"
                    metapath = meta_directory + "/" + filename[:-4] + ".json"
                with open(plainpath) as inf:
                    for line in inf:
                        if check_line(line):
                            file_lines.append(line)

                with open(metapath) as inf:
                    doc = json.load(inf)
                    doc["text"] = file_lines
                    doc["year"] = year

                all_data.append(doc)
    return all_data


def load_lex_raw():
    all_data = []
    for year in [2013, 2014, 2015, 2016]:
        plain_directory = "data/lex/%s/plain" % (year,)
        meta_directory = "data/lex/%s/metadata" % (year,)
        for filename in os.listdir(plain_directory):
            file_lines = []
            plainpath = plain_directory + "/" + filename
            metapath = meta_directory + "/" + filename.replace("txt", "html")
            with open(plainpath) as inf:
                for line in inf:
                    if check_line(line):
                        file_lines.append(line)
            with open(metapath) as inf:
                doc = json.load(inf)
                doc["text"] = file_lines
                doc["year"] = year
            all_data.append(doc)
    return all_data


def load_parl_raw():
    all_data = []
    for year in [2013, 2014, 2015, 2016]:
        plain_directory = "data/parl/%s/plain" % (year,)
        meta_directory = "data/parl/%s/metadata" % (year,)
        for filename in os.listdir(plain_directory):
            file_lines = []
            plainpath = plain_directory + "/" + filename
            metapath = meta_directory + "/" + filename.replace(".pdf.txt", ".json")
            with open(plainpath) as inf:
                for line in inf:
                    if check_line(line):
                        file_lines.append(line)
            with open(metapath) as inf:
                doc = json.load(inf)
                doc["text"] = file_lines
                doc["year"] = year
            all_data.append(doc)
    return all_data