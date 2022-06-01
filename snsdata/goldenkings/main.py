import os
import re
import platform
import datetime
import random
from time import sleep

import pytz
import pymysql
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def _get_driver():
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'

    chrome_options = webdriver.ChromeOptions()

    if platform.system() == "Windows":
        # chrome_path = os.getcwd() + "/chromedriver"
        chrome_path = ChromeDriverManager().install()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('disable-notifications')
    else:
        chrome_path = os.getcwd() + "/bin/chromedriver"
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--v=99')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"
    
    chrome_options.add_argument('--window-size=1200x800')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument(f'--user-agent={ua}')

    driver = webdriver.Chrome(chrome_path, chrome_options=chrome_options)
    driver.implicitly_wait(10)

    return driver


def _create_connection():
    connection_name = "x-rain-186405:us-central1:datatool-db-instance"

    try:
        if platform.system() == "Windows":
            from dotenv import load_dotenv
            load_dotenv()

            conn = pymysql.connect(
                host=os.getenv('HOST'),
                user=os.getenv('USER'),
                password=os.getenv('PASSWORD'),
                db=os.getenv('DB'))
        else:
            conn = pymysql.connect(unix_socket=f'/cloudsql/{connection_name}',
                                user=os.getenv('DB_USER'),
                                password=os.getenv('DB_PASS'),
                                db='spova_db')
    except Exception as e:
        print(e)
        raise
    finally:
        print('MySQL Connection was successful.')
    
    return conn


def _read_dataframe_from_mysql(conn, table_name):
    try:
        df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    except Exception as e:
        print(e)
        raise
    
    return df


def _squeeze_dataframe_by_target_date(df, days):
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date', ascending=False)

    target_days_ago = datetime.datetime.now(pytz.timezone('Asia/Tokyo')) - datetime.timedelta(days=days)
    print('取得日:', target_days_ago.date())

    target_df = df[df.date.map(lambda s: target_days_ago.date() == s)][['title', 'url', 'date']]
    print(target_df.shape)

    return target_df


def _get_tweet_info(e, article_url, article_title, article_date, is_title_base):
    article = BeautifulSoup(
        e.get_attribute('innerHTML'), 'html.parser'
    )
    atags = article.select('a')
    
    name = atags[1].text
    id = atags[2].text
    tweet_url = atags[3].get('href')
    date = atags[3].select_one('time').get('datetime')

    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.000Z') + datetime.timedelta(hours=9)

    if article_date > date:
        return None

    reaction_div = article.find(class_='css-1dbjc4n r-1ta3fxp r-18u37iz r-1wtj0ep r-1s2bzr4 r-1mdbhws')

    spans = reaction_div.find_all('span')

    spans = [span for span in spans if not span.find('span')]

    try:
        reply = spans[0].text if spans[0].text else 0
    except:
        reply = None

    try:
        retweet = spans[1].text if spans[1].text else 0
    except:
        retweet = None

    try:
        favorite = spans[2].text if spans[2].text else 0
    except:
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


def _get_tweet_impression(driver, df, table_name):
    driver.get('https://twitter.com/explore')
    sleep(random.choice([3, 4]))

    info_l = []

    for row in df.itertuples():
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

            while now_height <= bottom_height:
                if now_height > 50_000:
                    print(f"Break query={query}")
                    break
                articles = driver.find_elements_by_tag_name('article')
                for e in articles:
                    d = _get_tweet_info(e, article_title=title, article_url=url, article_date=row.date, is_title_base=is_title_base)
                    if d:
                        info_l.append(d)

                now_height += 2500
                driver.execute_script("window.scrollTo(0, {});".format(now_height))

                sleep(random.choice([2, 2.5, 3]))
                bottom_height = driver.execute_script("return document.body.scrollHeight")

                if bottom_height is None:
                    break
        finally:
            print(query)
            print('取得したツイート数：', len(info_l))
            sleep(random.choice([3, 4, 5]))

    driver.quit()

    return info_l


def _insert_data_to_table(conn, df, table_name):
    sql = (f'''
    INSERT INTO {table_name} 
        (reply, favorite, retweet, user_name, user_id, tweet_url, tweet_date, article_url_id, article_title, is_title_base)
    VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''')

    data = []
    for d in df.to_dict('records'):
        data.append(
            (d['reply'], d['favorite'], d['retweet'], d['name'], d['id'], d['tweet_url'], d['date'].strftime("%Y-%m-%d %H:%M:%S"), d['article_url'], d['article_title'], d['is_title_base'])
        )    
    print('追加するデータ：', len(data))

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


def main(event, context):
# def main():
    # i_table_name = 'eng_raw_table'
    i_table_name = 'jpn_raw_table' # 変更

    # 今回のデータをMySQLに追加する
    target_media_netloc = 'goldenkings.jp' # 変更
    o_table_name = 'jpn_twitter_table' # 変更

    conn = _create_connection()

    read_df = _read_dataframe_from_mysql(conn=conn, table_name=i_table_name)
    print('全データ数:', len(read_df))

    read_df = read_df[read_df.url.map(lambda s: target_media_netloc in s)]
    print(f'{target_media_netloc}:', len(read_df))

    target_df = _squeeze_dataframe_by_target_date(df=read_df, days=14)
    print(target_df.shape)

    if not len(target_df):
        return 'No data to be acquired.'

    title_base_df = target_df.copy()
    url_base_df = target_df.copy()

    title_base_df['is_title_base'] = True
    url_base_df['is_title_base'] = False

    query_df = pd.concat([title_base_df, url_base_df])
    print(query_df.shape)

    driver = _get_driver()

    info_l = _get_tweet_impression(driver, df=query_df, table_name=i_table_name)

    df = pd.DataFrame(info_l)

    df.retweet = df.retweet.map(lambda s: s.replace(',', '') if isinstance(s, str) else s)
    df.favorite = df.favorite.map(lambda s: s.replace(',', '') if isinstance(s, str) else s)

    df.retweet = df.retweet.map(lambda s: s.replace('万', '0000') if isinstance(s, str) else s)
    df.favorite = df.favorite.map(lambda s: s.replace('万', '0000') if isinstance(s, str) else s)


    _insert_data_to_table(conn, df, table_name=o_table_name)

    conn.close()


# if __name__ == '__main__':
#     main()