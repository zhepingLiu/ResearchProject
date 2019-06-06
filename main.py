import news
import processor
import cluster
import tweets
import datetime
import json
import sys
import operator
import time

def main():
    if int(sys.argv[5]) == 1:
        enable_time_relevancy = True
    else:
        enable_time_relevancy = False

    if int(sys.argv[6]) == 1:
        enable_hashtag_similarity = True
    else:
        enable_hashtag_similarity = False

    E = float(sys.argv[2])
    word_processor = processor.Processor(enable_hashtag_similarity)
    tweets_api = tweets.Tweets(int(sys.argv[4]))

    all_tweets = tweets_api.process_tweets(sys.argv[1])
    all_tokens = []
    copied_tweets = list(all_tweets)

    for tweet in copied_tweets:
        tokens = word_processor.tweet_tokenize(tweet[0])
        if tokens["text"] == []:
            all_tweets.remove(tweet)
            continue 
        all_tokens.append(tokens)

    all_clusters = []
    # we are computing the similarity of one tweet with all clusters
    # exists, not the similarity with other tweets
    cluster_id = 0
    for i in range(len(all_tweets)):
        # first cluster
        if all_clusters == []:
            tweet = all_tweets[i]
            token = all_tokens[i]
            new_cluster = cluster.Cluster(tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)
            continue
        
        clustered = False
        # max_cluster_similarity = 0
        # max_cluster_index = -1
        token = all_tokens[i]
        # print("Tweet after processed: %s" % (token["text"]))
        # for single_cluster in all_clusters:
        for j in range(len(all_clusters)):
            single_cluster = all_clusters[j]
            vector = single_cluster.get_vector(False)
            # no common words between the tweet and the cluster, skip
            if not intersection(vector["text"], token["text"]) and \
                not intersection(vector["hashtag"], token["hashtag"]):
                continue

            # start_pre_similarity = time.time()

            new_token = {}
            new_token["text"] = " ".join(token["text"])
            new_token["hashtag"] = token["hashtag"]
            # new_token["url"] = token["url"]
            # print("Pre similarity duration: %s" % (time.time() - start_pre_similarity))

            # if all_text_in_cluster(new_token["text"], vector["text"]):
            #     similarity = 1
            # else:
            #     vector = single_cluster.get_vector(True)
            #     similarity = word_processor.new_triple_similarity(new_token, vector)
            try:
                # print("Cluster: %s" % (vector["text"]))
                vector = single_cluster.get_vector(True)
                similarity = word_processor.new_triple_similarity(new_token, vector)
            except:
                continue
                # print(new_token)
                # print(vector)

            if enable_time_relevancy:
                similarity = word_processor.modified_similarity(
                    similarity, all_tweets[i][1], single_cluster)

            # print("Similarity: %f" % (similarity))
            if similarity >= E:
                tweet = all_tweets[i]
                single_cluster.push(tweet[0], tweet[1], token)
                clustered = True
                break

        # if max_cluster_index != -1:
        #     all_clusters[max_cluster_index].push(tweet[0], tweet[1], token)
        #     clustered = True

        if not clustered:
            tweet = all_tweets[i]
            token = all_tokens[i]
            new_cluster = cluster.Cluster(tweet[0], tweet[1], token, cluster_id)
            cluster_id += 1
            all_clusters.append(new_cluster)
        
        # print("-----------------------------------------------------------")

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

            cluster_vector = single_cluster.get_vector(True)["text"]
            
            if not intersection(cluster_vector, text):
                continue

            similarity = word_processor.docs_similarity(text, cluster_vector)
            # similarity = word_processor.modified_similarity(similarity, publish_time, single_cluster, True)
            # if enable_time_relevancy:
            #     similarity = word_processor.modified_similarity(
            #         similarity, publish_time, single_cluster, True)

            # if similarity >= F and similarity > max_similarity:
            if similarity >= F:
                # max_similarity = similarity
                # max_similarity_index = j
                # The news is related to this cluster
                news_cluster_group["article"] = i
                news_cluster_group["cluster"] = single_cluster.get_id()
                news_cluster_group["similarity"] = similarity
                related_news_clusters.append(news_cluster_group)
                # stop comparing with other clusters
                break
    
    print("Number of pairs generated in total: %d" % (len(related_news_clusters)))
    print("All generated pairs:")
    print(related_news_clusters)

    for related_pair in related_news_clusters:
        print("News below")
        article_id = related_pair["article"]
        print(articles[article_id])
        cluster_id = related_pair["cluster"]
        print("Tweets below:")
        for k in range(len(all_clusters[cluster_id].get_all_tweets())):
            print("[%d]: %s: " % (k, all_clusters[cluster_id].get_all_tweets()[k]))
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