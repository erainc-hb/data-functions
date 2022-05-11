import pandas as pd


df = pd.read_pickle('temp.pkl')
print(df.shape)
print(df.head())
# print(df.iloc[0])

print(df.favorite.iloc[30:40])

# date = df.date.iloc[0]
# print(date, type(date))

# date = date.strftime("%Y-%m-%d %H:%M:%S")
# print(date, type(date))

df.to_csv('temp.csv', index=False, encoding='utf-8-sig')