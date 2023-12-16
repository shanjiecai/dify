import os
import random


news_api_key = os.environ.get("NEWS_API_KEY", "cd4c844cee014f92a43b84fc92b117f3")
# print(news_api_key)
from newsapi import NewsApiClient
api = NewsApiClient(api_key=news_api_key)


def get_topic():
    # 根据最近的新闻内容总结出热点话题
    res = api.get_top_headlines(sources='bbc-news')
    # for i in res["articles"][:3]:
    #     print(i)
    #     print(i["title"])
    #     print(i["url"])
    #     print(i["urlToImage"])
    #     print(i["description"])
    # 抽取一条
    sample_news = random.sample(res["articles"], 1)[0]
    return "title: "+sample_news["title"]+"\n"+"description: "+sample_news["description"]+"\n"+"content: "+sample_news["content"]+"\n"


if __name__ == "__main__":
    res = api.get_top_headlines(sources='bbc-news')
    print(res)
    for i in res["articles"][:3]:
        print(i)
        print(i["title"])
        # print(i["url"])
        # print(i["urlToImage"])
        print(i["description"])
        # print(i["publishedAt"])
        print(i["content"])
        print("-----")
