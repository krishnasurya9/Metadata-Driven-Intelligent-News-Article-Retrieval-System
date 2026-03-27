import pandas as pd
import os

data_dir = r"a:\MSC\sem 2\project\code\data"
files_to_check = ["news_articles.csv", "bbc_news.csv", "ag_news_train.csv", "india-news-headlines.csv"]

for file in files_to_check:
    filepath = os.path.join(data_dir, file)
    if os.path.exists(filepath):
        print(f"\n{'='*50}")
        print(f"Dataset: {file} (Size: {os.path.getsize(filepath) / (1024*1024):.2f} MB)")
        try:
            df = pd.read_csv(filepath, nrows=5)
            print(f"Columns: {list(df.columns)}")
            print(f"Sample Row 1:\n{df.iloc[0].to_dict()}")
        except Exception as e:
            print(f"Error reading: {e}")
    else:
        print(f"\n{file} not found.")
