from collections import defaultdict

from analysis import load_data
import numpy as np
import pickle
import json
import re
import string

YEARS = [2013, 2014, 2015, 2016]
SOURCES = ["frontex", "parl", "lex"]

SEPARATOR = "."

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


def select_documents_for_topics(X_topics, topic_nums):
    documents_topic_scores = (X_topics ** 2) / (X_topics ** 2).sum(1)[:, np.newaxis]
    best_topic_indexes = documents_topic_scores.argmax(1)
    matches_selected = np.isin(best_topic_indexes, topic_nums)
    selected_document_indexes = np.argwhere(matches_selected).flatten()
    selected_documents = []
    for i, doc in enumerate(data):
        if i in selected_document_indexes:
            doc["matches_topic"] = int(best_topic_indexes[i])
            selected_documents.append(doc)
    return selected_documents


def count_words(texts, words=None):
    counts = defaultdict(int)
    total = 0
    for text in texts:
        for word in text.split():
            if words is None or word in words:
                counts[word] += 1
            total += 1
    return counts, total


def compute_word_count_breakdown(data, words=None):
    res = defaultdict(dict)
    for year in YEARS:
        for source in SOURCES:
            data_part = [d["text"] for d in data if d["source"] == source and d["year"] == year]
            word_counts, total = count_words(data_part, words)
            print("Source %s has %s words in year %s" % (source, total, year))
            res[year][source] = (word_counts, total)
    return res

def breakdown_by_year_only(data, words=None):
    res = defaultdict(dict)
    for year in YEARS:
        data_part = [d["text"] for d in data if d["year"] == year]
        word_counts, total = count_words(data_part, words)
        res[year] = (word_counts, total)
    return res

def compute_probabilites(words, data_global, data_filtered):
    global_counts, total_global = count_words([d["text"] for d in data_global], words)
    filtered_counts, total_filtered = count_words([d["text"] for d in data_filtered], words)

    p_global = {word: global_counts[word] / total_global for word in global_counts.keys()}
    p_filtered = {word: filtered_counts[word] / total_filtered for word in global_counts.keys()}

    print("Changes in word probabilities from all data to subselected data:")
    for word in words:
        p_f = p_filtered[word]
        p_g = p_global[word]
        if p_f > p_g:
            print("%s: %s -> %s. Increase by factor %.8s" % (word, str(p_g), p_f, p_f / p_g))
        else:
            print("%s: %s -> %s. Decrease by factor %.8s" % (word, str(p_g), p_f, p_g / p_f))


def output_probs_table(filename, table):
    with open(filename, "w") as outf:
        outf.write("sep=;\n")
        for word in table:
            outf.write("%s;%s\n" % (word, ";".join(map(str,table[word])).replace(".", SEPARATOR)))


def probability_breakdown_by_year(words, data):
    # all_counts, total_words = count_words([d["text"] for d in data], words)
    # p_word = {word: all_counts[word] / total_words for word in all_counts.keys()}
    breakdowns = compute_word_count_breakdown(data, words)

    source_background_word_counts = {}
    source_total_word_counts = defaultdict(int)
    for source in SOURCES:
        source_background_word_counts[source] = {
            word: sum([breakdowns[year][source][0][word] for year in YEARS]) for word in words
        }
        source_total_word_counts[source] = sum([breakdowns[year][source][1] for year in YEARS])

    final_res_probs = defaultdict(list)
    final_res_supps = defaultdict(list)
    frontex_res_probs = defaultdict(list)
    parl_res_probs = defaultdict(list)
    lex_res_probs = defaultdict(list)

    for year in YEARS:
        # total_words_in_year = sum([breakdowns[year][source][1] for source in SOURCES])
        print("%s" % year)
        word_Ps = defaultdict(list)
        word_supports = defaultdict(list)

        for source in SOURCES:
            source_word_counts_for_year, source_total_for_year = breakdowns[year][source]

            # source_prob_year = source_total_for_year / total_words_in_year
            # print("\tSource: %s. Source probability in year: %s" % (source, source_prob_year))

            for word in words:
                freq_here = source_word_counts_for_year[word]
                p_here = freq_here / source_total_for_year

                word_supports[word].append(freq_here)
                word_Ps[word].append(p_here)

        for word in word_Ps:
            # bg_word_count = source_background_word_counts[source][word]
            # if bg_word_count == 0:
            #     bg_word_count = 1
            # background_p = bg_word_count / source_total_word_counts[source]
            # change_percentage = (p_here - background_p) / background_p * 100

            word_probs = word_Ps[word]
            avg_change = sum(word_probs) / len(word_probs) * 100
            total_support = sum(word_supports[word])
            final_res_probs[word].append(avg_change)
            final_res_supps[word].append(total_support)
            frontex_res_probs[word].append(word_probs[0])
            parl_res_probs[word].append(word_probs[1])
            lex_res_probs[word].append(word_probs[2])
            print("\t%s: Vals: %s. Avg. prob is %.8s%% (support %s)" % (word, word_probs, avg_change, total_support))

    output_probs_table("averaged_word_probs.csv", final_res_probs)
    output_probs_table("word_supports.csv", final_res_supps)
    output_probs_table("frontex_word_probs.csv", frontex_res_probs)
    output_probs_table("parl_word_probs.csv", parl_res_probs)
    output_probs_table("lex_word_probs.csv", lex_res_probs)


def get_typical_contexts(data, words, window=10, minsup=5):
    all_importances = {}
    translator = str.maketrans('', '', string.punctuation)

    for year in YEARS:
        data_this_year = [d for d in data if d["year"] == year]
        text_this_year = [d["text"].translate(translator) for d in data_this_year]

        # step 1: count context words
        all_context_words = set()
        context_otherword_counts = {word: defaultdict(int) for word in words}
        for word in words:
            for text in text_this_year:
                t = text.lower().split()
                try:
                    i = t.index(word)
                except:
                    continue
                context = t[max(i-window, 0):min(i+window, len(t))]
                for other_word in context:
                    context_otherword_counts[word][other_word] += 1
                    all_context_words.add(other_word)

        # step 2: count base rates for other words
        other_counts, total_words_this_year = count_words(text_this_year, all_context_words)
        for other_word in list(other_counts.keys()):
            if other_counts[other_word] < minsup or len(other_word) > 25 or all([letter in "0123456789" for letter in other_word]):
                del other_counts[other_word]
        importances = {}
        for word in words:
            p_other_given_w = {
                other_word:
                    context_otherword_counts[word][other_word] /  # number of times this word occurs in w context
                    sum(context_otherword_counts[word].values())  # total number of words in w contexts
                for other_word in other_counts
            }
            importance_for_w = {
                other_word:
                    p_other_given_w[other_word]  # the conditional probability of the other word if we see our word
                    / (other_counts[other_word] / total_words_this_year)  # the prior probability of the other word
                for other_word in other_counts
            }
            importances[word] = importance_for_w
        all_importances[year] = importances

    for word in words:
        print(word)
        for year in YEARS:
            importance_for_w = all_importances[year][word]
            print(
                "\t%s: %s" % (
                    year,
                    ", ".join(
                        [
                            "%s(%s)" % (other_word, int(importance))
                            for (other_word, importance)
                            in sorted(importance_for_w.items(), key=lambda item: -item[1])[:10]
                        ]
                    )
                )
            )

    with open("contexts.csv", "w") as outf:
        outf.write("sep=;\n")
        for word in words:
            outf.write(
                "%s;%s\n" % (
                    word,
                    ";".join(
                        ["%s;" % year for year in YEARS]
                    )
                )
            )

            for top in range(30):
                row_data = [
                    list(sorted(
                        all_importances[year][word].items(), key=lambda item: -item[1]
                    ))[top]
                    for year in YEARS
                ]
                linestr = ";".join(
                    ["%s;%s" % (other_word, str(importance).replace(".", SEPARATOR)) for (other_word, importance) in row_data]
                )
                outf.write("%s;%s\n" % (top, linestr))

            outf.write("\n")


def examine_contexts(word_pairs, data, year, window=10, full=False):
    translator = str.maketrans('', '', string.punctuation)
    data_this_year = [d for d in data if d["year"] == year]
    text_this_year = [d["text"].translate(translator) for d in data_this_year]
    for word1, word2 in word_pairs:
        print((word1, word2))
        for text, doc in zip(text_this_year, data_this_year):
            t = text.lower().split()
            try:
                i = t.index(word1)
            except:
                continue
            context = t[max(i - window, 0):min(i + window, len(t))]
            if word2 in context:
                if full:
                    print("\t%s: %s (%s)" % (doc["source"], " ".join(context), " ".join(doc["title"].split())))
                    print(doc)
                else:
                    print("\t%s: %s (%s)" % (doc["source"], " ".join(context), " ".join(doc["title"].split())))

if __name__ == '__main__':
    SELECTED_TOPIC_NUMS = [29, 30, 33, 41, 48, 49, 4, 5, 7]
    WORDS = ["visa", "border", "asylum", "protection", "relocation", "security", "illegal", "territory", "external",
             "crossing", "migrants", "entry", "irregular", "land", "flow"]
    data, raw_text = load_all_data()

    try:
        with open("examine.pkl", "rb") as inf:
            (X, X_topics) = pickle.load(inf)
    except:
        vectorizer, lsa = load_models()
        X = vectorizer.transform(raw_text)
        X_topics = lsa.transform(X)
        with open("examine.pkl", "wb") as outf:
            pickle.dump((X, X_topics), outf)

    data_subselected = select_documents_for_topics(X_topics, SELECTED_TOPIC_NUMS)
    get_typical_contexts(data_subselected, words=WORDS)
    compute_probabilites(WORDS, data, data_subselected)
    probability_breakdown_by_year(WORDS, data_subselected)
    pairs = [
        ("illegal", "body"),
        ("territory","expulsion"),
        ("territory", "dynamic"),
        ("protection", "exploitation"),
        ("protection", "peace"),
        ("security", "freedom"),
        ("security", "biometrics"),
        ("migrants", "fingerprint"),
        ("migrants", "monitor")
    ]
    examine_contexts(pairs, data_subselected, 2016)
    examine_contexts([("migrants", "countermeasures")], data_subselected, 2015)
    examine_contexts([("illegal", "arms")], data_subselected, 2015, full=True)

    # with open("docs_out.csv", "w") as outf:
    #     for i, doc in enumerate(data_subselected):
    #         outf.write("%s,%s,%s,%s\n" % (i, doc["year"], doc["source"], doc["matches_topic"]))



