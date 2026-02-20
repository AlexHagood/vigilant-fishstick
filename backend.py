import pandas as pd
from PyQt6.QtGui import QColor
from typing import List, Tuple, Optional
import ast
from collections import defaultdict

class Skin:
    """Represents a CS:GO skin item with all its properties"""
    
    def __init__(self, item_id: int, backend: 'Backend'):
        self.backend = backend
        self.id: int = item_id
        
        # Get the row data for this ID
        row = self.backend.item_metadata[self.backend.item_metadata['id'] == item_id]
        
        if len(row) == 0:
            raise ValueError(f"No item found with id {item_id}")
        
        # Extract all properties from the row
        data = row.iloc[0]
        self.name: str = data['name']
        self.max_float: float = data['max_float']
        self.min_float: float = data['min_float']
        self.crates: List[str] = data['crates']
        self.rarity: str = data['rarity']
        self.weapon: str = data['weapon']
        self.stattrack: bool = data['stattrack']
        self.collection: str = data['collections']  # Single collection as string
        self.float: Optional[float] = None  # Float value for this specific instance
    
    def get_color(self) -> QColor:
        """Get the color associated with this skin's rarity"""
        rarity_colors = {
            "Consumer Grade": QColor("gray"),
            "Industrial Grade": QColor("lightgray"),
            "Mil-Spec Grade": QColor("blue"),
            "Restricted": QColor("purple"),
            "Classified": QColor("orange"),
            "Covert": QColor("red"),
            "Contraband": QColor("black"),
            "Extraordinary": QColor("gold")
        }
        return rarity_colors[self.rarity]
    
    def __repr__(self) -> str:
        return f"Skin(id={self.id}, name='{self.name}', rarity='{self.rarity}')"
    

    def get_tradeups(self) -> List['Skin']:
        """Get possible trade-up outputs for this skin"""
        next_rarity = Backend.next_rarity(self.rarity)
        if not self.collection:
            return []
        
        # Find all items in the next rarity that are in the same collection
        target_items = self.backend.item_metadata[
            (self.backend.item_metadata['rarity'] == next_rarity) & 
            (self.backend.item_metadata['collections'] == self.collection)
        ]
        
        return [self.backend.get_skin(row['id']) for _, row in target_items.iterrows()]

class Backend:
    def __init__(self, ui):
        self.ui = ui
        self._skin_cache = {}  # Cache for Skin objects
        self.load()
        
        # Get all unique collections (now just strings)
        unique_collections = self.item_metadata["collections"].dropna().unique()
        print("Unique collections:", sorted([c for c in unique_collections if c]))

    def load(self):
        collections = pd.read_csv('item_collection_mapping.csv')
        self.item_metadata = pd.read_csv('item_metadata.csv')
        self.item_metadata = self.item_metadata.merge(collections, on="name", how="left")
        
        # Handle duplicate collections column from merge
        if 'collections_y' in self.item_metadata.columns:
            self.item_metadata = self.item_metadata.drop(columns=['collections_x'])
            self.item_metadata = self.item_metadata.rename(columns={'collections_y': 'collections'})

        # Parse 'crates' column as list of strings (from string representations of lists)
        if 'crates' in self.item_metadata.columns:
            self.item_metadata['crates'] = self.item_metadata['crates'].fillna("[]").apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else []
            )
        
        # Fill missing collections with empty string
        if 'collections' in self.item_metadata.columns:
            self.item_metadata['collections'] = self.item_metadata['collections'].fillna("")

    def process_item(self, item):
        # Simulate some processing and update the UI
        self.ui.update_output(f"Processing item: {item.text()}")

    def get_item_list(self):
        """Get list of all item IDs (excluding Extraordinary and Contraband)"""
        filtered = self.item_metadata[
            ~self.item_metadata['rarity'].isin(['Extraordinary', 'Contraband'])
        ]
        return list(filtered['id'])
    
    def get_skin(self, item_id: int) -> Skin:
        """Create a Skin object from an item ID (with caching)"""
        if item_id not in self._skin_cache:
            self._skin_cache[item_id] = Skin(item_id, self)
        return self._skin_cache[item_id]
    
    def get_skin_by_name(self, name: str) -> Optional[Skin]:
        """Create a Skin object from an item name"""
        row = self.item_metadata[self.item_metadata['name'] == name]
        if len(row) == 0:
            return None
        item_id = row.iloc[0]['id']
        return Skin(item_id, self)
    
    @staticmethod 
    def next_rarity(rarity: str) -> str:
        rarity_order = [
            "Consumer Grade",
            "Industrial Grade",
            "Mil-Spec Grade",
            "Restricted",
            "Classified",
            "Covert",
            "Extraordinary"
        ]
        return rarity_order[rarity_order.index(rarity) + 1]
    
    @staticmethod
    def calculate_output_float(input_skins: List[Skin], output_skin: Skin) -> Optional[float]:
        """
        Calculate the output float value for a trade-up.
        
        Formula: y = (max - min) * x + min
        where:
        - x = average float value of input skins
        - y = output float value
        - min = minimum float of output skin
        - max = maximum float of output skin
        
        Args:
            input_skins: List of 10 input skins with their float values
            output_skin: The output skin to calculate float for
            
        Returns:
            The calculated output float value
        """
        # Calculate average float of input skins
        input_floats = [skin.float for skin in input_skins if skin.float is not None]
        if not input_floats:
            return None
        
        avg_input_float = sum(input_floats) / len(input_floats)
        
        # Get output skin's float range
        min_float = output_skin.min_float
        max_float = output_skin.max_float
        float_range = max_float - min_float
        
        # Calculate output float: y = range * x + min
        output_float = float_range * avg_input_float + min_float
        
        return output_float
    
    
    def analyze_selected_skins(self, skins: List[Skin]) -> str:
        """Analyze the selected skins with their float values and return a description"""
        if not skins:
            return "No items selected"
    
        
        rarities = [skin.rarity for skin in skins]
        collections = [skin.collection for skin in skins if skin.collection]  # List of collection strings
        
        result = "Selected Items:\n"
        for skin in skins:
            float_str = f"{skin.float:.4f}" if skin.float is not None else "Not set"
            result += f" - {skin.name} (Float: {float_str})\n"

        result += "\nItem rarity check:\n"
        if len(set(rarities)) != 1:
            result += f"ERROR: Selected items have different rarities"
            return result
        
        result += f"All items have the same rarity: {rarities[0]}\n"
        next_rarity = Backend.next_rarity(rarities[0])
        result += f"Target rarity: {next_rarity}\n"

        result += "\nTarget Collections:\n"
        for collection in set(collections):
            result += f" - {collection}\n"
        try:
            sorted_items = Backend.get_tradeup_outcomes(skins)
        except ValueError as e:
            result += f"INVALID TRADEUP: {e}\n"
            return result

        result += "\nTrade-up Outcomes:\n"
        total = 0.0
        for skin, prob in sorted_items:
            output_float = Backend.calculate_output_float(skins, skin)
            float_str = f"{output_float:.4f}" if output_float is not None else "N/A"
            result += f" - {skin.name}: {prob:.2%} (Float: {float_str})\n"
            total += prob
        result += f"Total probability: {total:.2%}\n"
        
        return result
    
    @staticmethod
    def get_tradeup_outcomes(items : list[Skin]) -> List[Tuple[Skin, float]]:
        """Given a list of Skin items, return a list of possible trade-up outcomes with probabilities"""
        if not items:
            return []
        
        rarities = [skin.rarity for skin in items]
        if len(set(rarities)) != 1:
            raise ValueError("All items must have the same rarity for trade-up analysis")
        
        if not (len(items) == 5 and rarities[0] == "Covert" or len(items) == 10 and rarities[0] in ["Consumer Grade", "Industrial Grade", "Mil-Spec Grade", "Restricted", "Classified"]):
            raise ValueError("Trade-ups require exactly 10 items of the same rarity (5 for Covert)")
        
        next_rarity = Backend.next_rarity(rarities[0])
        
        # Get all target items in the next rarity that match the collections of the input skins
        target_items = []
        for skin in items:
            tradeups = skin.get_tradeups()
            t = [((1 / len(tradeups) ) * (1 / len(items)), tradeup) for tradeup in tradeups]
            target_items.extend(t)

        # Combine target_items based on the skin, summing the probabilities
        combined = defaultdict(float)
        for prob, skin in target_items:
            combined[skin] += prob

        # Sort by probability descending
        sorted_items = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return sorted_items