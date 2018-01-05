import pickle
from operator import itemgetter

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from analysis import load_data
from collections import defaultdict
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD


def simple_full_wordcount(sent_stream):
    counter = defaultdict(int)
    total = 0
    for sent in sent_stream:
        for word in sent:
            counter[word.lower()] += 1
            total += 1

    return list(reversed(sorted(counter.items(), key=itemgetter(1)))), total


def print_top_words(model, feature_names, n_top_words):
    for topic_idx, (topic, e_var) in enumerate(zip(model.components_, model.explained_variance_ratio_)):
        message = "Topic #%d (%.6s): " % (topic_idx, e_var)
        message += ", ".join(
            ["%s (%.4s)" % (feature_names[i], topic[i]) for i in topic.argsort()[:-n_top_words - 1:-1]]
        )
        print(message)
        print()
    print()


def preprocess_data(docs, tfidf=True):
    if tfidf:
        vectorizer = TfidfVectorizer(
            max_df=0.75, min_df=2,
            stop_words=STOPWORDS,
            # stop_words='english'
            ngram_range=(1, 2)
        )
    else:
        vectorizer = CountVectorizer(
            max_df=0.75, min_df=2,
            stop_words=STOPWORDS,
            # stop_words = 'english',
            ngram_range=(1, 2)
        )
    X = vectorizer.fit_transform(docs)
    return X, vectorizer


def train_topic_model(X, vectorizer, model="lda", n_topics=8):
    if model == "lda":
        model = LatentDirichletAllocation(
            n_topics=n_topics, max_iter=5, learning_method='online', learning_offset=50., random_state=0
        )
    elif model == "lsa":
        model = TruncatedSVD(n_components=n_topics, algorithm="arpack")

    X_t = model.fit_transform(X)

    print("\nTopics:")
    tf_feature_names = vectorizer.get_feature_names()
    print_top_words(model, tf_feature_names, 100)
    return model, X_t

STOPWORDS = [
    "u00d5",  "u00d6", "u2026", "n0",
    "u2026", "u0435", "u043e", "u2026", "u2026", "u0430", "u0438", "u03b1", "u043d", "u00a0", "u03b9", "u03b5", "u03bf",
    "u03bd", "u0442", "u00a0", "u00ea", "u0440", "u03c4", "u2013", "u03c4"
    "2010", "2011", "2012", "2013", "2014", "2015", "2016", "00", "000"
]
if __name__ == '__main__':

    model_name = "lsa"

    frontex = load_data.load_frontex_raw()
    parl = load_data.load_parl_raw()
    lex = load_data.load_lex_raw()
    print("Got %s documents from frontex" % len(frontex))
    print("Got %s documents from lex" % len(lex))
    print("Got %s documents from parl" % len(parl))

    print("By year:")
    for year in [2013, 2014, 2015, 2016]:
        print(year)
        print("Frontex: %s" % len([d for d in frontex if d["year"] == year]))
        print("Parl: %s" % len([d for d in parl if d["year"] == year]))
        print("Lex: %s" % len([d for d in lex if d["year"] == year]))

    docs = [" ".join(doc["text"]) for doc in frontex + parl + lex]
    print(len(docs))
    X, vectorizer = preprocess_data(docs, tfidf=True)

    with open("models/vectorizer.model", "wb") as outf:
        pickle.dump(vectorizer, outf)

    topic_model, X_t = train_topic_model(X, model=model_name, vectorizer=vectorizer, n_topics=50)

    with open("models/%s.model" % model_name, "wb") as outf:
        pickle.dump(topic_model, outf)


    # sent_stream = (word_tokenize(sent) for doc in data for sent in doc["text"])

    # sent_ngram_stream = ([" ".join(x) for x in sent + ngrams(sent, 2) + ngrams(sent, 3)] for sent in sent_stream)
    # counts, total = simple_full_wordcount(sent_stream)
    # print(counts[:200])
    # print(total)
    # input()
    # counts, total = simple_full_wordcount(sent_ngram_stream)
    # print(counts[:200])
    # print(total)

