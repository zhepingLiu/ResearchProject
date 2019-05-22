from newsapi import NewsApiClient
import json
import datetime

class News:

    def __init__(self):
        self.API_KEY = "a59ccd8e65634ff9a3611623b2911394"
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')
        self.newsapi = NewsApiClient(api_key=self.API_KEY)

    def retrieve_everything(self, from_param=None, language="en"):

        PAGE_SIZE = 100

        if from_param == None:
            from_param = self.today

        all_news = self.newsapi.get_everything( q = 'politics',
                                                # from_param = from_param,
                                                from_param = '2019-04-27',
                                                to = '2019-04-29',
                                                sources = "abc-news-au, google-news-au",
                                                page_size = PAGE_SIZE,
                                                language = language)

        totalResults = all_news["totalResults"]
        print("Total number of news articles retrieved: %d" % (totalResults))

        return all_news

    def process_news(self, all_news):
        all_news = all_news['articles']
        # titles = []
        articles = []

        for news in all_news:
            article = {}

            article["title"] = news["title"]

            publish_time = news["publishedAt"]
            publish_time = datetime.datetime.strptime(
                publish_time, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
            article["publish_time"] = publish_time

            article["description"] = news["description"]

            articles.append(article)
        
        return articles
