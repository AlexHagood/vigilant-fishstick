from database.database_connection import DatabaseConnection
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import database.mapped_classes as mapClass
class calculator:
  def __init__(self, db_connection):
    self.db_connection = db_connection
    print("calculator initiated")
    
  def database_seeding(self):
    item_metadata_df = pd.read_csv('item_metadata.csv')
    #db_connection.seed_items_table(item_metadata_df)

    market_df = pd.read_csv('csgo2_items.csv')
    db_connection.seed_price_table(market_df)
    
    item_crate_map = pd.read_csv('item_crate_mapping.csv')
    #db_connection.seed_item_crate_mapping_table(item_crate_map)
    
    item_collection_map = pd.read_csv('item_collection_mapping.csv')
    #db_connection.seed_item_collection_mapping_table(item_collection_map)
    
  def expected_helper(self, items):
    sum = 0
    for item in items:
      sum += item.sell_price
    return sum/len(items)
  
  def finding_expected_values(self, engine):
    with Session(engine) as session:
        self.expected_values = {}
        unique_collections = session.query(mapClass.ItemCollectionMapping.collections).distinct().all()
        unique_collections = [row[0] for row in unique_collections]
        unique_rarities = session.query(mapClass.ItemMetadata.rarity).distinct().all()
        unique_rarities = [row[0] for row in unique_rarities]
        wear_levels = {"Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"}

        for rarity in unique_rarities:
            for collection in unique_collections:
                for wear_level in wear_levels:
                    items = (
                        session.query(mapClass.ItemMarketData)
                        .join(
                            mapClass.ItemCollectionMapping,
                            mapClass.ItemMarketData.base_name == mapClass.ItemCollectionMapping.name
                        )
                        .join(
                            mapClass.ItemMetadata,
                            mapClass.ItemMarketData.base_name == mapClass.ItemMetadata.name
                        )
                        .filter(
                            mapClass.ItemCollectionMapping.collections == collection,
                            mapClass.ItemMetadata.rarity == rarity,
                            mapClass.ItemMarketData.wear == wear_level
                        )
                        .all()
                    )

                    if not items:
                        continue

                    key = (rarity, collection, wear_level)
                    self.expected_values[key] = self.expected_helper( items)
                    print(f"Found {len(items)} items for {collection} | {rarity} | {wear_level}")            
                    
  
    
  

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

#calc.database_seeding()
calc.finding_expected_values(db_connection.engine)

print(calc.expected_values)