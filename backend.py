import pandas as pd
from PyQt6.QtGui import QColor
from typing import List, Tuple, Optional
import ast
from collections import defaultdict

class Skin:
    """
    Represents a CS:GO skin item with all its properties.
    
    Attributes:
        id (int): Unique identifier for this skin
        name (str): Full name of the skin (e.g., "AK-47 | Redline")
        max_float (float): Maximum float value for this skin (typically <= 1.0)
        min_float (float): Minimum float value for this skin (typically >= 0.0)
        crates (List[str]): List of crate names this skin can drop from
        rarity (str): Rarity tier (e.g., "Mil-Spec Grade", "Classified", "Covert")
        weapon (str): Weapon type (e.g., "AK-47", "M4A4")
        stattrack (bool): Whether this is a StatTrak variant
        collection (str): Collection name this skin belongs to
        float (Optional[float]): Float value for this specific instance (if set)
    
    Note: StatTrak and non-StatTrak versions are considered distinct skins.
    """
    
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
        """
        Get possible trade-up outputs for this skin.
        
        Returns all skins in the same collection as this skin, but at the next
        higher rarity tier. These are the possible outputs if this skin is used
        as an input in a trade-up contract.
        
        Returns:
            List of Skin objects representing possible trade-up outcomes
        """
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
        
        Formula: f_out = min_f + f_bar * (max_f - min_f)
        where:
        - f_bar = average float value of input skins
        - f_out = output float value
        - min_f = minimum float of output skin
        - max_f = maximum float of output skin
        
        This remaps the average input float from [0,1] into the valid
        float range [min_f, max_f] for the output skin.
        
        Args:
            input_skins: List of 10 input skins with their float values
            output_skin: The output skin to calculate float for
            
        Returns:
            The calculated output float value, or None if input floats not set
        """
        # Calculate average float of input skins (f_bar)
        input_floats = [skin.float for skin in input_skins if skin.float is not None]
        if not input_floats:
            return None
        
        f_bar = sum(input_floats) / len(input_floats)
        
        # Get output skin's float range
        min_f = output_skin.min_float
        max_f = output_skin.max_float
        
        # Calculate output float: f_out = min_f + f_bar * (max_f - min_f)
        f_out = min_f + f_bar * (max_f - min_f)
        
        return f_out    
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
    def get_tradeup_outcomes(items: list[Skin]) -> List[Tuple[Skin, float]]:
        """
        Given a list of input skins, return possible trade-up outcomes with probabilities.
        
        For each possible output skin s:
        P(s_out = s) = (n_c / 10) * (1 / |S(c, r_out)|)
        
        where:
        - n_c = number of input skins from collection c = collection(s)
        - |S(c, r_out)| = number of skins in collection c at rarity r_out
        - r_out = input rarity + 1
        
        Args:
            items: List of input skins (must all have same rarity, 10 items for most rarities, 5 for Covert)
            
        Returns:
            List of (Skin, probability) tuples sorted by probability descending
            
        Raises:
            ValueError: If items have different rarities or invalid count
        """
        if not items:
            return []
        
        # Validate all items have the same rarity
        rarities = [skin.rarity for skin in items]
        if len(set(rarities)) != 1:
            raise ValueError("All items must have the same rarity for trade-up analysis")
        
        # Validate item count (10 for most rarities, 5 for Covert)
        rarity = rarities[0]
        expected_count = 5 if rarity == "Covert" else 10
        if len(items) != expected_count:
            raise ValueError(f"Trade-ups require exactly {expected_count} items for {rarity} rarity")
        
        # Calculate probabilities for each possible output skin
        # P(s_out = s) = (n_c / N) * (1 / |S(c, r_out)|)
        probabilities = defaultdict(float)
        
        for input_skin in items:
            # Get all possible outputs from this input's collection
            possible_outputs = input_skin.get_tradeups()
            
            if not possible_outputs:
                continue
            
            # n_c / N: probability of selecting this collection
            collection_prob = 1.0 / len(items)
            
            # 1 / |S(c, r_out)|: uniform selection within collection
            skin_prob = 1.0 / len(possible_outputs)
            
            # Add probability contribution to each possible output
            for output_skin in possible_outputs:
                probabilities[output_skin] += collection_prob * skin_prob

        # Sort by probability descending
        sorted_outcomes = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        return sorted_outcomes