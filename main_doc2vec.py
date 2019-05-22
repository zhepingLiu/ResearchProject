import news
import processor
import cluster
import tweets
import datetime
import json
import sys
from doc2vec_model import Doc2VecModel
from gensim.models.doc2vec import Doc2Vec
from scipy import spatial
import time

def main():
    E = float(sys.argv[2])
    # model = Doc2Vec.load("./enwiki_dbow/doc2vec.bin")
    # print("Starts loading the model.")
    doc2vec_model = Doc2VecModel()
    model = doc2vec_model.get_model()
    # print("Model loaded.")
    word_processor = processor.Processor()
    tweets_api = tweets.Tweets(int(sys.argv[4]))

    # print("Starts loading the dataset")
    all_tweets = tweets_api.process_tweets(sys.argv[1])
    # print("Dataset loaded")

    all_tokens = []
    copied_tweets = list(all_tweets)

    for tweet in copied_tweets:
        tokens = word_processor.tweet_tokenize(tweet[0])

        if tokens == []:
            all_tweets.remove(tweet)
            continue
        all_tokens.append(tokens)

    # print("pre-processing completed")

    all_clusters = []
    cluster_id = 0
    for i in range(len(all_tweets)):
        # start_total = time.time()
        # first cluster
        if all_clusters == []:
            tweet = all_tweets[i]
            token = all_tokens[i]
            new_cluster = cluster.Cluster(
                tweet[0], tweet[1], token, cluster_id, True, model)
            cluster_id += 1
            all_clusters.append(new_cluster)
            continue

        clustered = False
        # print("Starts clustering %d" % (i))
        token = all_tokens[i]
        for j in range(len(all_clusters)):
            vector = all_clusters[j].get_vector(False)
            # no common words between the tweet and the cluster, skip
            if not intersection(vector["text"], token["text"]) and \
                not intersection(vector["hashtag"], token["hashtag"]):
                continue

            # vector = single_cluster.get_vector(True)
            new_token = {}
            new_token["text"] = token["text"]
            new_token["hashtag"] = token["hashtag"]

            # cluster_dbow_vector = model.infer_vector(vector["text"])
            # similarity = spatial.distance.cosine(tweet_dbow_vector, cluster_dbow_vector)
            # similarity = 1 - similarity
            # if all_text_in_cluster(new_token["text"], vector["text"]):
            #     similarity = 1
            # else:
            #     tweet_dbow_vector = model.infer_vector(new_token["text"])
            #     similarity = word_processor.doc2vec_double_similarity(new_token, vector, tweet_dbow_vector, all_clusters[j])
            tweet_dbow_vector = model.infer_vector(new_token["text"])
            similarity = word_processor.doc2vec_double_similarity(
                new_token, vector, tweet_dbow_vector, all_clusters[j])

            if similarity >= E:
                tweet = all_tweets[i]
                all_clusters[j].push(tweet[0], tweet[1], token)
                clustered = True
                break

        if not clustered:
            # start_new_cluster = time.time()
            tweet = all_tweets[i]
            token = all_tokens[i]
            new_cluster = cluster.Cluster(tweet[0], tweet[1], token, cluster_id, True, model)
            cluster_id += 1
            all_clusters.append(new_cluster)
            # print("New cluster duration: %s" %
            #       (time.time() - start_new_cluster))

        # print("Total time: %s" % (time.time() - start_total))
        # print("Clustering completed %d" % (i))

    print("Total number of clusters generated: %d" % (len(all_clusters)))
    cluster_sizes = [x.get_size() for x in all_clusters]
    print("The sizes of all clusters generated:")
    print(cluster_sizes)
    max_cluster_size = max(cluster_sizes)
    print("The max cluster size is: %d" % (max_cluster_size))

    news_api = news.News()
    articles = news_api.process_news(news_api.retrieve_everything())
    F = float(sys.argv[3])
    related_news_clusters = []

    # for article in articles:
    for i in range(len(articles)):
        news_cluster_group = {}
        # max_similarity = 0
        # max_similarity_index = -1

        article = articles[i]
        text = article["title"] + article["description"]
        publish_time = article["publish_time"]

        # for single_cluster in all_clusters:
        for j in range(len(all_clusters)):
            single_cluster = all_clusters[j]

            # Remove outlier clusters
            if single_cluster.get_size() < 10:
                continue
            # print("Article %d, Cluster %d." % (i, j))
            cluster_vector = single_cluster.get_vector(True)["text"]
            if not intersection(cluster_vector, text):
                continue
            similarity = word_processor.docs_similarity(text, cluster_vector)
            similarity = word_processor.modified_similarity(
                similarity, publish_time, single_cluster, True)

            if similarity >= F:
                news_cluster_group["article"] = i
                news_cluster_group["cluster"] = single_cluster.get_id()
                news_cluster_group["similarity"] = similarity
                related_news_clusters.append(news_cluster_group)
                # stop comparing with other clusters
                break

    print("Number of pairs generated in total: %d" %
          (len(related_news_clusters)))
    print("All generated pairs:")
    print(related_news_clusters)

    for related_pair in related_news_clusters:
        print("News below")
        article_id = related_pair["article"]
        print(articles[article_id])
        cluster_id = related_pair["cluster"]
        print("Tweets below:")
        for k in range(len(all_clusters[cluster_id].get_all_tweets())):
            print("[%d]: %s: " %
                  (k, all_clusters[cluster_id].get_all_tweets()[k]))
        print("----------------------------------------------------")

def intersection(lst1, lst2):
    return bool(set(lst1) & set(lst2))

def all_text_in_cluster(doc1, doc2):
    for tweet_word in doc1:
        if tweet_word not in doc2:
            return False

    return True


if __name__ == "__main__":
    main()
