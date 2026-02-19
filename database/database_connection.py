import mysql.connector
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv() 
db_password = os.getenv('DB_PASSWORD')

config = {
    'user': 'root',
    'password': db_password,
    'host': 'localhost',
    'database': 'csgo'
}

class DatabaseConnection:
  def __init__(self, user, password, host, database):
    self.user = user
    self.password = password
    self.host = host
    self.database = database
    
    try:
      self.engine = create_engine(f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}/{self.database}')
      print("Connection established successfully!")
    except mysql.connector.Error as err:
      print(err)
      
  def seed_items_table(self, items_df):
    table_name="item_metadata"
    try:
      items_df.to_sql(name=table_name, con=self.engine, if_exists='append', index=False, index_label=None)
      print(f"Data imported successfully into {self.database}.{table_name}")
    except Exception as e:
      print(e)

  def seed_price_table(self, prices_df):
    table_name="item_market_data"
    try:
      prices_df.to_sql(name=table_name, con=self.engine, if_exists='append', index=False)
      print(f"Data imported successfully into {self.database}.{table_name}")
    except Exception as e:
      print(e)
      
  def seed_item_crate_mapping_table(self, prices_df):
    table_name="item_crate_mapping"
    try:
      prices_df.to_sql(name=table_name, con=self.engine, if_exists='append', index=False)
      print(f"Data imported successfully into {self.database}.{table_name}")
    except Exception as e:
      print(e)
      
  