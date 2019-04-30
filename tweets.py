from datetime import datetime, timezone
import time
import random

class Tweets:

    def __init__(self):
        self.all_tweets = []

    def process_tweets(self, data):
        # for tweet in data:
        for i in range(500):
        # for i in range(len(data)):
            tweet = data[i]
            text = tweet["text"]
            # ts = time.strftime(
            #     '%Y-%m-%d %H:%M:%S', time.strptime( tweet['created_at'], 
            #     '%a %b %d %H:%M:%S +0000 %Y'))
            ts = datetime.strptime(tweet['created_at'],
                    '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=timezone.utc)
            self.all_tweets.append((text, ts))
        
        # random.shuffle(self.all_tweets)
        return self.all_tweets