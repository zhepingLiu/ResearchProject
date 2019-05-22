import main
import datetime
import numpy as np
import pandas as pd
import time
from doc2vec_model import Doc2VecModel

class Cluster:

    def __init__(self, initial_tweet, tweet_time, tokens, id, is_doc2vec=False, doc2vec_model=None):
        self.time_centroid = tweet_time
        self.initial_time = tweet_time
        self.active = True
        self.add_new = True
        self.add_new_time = True
        self.all_tweets = []
        self.cluster_vector = {"text": [], "hashtag": []}
        self.doc2vec_vector = None
        self.cluster_variance = None
        self.push(initial_tweet, tweet_time, tokens)
        self.id = id

        if is_doc2vec:
            self.model = doc2vec_model

    def get_all_tweets(self):
        return self.all_tweets

    def get_size(self):
        return len(self.all_tweets)

    def get_id(self):
        return self.id

    def get_doc2vec_vector(self):
        if self.add_new:
            # new tweets has been pushed
            self.doc2vec_vector = self.model.infer_vector(self.cluster_vector["text"])
            # self.doc2vec_vector = main.infer_doc2vec_model(self)
            self.add_new = False
        
        return self.doc2vec_vector

    def get_time_centroid(self):
        if self.add_new:
            self.time_centroid = self.compute_time_centroid()
            self.add_new_time = False

        return self.time_centroid        

    def get_vector(self, is_str):
        if is_str:
            new_vector = {"text": [], "hashtag": []}
            new_vector["text"] = " ".join(self.cluster_vector["text"])
            new_vector["hashtag"] = self.cluster_vector["hashtag"]
            return new_vector
        
        return self.cluster_vector

    def is_active(self):
        if self.active:    
            d = datetime.datetime.today() - datetime.timedelta(days=3)
            if d > self.initial_time:
                self.active = False
        return self.active

    def push(self, tweet, tweet_time, tokens):
        self.all_tweets.append((tweet, tweet_time))
        self.push_text(tokens["text"])

        if tweet_time < self.initial_time:
            self.initial_time = tweet_time

        if tokens["hashtag"] != []:
            self.push_hashtag(tokens["hashtag"])

        self.add_new = True
        self.add_new_time = True
    
    def push_text(self, texts):
        for text in texts:
            self.cluster_vector["text"].append(text)

    def push_hashtag(self, hashtags):
        # print("New hashtags: %s" % (hashtags))
        for hashtag in hashtags:
            self.cluster_vector["hashtag"].append(hashtag)

    def compute_time_centroid(self):
        datetimes = []
        for (_, time) in self.all_tweets:
            datetimes.append(time)
        
        datetimes = pd.Series(datetimes)
        min_datetime = datetimes.min()
        mean_datetime = (min_datetime + (datetimes - min_datetime).mean()).to_pydatetime()

        return mean_datetime

    def compute_time_variance(self):
        if self.cluster_variance == None:
            time_sum = 0
            
            for (_, time) in self.all_tweets:
                difference = time - self.get_time_centroid()
                difference = difference.days
                difference = difference * difference
                time_sum += difference

            return time_sum / len(self.all_tweets)
        else:
            return self.cluster_variance

        
