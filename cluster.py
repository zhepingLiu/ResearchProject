import datetime
import numpy as np
import pandas as pd

class Cluster:

    def __init__(self, initial_tweet, tweet_time, tokens, id):
        self.time_centroid = tweet_time
        self.initial_time = tweet_time
        self.active = True
        self.is_clustered = False
        self.all_tweets = []
        self.cluster_vector = {"text": [], "hashtag": [], "url": []}
        self.push(initial_tweet, tweet_time, tokens)
        self.id = id

    def change_clustered(self):
        self.is_clustered = True

    def get_all_tweets(self):
        return self.all_tweets

    def get_size(self):
        return len(self.all_tweets)

    def get_id(self):
        return self.id

    def get_vector(self, is_str):
        if is_str:
            new_vector = {"text": [], "hashtag": [], "url": []}
            new_vector["text"] = " ".join(self.cluster_vector["text"])

            new_vector["hashtag"] = self.cluster_vector["hashtag"]
            new_vector["url"] = self.cluster_vector["url"]
            # if self.cluster_vector["hashtag"] != []:
            #     new_vector["hashtag"] = " ".join(self.cluster_vector["hashtag"])
            # else:
            #     new_vector["hashtag"] = ""

            # if self.cluster_vector["url"] != []:
            #     new_vector["url"] = " ".join(self.cluster_vector["url"])
            # else:
            #     new_vector["url"] = ""

            return new_vector
        
        return self.cluster_vector

    def is_active(self):
        if self.active:    
            d = datetime.datetime.today() - datetime.timedelta(days=3)
            if d > self.time_centroid:
                self.active = False
        return self.active

    def push(self, tweet, tweet_time, tokens):
        self.all_tweets.append((tweet, tweet_time))
        self.time_centroid = self.compute_time_centroid()
        self.push_text(tokens["text"])

        if tweet_time < self.initial_time:
            self.initial_time = tweet_time

        if tokens["hashtag"] != []:
            self.push_hashtag(tokens["hashtag"])
        if tokens["url"] != []:
            self.push_url(tokens["url"])
    
    def push_text(self, texts):
        for text in texts:
            self.cluster_vector["text"].append(text)

    def push_hashtag(self, hashtags):
        # print("New hashtags: %s" % (hashtags))
        for hashtag in hashtags:
            self.cluster_vector["hashtag"].append(hashtag)
    
    def push_url(self, urls):
        # print("New urls: %s" % (urls))
        for url in urls:
            self.cluster_vector["url"].append(url)

    def compute_time_centroid(self):
        datetimes = []
        for (tweet, time) in self.all_tweets:
            datetimes.append(time)
        
        datetimes = pd.Series(datetimes)
        min_datetime = datetimes.min()
        mean_datetime = (min_datetime + (datetimes - min_datetime).mean()).to_pydatetime()

        return mean_datetime

    def compute_time_variance(self):
        time_sum = 0
        
        for (tweet, time) in self.all_tweets:
            difference = time - self.time_centroid
            difference = difference.days
            difference = difference * difference
            time_sum += difference

        return time_sum / len(self.all_tweets)

        
