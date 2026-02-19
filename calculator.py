from database.database_connection import DatabaseConnection
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy.orm import Session

class calculator:
  def __init__(self, db_connection):
    self.db_connection = db_connection
    print("calculator initiated")
    
  def database_seeding(self):
    item_metadata_df = pd.read_csv('item_metadata.csv')
    db_connection.seed_items_table(item_metadata_df)

    market_df = pd.read_csv('csgo2_items.csv')
    db_connection.seed_price_table(market_df)
    
    item_crate_map = pd.read_csv('item_crate_mapping.csv')
    db_connection.seed_item_crate_mapping_table(item_crate_map)
    
  def finding_expected_values(self, engine):
    with Session(engine) as session:
      self.expected_values = {}
    
  

load_dotenv()
db_password = os.getenv('DB_PASSWORD')

config = {
    'user': 'root',
    'password': db_password,
    'host': 'localhost',
    'database': 'csgo'
}

db_connection = DatabaseConnection(config['user'], config['password'], config['host'], config['database'])

calc = calculator(db_connection)

calc.database_seeding()
calc.finding_expected_values(db_connection.engine)