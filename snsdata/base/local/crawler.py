import os
import platform
import datetime

import pytz
import pymysql
import pandas as pd
from selenium import webdriver
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


def _read_dataframe_from_mysql(table_name):
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
        df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    except Exception as e:
        print(e)
        raise
    finally:
        print('MySQL Connection was successful.')
        conn.close()
    
    return df


def _squeeze_dataframe_by_target_date(df, days):
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date', ascending=False)

    target_days_ago = datetime.datetime.now(pytz.timezone('Asia/Tokyo')) - datetime.timedelta(days=days)
    print(target_days_ago.date())

    target_df = df[df.date.map(lambda s: target_days_ago.date() <= s)][['title', 'url', 'date']]
    
    print(target_df.shape)

    return target_df