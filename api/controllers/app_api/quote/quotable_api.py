import random

import requests

# https://github.com/lukePeavey/quotable
"""https://api.quotable.io/search/quotes?query=dog
{
    "__info__": {
        "$search": {
            "queryString": {
                "query": "dog",
                "defaultPath": "content"
            }
        }
    },
    "count": 2,
    "totalCount": 2,
    "page": 1,
    "totalPages": 1,
    "results": [
        {
            "_id": "wVSm962FzR",
            "content": "There are three faithful friends - an old wife, an old dog, and ready money.",
            "author": "Benjamin Franklin",
            "tags": [
                "Wisdom"
            ],
            "authorId": "xkvcrqREjoOB",
            "authorSlug": "benjamin-franklin",
            "length": 76,
            "dateAdded": "2020-01-26",
            "dateModified": "2023-04-14"
        },
        {
            "_id": "uSGo8Fn65z",
            "author": "Abraham Lincoln",
            "content": "How many legs does a dog have if you call his tail a leg? Four. Saying that a tail is a leg doesn't make it a leg.",
            "tags": [
                "Truth"
            ],
            "authorId": "8k75S1ntV9GW",
            "authorSlug": "abraham-lincoln",
            "length": 114,
            "dateAdded": "2022-03-12",
            "dateModified": "2023-04-14"
        }
    ]
}
"""


#
def get_quotable_quote(query: str, word_limit: int = None):
    url = f"https://api.quotable.io/search/quotes?query={query}"
    response = requests.request("GET", url)
    if response.json()['totalCount'] == 0:
        raise Exception("No quote found")
    if word_limit:
        # 随机返回一个符合条件的，否则返回最短的
        res = []
        min_index = 0
        min_length = 10000
        for index, i in enumerate(response.json()['results']):
            if len(i['content'].split(" ")) <= word_limit:
                res.append(i)
            if len(i['content'].split(" ")) < min_length:
                min_length = len(i['content'].split())
                min_index = index
        if res:
            return random.choice(res)
        else:
            return response.json()['results'][min_index]
    else:
        # 随机返回一个
        return random.choice(response.json()['results'])
