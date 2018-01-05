from analysis import load_data
import numpy as np
import pickle
import json
import re


def load_models():
    with open("models/lsa.model", "rb") as inf:
        lsa = pickle.load(inf)

    with open("models/vectorizer.model", "rb") as inf:
        vectorizer = pickle.load(inf)

    return vectorizer, lsa


def load_all_data():
    try:

        with open("data_cache.pkl", "rb") as inf:
            print("loading data from cache..")
            return pickle.load(inf)
    except:
        pass

    frontex = load_data.load_frontex_raw()
    parl = load_data.load_parl_raw()
    lex = load_data.load_lex_raw()

    for doc in frontex:
        doc["source"] = "frontex"
    for doc in parl:
        doc["source"] = "parl"
    for doc in lex:
        doc["source"] = "lex"

    data = frontex + parl + lex
    for doc in data:
        doc["text"] = re.sub(r"(\\n|\n| )+", " ", " ".join(doc["text"]))

    raw_text = [d["text"] for d in data]

    with open("data_cache.pkl", "wb") as outf:
        pickle.dump((data, raw_text), outf)

    return data, raw_text


def group_data_by_years(data):
    data_by_years = {}
    for year in [2013, 2014, 2015, 2016]:
        X = [d for d in data if d["year"] == year]
        data_by_years[year] = X
    return data_by_years

if __name__ == '__main__':
    SELECTED_TOPIC_NUMS = [29, 30, 33, 41, 48, 49, 4, 5, 7]
    vectorizer, lsa = load_models()
    data, raw_text = load_all_data()

    X = vectorizer.transform(raw_text)
    X_topics = lsa.transform(X)

    documents_topic_scores = (X_topics ** 2) / (X_topics ** 2).sum(1)[:, np.newaxis]
    best_topic_indexes = documents_topic_scores.argmax(1)
    matches_selected = np.isin(best_topic_indexes, SELECTED_TOPIC_NUMS)
    selected_document_indexes = np.argwhere(matches_selected).flatten()
    selected_documents = []
    for i, doc in enumerate(data):
        if i in selected_document_indexes:
            doc["matches_topic"] = int(best_topic_indexes[i])
            selected_documents.append(doc)

    with open("docs_out.csv", "w") as outf:
        for i, doc in enumerate(selected_documents):
            outf.write("%s,%s,%s,%s\n" % (i, doc["year"], doc["source"], doc["matches_topic"]))

