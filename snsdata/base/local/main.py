from bs4 import BeautifulSoup
import re
from time import sleep
import os
import pickle
import random
import logging
# from datetime import datetime
import datetime


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd

from crawler import _read_dataframe_from_mysql, _get_driver, _squeeze_dataframe_by_target_date

formatter = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename='test.log', level=logging.INFO, format=formatter)

CSS_CLASS = 'css-1dbjc4n r-1ta3fxp r-18u37iz r-1wtj0ep r-1s2bzr4 r-1mdbhws'

top_url = 'https://twitter.com/explore'



def get_tweet_info(e, article_url, article_title, article_date, is_title_base):
    article = BeautifulSoup(
        e.get_attribute('innerHTML'), 'html.parser'
    )
    atags = article.select('a')
    
    name = atags[1].text
    id = atags[2].text
    tweet_url = atags[3].get('href')
    date = atags[3].select_one('time').get('datetime')

    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.000Z')

    if article_date > date:
        return None

    reaction_div = article.find(
        class_=CSS_CLASS)
    spans = reaction_div.find_all('span')

    spans = [span for span in spans if not span.find('span')]

    try:
        reply = spans[0].text if spans[0].text else 0
    except:
        logging.info(f"url={article_url} reply={None}")
        reply = None

    try:
        retweet = spans[1].text if spans[1].text else 0
    except:
        logging.info(f"url={article_url} retweet={None}")
        retweet = None

    try:
        favorite = spans[2].text if spans[2].text else 0
    except:
        logging.info(f"url={article_url} fav={None}")
        favorite = None

    d = {
        'name': name,
        'id': id,
        'tweet_url': tweet_url,
        'date': date,
        'reply': reply,
        'retweet': retweet,
        'favorite': favorite,
        'article_url': article_url,
        'article_title': article_title,
        'is_title_base': is_title_base
    }

    return d

# table_name = "eng_twitter_table"
# table_name = 'eng_raw_table'
table_name = 'jpn_raw_table'

df = _read_dataframe_from_mysql(table_name=table_name)

target_df = _squeeze_dataframe_by_target_date(df=df, days=7)
print(target_df.shape)

target_df = target_df.head()
print(target_df.shape)

title_base_df = target_df.copy()
url_base_df = target_df.copy()

title_base_df['is_title_base'] = True
url_base_df['is_title_base'] = False

query_df = pd.concat([title_base_df, url_base_df])
print(query_df.shape)

driver = _get_driver()
driver.get(top_url)
sleep(random.choice([3, 4]))

info_l = []

for row in query_df.itertuples():
    title = row.title
    url = row.url
    is_title_base = row.is_title_base

    query = ""
    if is_title_base:
        query = '"{}"'.format(title)
        
        if 'jpn' in table_name:
            query = re.sub('[\n\r\t]', '', query)
        
        if not query:
            continue
    else:
        query = '"{}"'.format(url)

    sleep(random.choice([1, 2]))
    search_box = driver.find_element_by_tag_name('input')
    sleep(random.choice([3, 5]))

    search_box.clear()
    sleep(random.choice([1, 2]))

    input_text = search_box.get_attribute("value")
    if input_text:
        search_box.send_keys(Keys.BACKSPACE * len(input_text))

    try:
        search_box.send_keys(query)
        sleep(random.choice([3, 4]))
    except:
        print('You can not search this query.')
        JS_ADD_TEXT_TO_INPUT = """
        console.log( "start" );
        try {
            var elm = arguments[0], txt = arguments[1];
            elm.value += txt;

            elm.dispatchEvent(new Event('change'));
        } catch(e) {
            console.log( e.message );
        }
        """
        driver.execute_script(JS_ADD_TEXT_TO_INPUT, search_box, query)

        sleep(random.choice([1, 2]))
        search_box.send_keys(' ')
        sleep(random.choice([1, 2]))

    search_box.send_keys(Keys.ENTER)
    sleep(random.choice([2, 3]))

    # driver.refresh()
    # sleep(random.choice([2, 3]))

    new_post_tab = driver.find_element_by_css_selector(
        '#react-root > div > div > div.css-1dbjc4n.r-18u37iz.r-13qz1uu.r-417010 > main > div > div > div > div.css-1dbjc4n.r-14lw9ot.r-jxzhtn.r-1ljd8xs.r-13l2t4g.r-1phboty.r-1jgb5lz.r-11wrixw.r-61z16t.r-1ye8kvj.r-13qz1uu.r-184en5c > div > div.css-1dbjc4n.r-1e5uvyk.r-aqfbo4.r-6026j.r-gtdqiz.r-1gn8etr.r-1g40b8q > div:nth-child(2) > nav > div > div.css-1dbjc4n.r-1adg3ll.r-16y2uox.r-1wbh5a2.r-1pi2tsx.r-1udh08x > div > div:nth-child(2)'
    )
    new_post_tab.click()

    sleep(random.choice([2, 3]))

    try:
        WebDriverWait(driver, 8).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'article')))
    except:
        print(f'{query} is not exist.')
    else:
        sleep(random.choice([1, 2]))

        bottom_height = driver.execute_script("return document.body.scrollHeight")
        now_height = 0

        print('取得した高さ', bottom_height)

        while now_height <= bottom_height:
            print('現在の高さ : ', now_height)
            if now_height > 50_000:
                logging.info(f"Break query={query}")
                break
            articles = driver.find_elements_by_tag_name('article')
            for e in articles:
                d = get_tweet_info(e, article_title=title, article_url=url, article_date=row.date, is_title_base=is_title_base)
                if d:
                    info_l.append(d)
            print('取得したツイート数の合計：', len(articles))

            now_height += 2500
            driver.execute_script("window.scrollTo(0, {});".format(now_height))

            sleep(random.choice([2, 2.5, 3]))
            bottom_height = driver.execute_script("return document.body.scrollHeight")
            print('取得した高さ : ', bottom_height)
            print()

            if bottom_height is None:
                break
    finally:
        sleep(random.choice([3, 4, 5]))

print(info_l)
print('ツイート数：', len(info_l))
driver.quit()

df = pd.DataFrame(info_l)
df.to_pickle('temp.pkl')

df.retweet = df.retweet.map(lambda s: s.replace(',', '') if isinstance(s, str) else s)
df.favorite = df.favorite.map(lambda s: s.replace(',', '') if isinstance(s, str) else s)

df.retweet = df.retweet.map(lambda s: s.replace('万', '0000') if isinstance(s, str) else s)
df.favorite = df.favorite.map(lambda s: s.replace('万', '0000') if isinstance(s, str) else s)

# 今回のデータをMySQLに追加する
import pymysql

host = '104.197.254.77'
user = 'root'
password = '77KriM0kwgpNi25q'
db = 'spova_db'

conn = None
try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        db=db)
except Exception as e:
    print(e)
    raise
finally:
    print('MySQL Connection was successful.')

table_name = 'test_jpn_twitter_table'

sql = (f'''
INSERT INTO {table_name} 
    (reply, favorite, retweet, user_name, user_id, tweet_url, tweet_date, article_url_id, article_title, is_title_base)
VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
''')
    
# new_df.date = new_df.date.map(lambda v: v.strftime("%Y-%m-%d"))

data = []
for d in df.to_dict('records'):
    data.append(
        (d['reply'], d['favorite'], d['retweet'], d['name'], d['id'], d['tweet_url'], d['date'].strftime("%Y-%m-%d %H:%M:%S"), d['tweet_url'], d['article_title'], d['is_title_base'])
    )    
print('追加するデータ：', len(data))

# datetimeからstrに変換する
with conn.cursor() as cursor:
    try:
        cursor.executemany(sql, data)
        conn.commit()
    except Exception as e:
        print(e)
        raise
    counter = cursor.rowcount

counter = counter if counter > 0 else 0
print(f"{counter} records inserted.")

conn.close()