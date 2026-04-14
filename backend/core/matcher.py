import pandas as pd

class CardDatabase:
    def __init__(self, csv_path):
        """Loads and optimizes the CSV for zero-latency lookups."""
        print("Loading local card database into memory...")
        
        # 1. Load the raw data
        self.df = pd.read_csv(csv_path)
        
        # 2. Clean the data (OCR can sometimes add weird spaces, so we strip them)
        self.df['set_id'] = self.df['set_id'].astype(str).str.strip().str.lower()
        self.df['card_number'] = self.df['card_number'].astype(str).str.strip().str.lower()
        self.df['language'] = self.df['language'].astype(str).str.strip().str.lower()
        
        # 3. Create the "Super Key" (MultiIndex)
        # This makes lookups O(1) time complexity (instant), instead of O(N) (slow)
        self.df.set_index(['language', 'set_id', 'card_number'], inplace=True)
        
        print(f"Database ready! {len(self.df)} cards loaded.")

    def find_card(self, language, set_id, card_number):
        """Instantly fetches a single card using the index."""
        # Clean the incoming OCR text so it matches our database format
        lang_clean = str(language).strip().lower()
        set_clean = str(set_id).strip().lower()
        num_clean = str(card_number).strip().lower()

        try:
            # .loc looks directly at the Index we set up earlier. 
            # It doesn't search; it just goes straight to the answer.
            card_data = self.df.loc[(lang_clean, set_clean, num_clean)]
            
            # If multiple versions exist (e.g., a reverse holo with the same number),
            # grab the first one. The API will give us both prices anyway.
            if isinstance(card_data, pd.DataFrame):
                card_data = card_data.iloc[0]
                
            return {
                "success": True,
                "api_id": card_data['api_id'],
                "name": card_data['name']
            }
            
        except KeyError:
            # If the specific combo of Set + Number doesn't exist, it fails gracefully
            return {
                "success": False,
                "error": f"Card not found: {set_clean} {num_clean} ({lang_clean})"
            }

# --- Quick Test ---
if __name__ == "__main__":
    # Point this to the CSV we created in the previous step
    db = CardDatabase("../../data/local_cards_db.csv")
    
    # Simulate a successful OCR read from the Japanese card you showed me!
    print("\nSimulating successful scan...")
    result = db.find_card(language="jp", set_id="sv8a", card_number="012")
    print(result)

    # Simulate a bad OCR read
    print("\nSimulating bad scan...")
    bad_result = db.find_card(language="en", set_id="base1", card_number="999")
    print(bad_result)