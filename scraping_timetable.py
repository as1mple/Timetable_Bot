from selenium import webdriver
import pandas as pd

URL = "https://iq.vntu.edu.ua/b04213/curriculum/c_list.php?view=g&spring=0&group_id=5389"
MAX_COLL = 11

clean_heap = lambda array: [item for index, item in enumerate(array) if index % 8 != 0]


def creat_data_frame(info: list) -> pd.DataFrame:
    columns = ['Date', 'Day']
    [columns.append(f"Lesson {i}") for i in range(1, MAX_COLL - 1)]
    data_frame = pd.DataFrame({i: [] for i in columns})
    for i in range(MAX_COLL):
        if i < 2:
            data_frame[columns[i]] = clean_heap(info[i])
        else:
            data_frame[columns[i]] = info[i]
    return data_frame


if __name__ == '__main__':
    driver = webdriver.Chrome('drivers/chromedriver')
    driver.get(URL)

    table = driver.find_element_by_css_selector("body > table")

    data = [list(map(lambda el: el.text, table.find_elements_by_xpath(f"./tbody/tr/td[{i}]")[0:])) for i in
            range(1, MAX_COLL + 1)]

    db = creat_data_frame(info=data)
    db.to_csv("timetable.csv")
