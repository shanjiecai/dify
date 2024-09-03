import json

import openpyxl
import requests


def get_result(query, app_id="94aad33c-d817-4da7-917a-fc34df0dedfc"):
    url = "http://13.56.164.188/backend-api/v1/chat-messages"

    payload = json.dumps({"query": query, "response_mode": "blocking", "app_id": app_id, "user": "Human"})
    headers = {"Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f", "Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.json()["answer"]


app_id_list = [
    "94aad33c-d817-4da7-917a-fc34df0dedfc",
    "9fb89632-9904-4471-b2f6-c2cc54a6aa2e",
    "5c321cdb-e7ac-413e-85b6-b631f21fb7a2",
    "5e8bcd24-eec2-4df5-bf8e-7b809e7b4265",
]
if __name__ == "__main__":
    with open("./data/Adarina_test.txt") as f:
        query = f.readlines()
    Adarina_Daniels_res_list = []
    # Adrianna_Corona_res_list = []
    # Anthony_Moore_res_list = []
    # Mallory_Asis_res_list = []

    query_list = []
    # 写入excel test4.xlsx
    wb = openpyxl.Workbook()
    ws = wb.active
    # ws.append(["query", "Adarina_Daniels", "Adrianna_Corona", "Anthony_Moore", "Mallory_Asis"])
    ws.append(["query", "Adarina_Daniels"])
    # writer = csv.writer(open("./data/test3.csv", "a"))
    # reader = csv.reader(open("./data/test3.csv", "r"))
    # if len(list(reader)) == 0:
    #     writer.writerow(["query", "Adarina_Daniels", "Adrianna_Corona", "Anthony_Moore", "Mallory_Asis"])
    for q in query:
        q = ".".join(q.split(".")[1:]).strip()
        print(q)
        res = get_result(q, "94aad33c-d817-4da7-917a-fc34df0dedfc")
        Adarina_Daniels_res_list.append(res)
        # res1 = get_result(q, "9fb89632-9904-4471-b2f6-c2cc54a6aa2e")
        # Adrianna_Corona_res_list.append(res1)
        # res2 = get_result(q, "5c321cdb-e7ac-413e-85b6-b631f21fb7a2")
        # Anthony_Moore_res_list.append(res2)
        # res3 = get_result(q, "5e8bcd24-eec2-4df5-bf8e-7b809e7b4265")
        # Mallory_Asis_res_list.append(res3)
        query_list.append(q)
        ws.append([q, res])
        # writer.writerow([q, res, res1, res2, res3])
        # f.write(q + "\t" + res1 + "\t" + res2 + "\t" + res3 + "\n")
    wb.save("./data/test_Adarina_Daniels_1201.xlsx")

    with open("./data/Maria_test.txt") as f:
        query = f.readlines()
    Maria_Paula_Noriega_res_list = []

    query_list = []
    # 写入excel test4.xlsx
    wb = openpyxl.Workbook()
    ws = wb.active
    # ws.append(["query", "Adarina_Daniels", "Adrianna_Corona", "Anthony_Moore", "Mallory_Asis"])
    ws.append(["query", "Maria_Arabo"])
    for q in query:
        q = ".".join(q.split(".")[1:]).strip()
        print(q)
        res = get_result(q, "71c76639-6f80-4472-af5d-37cf87cdd794")
        Maria_Paula_Noriega_res_list.append(res)
        query_list.append(q)
        ws.append([q, res])
    wb.save("./data/test_Maria_Arabo_1201.xlsx")

    # 整理成csv

    # for i in range(len(Adarina_Daniels_res_list)):
    #     f.write(query_list[i] + "\t" + Adarina_Daniels_res_list[i] + "\n")
