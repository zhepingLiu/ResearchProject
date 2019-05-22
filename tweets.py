from datetime import datetime, timezone
import time
import random
import json

class Tweets:

    def __init__(self, number):
        self.all_tweets = []
        self.number = number

    def process_tweets(self, file):
        i = 0
        for input_tweet in open(file):
            tweet = json.loads(input_tweet)
            text = tweet["text"]
            ts = datetime.strptime(tweet["created_at"],
                '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=timezone.utc)
            self.all_tweets.append((text, ts))
            i += 1
            if i >= self.number:
                break
    
        return self.all_tweets
