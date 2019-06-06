from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from datetime import datetime, date
import math
import re
from scipy import spatial

class Processor:
    
    def __init__(self, enable_hashtag_similarity):
        self.stemmer = PorterStemmer()
        self.tfidfVectorizer = TfidfVectorizer(
            tokenizer=self.tweet_text_tokenizer, stop_words="english")
        self.non_doc_tfidfVectorizer = TfidfVectorizer(
            stop_words=None, preprocessor=self.do_nothing_pre_processor)
        self.hashtag_index = 0
        self.text_index = 0
        self.enable_hashtag_similarity = enable_hashtag_similarity

    # tokenize sentences
    def sentences_tokenize(self, doc):
        sentences = sent_tokenize(doc)
        return sentences

    # remove stop words
    # remove punctuations
    # stem words
    # lowercase all words
    # tokenize words
    def words_tokenize(self, doc):
        tokenizer = RegexpTokenizer(r'\w+')
        stop_words = set(stopwords.words('english'))
        words_tokens = tokenizer.tokenize(doc)
        filtered_words = [w for w in words_tokens if not w in stop_words]

        processed_words = []
        for words in filtered_words:
            processed_words.append(self.stemmer.stem(words).lower())

        return processed_words

    def tweet_tokenize(self, tweet):
        tokens = {}
        # remove the @username in the twitter text
        tweet = re.sub(r"@\S+", "", tweet)
        
        # extract urls and hashtags
        urls = re.findall(r"(?P<url>https?://[^\s]+)", tweet)
        hashtags = re.findall(r"#(\w+)", tweet)

        # lowercase all hashtags
        hashtags = [x.lower() for x in hashtags]

        if "auspol" in hashtags:
            hashtags.remove("auspol")

        # remove the hashtags and urls in the tweet
        if urls != []:
            tweet = re.sub(r"(?P<url>https?://[^\s]+)", "", tweet)
        if hashtags != []:
            tweet = re.sub(r"#(\w+)", "", tweet)

        # remove first word "RT" and the second word [username]
        tokens["text"] = self.words_tokenize(tweet)[1:]
        if "auspol" in tokens["text"]:
            tokens["text"].remove("auspol")
        tokens["url"] = urls
        tokens["hashtag"] = hashtags
        return tokens

    def tweet_text_tokenizer(self, tweet):
        tweet = re.sub(r"@\S+", "", tweet)
        tweet = re.sub(r"(?P<url>https?://[^\s]+)", "", tweet)
        tweet = re.sub(r"#(\w+)", "", tweet)
        return self.words_tokenize(tweet)[1:]


    def tfidf(self, docs):
        vectorizer = CountVectorizer()
        transformer = TfidfTransformer()

        keywords_frequency = vectorizer.fit_transform(docs)
        keywords = vectorizer.get_feature_names()
        tfidf = transformer.fit_transform(keywords_frequency)

        return tfidf

    def dot_product(self, v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    def magnitude(self, vector):
        return math.sqrt(self.dot_product(vector, vector))

    # TODO: v1 and v2 must have the SAME keywords for calculating the similarity
    def similarity(self, v1, v2):
        return self.dot_product(v1, v2) / (self.magnitude(v1) * self.magnitude(v2) + .00000001)

    def docs_similarity(self, doc1, doc2):
        documents = [doc1, doc2]
        tfidf = self.tfidfVectorizer.fit_transform(documents)
        similarity = (tfidf * tfidf.T).A
        return similarity[0, 1]

    def not_docs_similarity(self, vector1, vector2):
        vectors = [vector1, vector2]
        tfidf = self.non_doc_tfidfVectorizer.fit_transform(vectors)
        similarity = tfidf * tfidf.T
        return (similarity.A)[0, 1]

    def hashtag_url_similarity(self, vector, cluster_vector):
        similar = bool(set(vector) & set(cluster_vector))
        
        return similar

    def do_nothing_pre_processor(self, vector):
        return vector

    def modified_similarity(self, similarity, tweet_time, cluster, is_initial=False):

        if not is_initial:
            time_centroid = cluster.time_centroid
        else:
            time_centroid = cluster.initial_time

        time = tweet_time - time_centroid
        time = time.days

        variance = cluster.compute_time_variance()
        gaussian_parameter = math.exp(-(time * time) / 2 * variance)

        return similarity * gaussian_parameter

    # TODO: if there is a match url/hashtag in the cluster, give it a score of 1
    #       this should also avoid the current problem of EMPTY VOCABULARY
    # NOTICE: doc1["hashtag"] and doc1["url"] are now lists not str
    def new_triple_similarity(self, doc1, doc2):
        if self.enable_hashtag_similarity:
            if doc1["hashtag"] != [] and doc2["hashtag"] != []:
                hashtag_similar = self.hashtag_url_similarity(doc1["hashtag"], doc2["hashtag"])
        else:
            hashtag_similar = False

        text_similarity = self.docs_similarity(doc1["text"], doc2["text"])
        if hashtag_similar:
            return 0.2 + text_similarity
        else:
            return text_similarity

    def doc2vec_double_similarity(self, doc1, doc2, tweet_dbow_vector, cluster):
        if doc1["hashtag"] != [] and doc2["hashtag"] != []:
            hashtag_similar = self.hashtag_url_similarity(
                doc1["hashtag"], doc2["hashtag"])
        else:
            hashtag_similar = False

        if hashtag_similar:
            return 1
        else:
            cluster_dbow_vector = cluster.get_doc2vec_vector()
            similarity = spatial.distance.cosine(
                tweet_dbow_vector, cluster_dbow_vector)
            similarity = 1 - similarity

            return similarity

    def text_hashtag_url_similarity(self, alpha, beta, gamma, doc1, doc2):
        if beta != 0 and gamma != 0:
            text_similarity = self.docs_similarity(doc1["text"], doc2["text"])
            if doc2["hashtag"] != "" and doc2["url"] != "":
                hashtag_similarity = self.not_docs_similarity(doc1["hashtag"], doc2["hashtag"])
                url_similarity = self.not_docs_similarity(doc1["url"], doc2["url"])
                return alpha * text_similarity + beta * hashtag_similarity + gamma * url_similarity
            else:
                return text_similarity
        elif beta != 0 and gamma == 0:
            text_similarity = self.docs_similarity(doc1["text"], doc2["text"])
            if doc2["hashtag"] != '':
                hashtag_similarity = self.not_docs_similarity(
                    doc1["hashtag"], doc2["hashtag"])
                return alpha * text_similarity + beta * hashtag_similarity
            else:
                return text_similarity
        elif beta == 0 and gamma != 0:
            text_similarity = self.docs_similarity(doc1["text"], doc2["text"])
            if not doc2["url"] == []:
                url_similarity = self.not_docs_similarity(doc1["url"], doc2["url"])
                return alpha * text_similarity + gamma * url_similarity
            else:
                return text_similarity
        else:
            text_similarity = self.docs_similarity(doc1["text"], doc2["text"])
            return text_similarity
