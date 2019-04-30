import news
import processor
import cluster
import tweets
import datetime
import json
import sys
import operator

def main():
    E = 0.95
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
    # we are computing the similarity of one tweet with all clusters
    # exists, not the similarity with other tweets
    cluster_id = 0
    for i in range(len(all_tweets)):
        tweet = all_tweets[i]
        token = all_tokens[i]
        # first cluster
        if all_clusters == []:
            new_cluster = cluster.Cluster(tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)
            continue
        
        clustered = False
        # max_cluster_similarity = 0
        # max_cluster_index = -1

        # for single_cluster in all_clusters:
        for j in range(len(all_clusters)):
            single_cluster = all_clusters[j]
            vector = single_cluster.get_vector(False)
            # no common words between the tweet and the cluster, skip
            common_text_vector = intersection(vector["text"], token["text"])
            common_hashtag_vector = intersection(vector["hashtag"], token["hashtag"])
            common_url_vector = intersection(vector["url"], token["url"])
            if common_text_vector == [] and \
                common_hashtag_vector == [] and \
                common_url_vector == []:
                continue

            vector = single_cluster.get_vector(True)

            new_token = {}
            new_token["text"] = " ".join(token["text"])

            new_token["hashtag"] = token["hashtag"]
            new_token["url"] = token["url"]

            similarity = word_processor.new_triple_similarity(new_token, vector)

            # # similarity = word_processor.docs_similarity(tweet[0], vector)
            similarity = word_processor.modified_similarity(
                    similarity, tweet[1], single_cluster)

            # if similarity >= E and similarity > max_cluster_similarity:
            if similarity >= E:
                # max_cluster_similarity = similarity
                # max_cluster_index = j
                single_cluster.push(tweet[0], tweet[1], token)
                clustered = True
                # TODO: we need to consider when one tweet is similar to multiple clusters,
                # which cluster should we push to
                break

        # if max_cluster_index != -1:
        #     all_clusters[max_cluster_index].push(tweet[0], tweet[1], token)
        #     clustered = True

        if not clustered:
            new_cluster = cluster.Cluster(tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)

        # print(i)

    print("Total number of clusters generated: %d" % (len(all_clusters)))
    cluster_sizes = [x.get_size() for x in all_clusters]
    print("The sizes of all clusters generated:")
    print(cluster_sizes)
    max_cluster_size = max(cluster_sizes)

    # for j in range(len(cluster_sizes)):
    #     if cluster_sizes[j] == max_cluster_size:
    #         break

    print("The max cluster size is: %d" % (max_cluster_size))
    # print("Number of tweets clustered using hashtag/url: %d" % (word_processor.hashtag_index))
    # print("Number of tweets clustered using text: %d" % (word_processor.text_index))

    # for item in all_clusters[j].get_all_tweets():
    #     print(item)

    # similarity = word_processor.docs_similarity(all_tweets[0][0], all_tweets[0][0])
    # the similarity we get is greater the better, closer to 1 means they are very
    # similar, otherwise very different

    # TODO: after finish clustering, we need to compute the similarity between
    # each cluster and each news we retrieved
    F = 0.9
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
            similarity = word_processor.modified_similarity(similarity, time, single_cluster, True)

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
    print("Number of pairs generated in total: %d" % (len(related_news_clusters)))
    print("All generated pairs:")
    print(related_news_clusters)
    # print("The most valueable pair: ")
    # print()

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

if __name__ == "__main__":
    main()