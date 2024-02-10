import glob
import os
import time

import pandas as pd
from dotenv import load_dotenv

from utils.loader import Loader
from utils.slack import SlackBot


def collate_csv() -> pd.DataFrame:
  loader = Loader()

  pattern = '**/ph_check*.csv'
  files = glob.glob(pattern, recursive=True)

  for file in files:
    loader.decrypt_file(file)

  combined = pd.concat([pd.read_csv(file) for file in files])

  return combined
  

def main():
  load_dotenv()

  output_file = f'data/ph_list_{time.strftime("%m_%Y")}.csv'

  df = collate_csv()
  df['phv'] = df['phv'].astype('Int64')
  df['updated_at'] = pd.to_datetime('today').date()

  bot = SlackBot()

  prev = bot.getLatestFile(os.getenv('CACHE_CHANNEL'))
  unknown = df[df['phv'] < 0]
  known  = df[df['phv'] >= 0]

  df1 = pd.concat([unknown, prev])

  df1 = df1.sort_values('phv')
  df1 = df1.drop_duplicates(['id', 'car_plate'], keep='last')

  df1 = pd.concat([df1, known])

  df1['updated_at'] = pd.to_datetime(df1['updated_at']).date()

  df1 = df1.sort_values('updated_at')
  df1 = df1.drop_duplicates(['id', 'car_plate'], keep='last')

  df1.to_csv(output_file, index=False)

  bot.deleteLatestMessage(os.getenv('CACHE_CHANNEL'))
  bot.uploadFile(output_file, os.getenv('CACHE_CHANNEL'), f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
  main()
