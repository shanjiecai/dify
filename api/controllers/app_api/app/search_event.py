import os
import random
from bs4 import BeautifulSoup
import requests
import traceback


news_api_key = os.environ.get("NEWS_API_KEY", "cd4c844cee014f92a43b84fc92b117f3")
# print(news_api_key)
from newsapi import NewsApiClient
api = NewsApiClient(api_key=news_api_key)


def get_image_url(i):
    response = requests.get(i["url"], timeout=10)

    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(response.text, "html.parser")

    # 找到所有的图片标签
    images = soup.find_all("img")

    # # 遍历所有的图片标签，提取图片链接
    # for image in images:
    #     image_url = image["src"]
    #     print(image_url)
    print(images[0]["src"])
    return images[0]["src"]


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
    try:
        image_url = get_image_url(sample_news)
    except:
        print(str(traceback.format_exc()))
        image_url = None
    return "title: "+sample_news["title"]+"\n"+"description: "+sample_news["description"]+"\n"+"content: "+sample_news["content"]+"\n", image_url


if __name__ == "__main__":
    res = api.get_top_headlines(sources='bbc-news')
    print(res)
    for i in res["articles"][:3]:
        # print(i)
        print(i["title"])
        # print(i["url"])
        # print(i["urlToImage"])
        print(i["description"])
        # print(i["publishedAt"])
        print(i["content"])
        response = requests.get(i["url"])

        # 使用BeautifulSoup解析网页内容
        soup = BeautifulSoup(response.text, "html.parser")

        # 找到所有的图片标签
        images = soup.find_all("img")

        # # 遍历所有的图片标签，提取图片链接
        # for image in images:
        #     image_url = image["src"]
        #     print(image_url)
        print(images[0]["src"])
        print("-----")
