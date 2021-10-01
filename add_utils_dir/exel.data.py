import datetime
import statistics
import time

import pandas as pd
from openpyxl import load_workbook

df = pd.DataFrame({'UserID': [],
                   'Name': [],
                   'Url': [],
                   'Number': [],
                   'Date': []})

df.to_excel('username.xlsx', index=False)

# top_players = pd.read_excel('username.xlsx')
# print(top_players.head())

# print(top_players.head())
# print()
now_date = datetime.datetime.now().replace(microsecond=0)


# print(now_date)

def time_track(func):
    def wrapper(*args, **kwargs):
        now = time.time()
        res = func(*args, **kwargs)
        end = time.time() - now
        print(f'Время выполнения {end} c')
        # return res
        return end

    return wrapper


def append_to(user_id, text, time):
    wb = load_workbook("../username.xlsx")
    ws = wb["Sheet1"]

    row = (101, 102, 103)  # <--- новая строка
    ws.append(row)

    wb.save("teams1.xlsx")
    wb.close()


@time_track
def append_to_exel(user_id, text, name):
    time = datetime.datetime.now().replace(microsecond=0)
    excel_data_df = pd.read_excel('username.xlsx')
    data = pd.DataFrame({
        'UserID': [user_id],
        'Name': [name],
        'Url': [f"https://vk.com/id{user_id}"],
        'Number': [text],
        'Date': [time]
    })
    res = excel_data_df.append(data)
    res.to_excel('username.xlsx', index=False)
    # print(res)
    return data


def append_to2(user_id, text):
    time = datetime.datetime.now().replace(microsecond=0)
    excel_data_df = pd.read_excel('username.xlsx')
    data = pd.DataFrame({
        'UserID': [user_id],
        'Url': [f"https://vk.com/id{user_id}"],
        'Number': [text],
        'Date': [time]
    })
    res = excel_data_df.append(data)
    res.to_excel('username.xlsx', index=False)
    # print(res)
    return data
    # k.to_excel('teams1.xlsx')

def run():
    sql_data = []
    for i in range(100):
        # USER_LIST[i].state+=1
        sql_data.append(append_to_exel(342141234, 'sfgsdfgsdfger2342134', 'коля'))

    print('json average time', statistics.mean(sql_data))
# append_to_exel(342141234, 'sfgsdfgsdfger2342134', 'коля')
if __name__ == '__main__':
    run()
# df.to_excel('username.xlsx', index=False)
# append_to2(1234123, '898973212')


# df2 = pd.DataFrame({
#         'ID': 123,
#         'Url': "aasdfasdf",
#         'Number': 33,
#         'Date': datetime.datetime.now().replace(microsecond=0)
#     })
# excel_data_df = pd.read_excel('username.xlsx')
# # print whole sheet data
# # print(excel_data_df)
# k = excel_data_df.append(df2)
# k = k.append(df2)
# k = k.append(df2)
# k = k.append(df2)
# 
# print(k)
# print(k["ID"].to_list())
