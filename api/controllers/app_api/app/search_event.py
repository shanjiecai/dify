import os
import random
from bs4 import BeautifulSoup
import requests
import traceback
from urllib.request import urlretrieve


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
    while res["articles"]:
        # 随机拿出一条不放回
        sample_news = random.sample(res["articles"], 1)[0]
        try:
            image_url = get_image_url(sample_news)
        except:
            print(str(traceback.format_exc()))
            image_url = None
        download_res = download_from_url(image_url)
        if download_res:
            break
        else:
            continue
    return "title: "+sample_news["title"]+"\n"+"description: "+sample_news["description"]+"\n"+"content: "+sample_news["content"]+"\n", image_url


def download_from_url(url, dst="./test2.jpg"):
    """
    @param: url to download file
    @param: dst place to put the file
    """
    try:

        headers = {
            "authority": "ichef.bbci.co.uk",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "macOS",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # urlretrieve(url, dst)
        res = requests.get(url, headers=headers)
        with open(dst, 'wb') as f:
            f.write(res.content)
        return True
    except:
        print(str(traceback.format_exc()))
        return False


if __name__ == "__main__":
    res = api.get_top_headlines(sources='bbc-news')
    # # print(res)
    # for i in res["articles"][:3]:
    #     # print(i)
    #     print(i["title"])
    #     # print(i["url"])
    #     # print(i["urlToImage"])
    #     print(i["description"])
    #     # print(i["publishedAt"])
    #     print(i["content"])
    #     print(i["url"])
    #     response = requests.get(i["url"])
    #
    #     # 使用BeautifulSoup解析网页内容
    #     soup = BeautifulSoup(response.text, "html.parser")
    #
    #     # 找到所有的图片标签
    #     images = soup.find_all("img")
    #
    #     # # 遍历所有的图片标签，提取图片链接
    #     # for image in images:
    #     #     image_url = image["src"]
    #     #     print(image_url)
    #     print(images[0]["src"])
    #     download_from_url(images[0]["src"])
    #     print("-----")
    a, b = get_topic()
    print(a)
    print(b)
    # img_url = "https://ichef.bbci.co.uk/news/976/cpsprodpb/3694/production/_132227931_annapoorani2.jpg"
    # # img_url = "https://ichef.bbci.co.uk/news/976/cpsprodpb/3B49/production/_132277151_gettyimages-1916272669.jpg"
    # # img_url = "https://ichef.bbci.co.uk/news/976/cpsprodpb/13D0/production/_132227050_53450363008_67756bd6d1_k.jpg"
    # download_from_url(img_url)
