import news
import processor
import cluster
import tweets
import datetime
import json
import sys
from gensim.test.utils import datapath, get_tmpfile
from gensim.models import KeyedVectors, Word2Vec
from gensim.scripts.glove2word2vec import glove2word2vec


def main():
    E = float(sys.argv[2])

    # glove_file = datapath('glove.twitter.27B/glove.twitter.27B.200d.txt')
    # tmp_file = get_tmpfile("tweets_word2vec.txt")
    # _ = glove2word2vec(glove_file, tmp_file)
    # model = KeyedVectors.load_word2vec_format(tmp_file)
    # model.save("tweets_word2vec.model")

    # print("model completed")

    model = KeyedVectors.load("glove.twitter.27B/tweets_word2vec.model")

    news_api = news.News()
    word_processor = processor.Processor()
    tweets_api = tweets.Tweets()
    articles = news_api.process_news(news_api.retrieve_everything())

    data = []
    for line in open(sys.argv[1]):
        data.append(json.loads(line))

    all_tweets = tweets_api.process_tweets(data)

    all_tokens = []
    copied_tweets = list(all_tweets)

    for tweet in copied_tweets:
        tokens = word_processor.tweet_tokenize(tweet[0])
        if tokens == []:
            all_tweets.remove(tweet)
            continue
        all_tokens.append(tokens)

    all_clusters = []
    cluster_id = 0
    for i in range(len(all_tweets)):
        tweet = all_tweets[i]
        token = all_tokens[i]
        # first cluster
        if all_clusters == []:
            new_cluster = cluster.Cluster(
                tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)
            continue

        clustered = False

        for j in range(len(all_clusters)):
            single_cluster = all_clusters[j]
            vector = single_cluster.get_vector(False)
            # no common words between the tweet and the cluster, skip
            common_text_vector = intersection(vector["text"], token["text"])
            common_hashtag_vector = intersection(
                vector["hashtag"], token["hashtag"])
            common_url_vector = intersection(vector["url"], token["url"])
            if common_text_vector == [] and \
                    common_hashtag_vector == [] and \
                    common_url_vector == []:
                continue

            # vector = single_cluster.get_vector(True)

            new_token = {}
            new_token["text"] = token["text"]
            new_token["hashtag"] = token["hashtag"]

            # TODO: we can check if a word is in the pre-trained model by doing the following
            # for word not in new_token["text"]:
            #     if word in model.wv.vocab: # if word in model.vocab:
            #         print(word)

            similarity = model.wv.n_similarity(new_token["text"], vector["text"])
            print(similarity)

            if similarity >= E:
                # max_cluster_similarity = similarity
                # max_cluster_index = j
                single_cluster.push(tweet[0], tweet[1], token)
                clustered = True
                break

        if not clustered:
            new_cluster = cluster.Cluster(
                tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)

    print("Total number of clusters generated: %d" % (len(all_clusters)))
    cluster_sizes = [x.get_size() for x in all_clusters]
    print("The sizes of all clusters generated:")
    print(cluster_sizes)
    max_cluster_size = max(cluster_sizes)
    print("The max cluster size is: %d" % (max_cluster_size))

    F = float(sys.argv[3])
    related_news_clusters = []

    # for article in articles:
    for i in range(len(articles)):
        news_cluster_group = {}
        # max_similarity = 0
        # max_similarity_index = -1

        article = articles[i]
        text = article["title"] + article["description"]
        time = article["publish_time"]

        # for single_cluster in all_clusters:
        for j in range(len(all_clusters)):
            single_cluster = all_clusters[j]

            # Remove outlier clusters
            # if single_cluster.get_size() <= 10 or single_cluster.is_clustered:
            if single_cluster.get_size() <= 10:
                continue

            cluster_vector = single_cluster.get_vector(True)["text"]
            similarity = word_processor.docs_similarity(text, cluster_vector)
            similarity = word_processor.modified_similarity(
                similarity, time, single_cluster, True)

            # if similarity >= F and similarity > max_similarity:
            if similarity >= F:
                # max_similarity = similarity
                # max_similarity_index = j
                # The news is related to this cluster
                news_cluster_group["article"] = i
                news_cluster_group["cluster"] = single_cluster.get_id()
                related_news_clusters.append(news_cluster_group)
                # stop comparing with other clusters
                break

        # if max_similarity_index == -1:
        #     continue
        # news_cluster_group["article"] = i
        # news_cluster_group["cluster"] = max_similarity_index
        # related_news_clusters.append(news_cluster_group)
        # all_clusters[max_similarity_index].change_clustered()

    counter = {}
    for item in related_news_clusters:
        if item["cluster"] not in counter:
            counter[item["cluster"]] = 1
        else:
            counter[item["cluster"]] += 1

    # most_related_cluster = max(counter.items(), key=operator.itemgetter(1))[0]
    print("Number of pairs generated in total: %d" %
          (len(related_news_clusters)))
    print("All generated pairs:")
    print(related_news_clusters)


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


if __name__ == "__main__":
    main()
