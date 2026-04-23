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
        
        # Ensure printed_total exists and is an integer 
        # (Fills any missing data with 0 to prevent math crashes)
        if 'printed_total' in self.df.columns:
            self.df['printed_total'] = self.df['printed_total'].fillna(0).astype(int)
        else:
            print("WARNING: 'printed_total' column missing. Did you re-run build_db.py?")
            self.df['printed_total'] = 0

        # 3. Create the "Super Key" (MultiIndex)
        # drop=False is crucial here! It builds the fast index but keeps the original columns
        # so we can still use them in our smart_guess filter.
        self.df.set_index(['language', 'set_id', 'card_number'], drop=False, inplace=True)
        
        print(f"Database ready! {len(self.df)} cards loaded.")

    def find_card(self, language, set_id, card_number):
        """Instantly fetches a single card using the index (when you know the set ID)."""
        lang_clean = str(language).strip().lower()
        set_clean = str(set_id).strip().lower()
        num_clean = str(card_number).strip().lower()

        try:
            # .loc looks directly at the Index we set up earlier. 
            card_data = self.df.loc[(lang_clean, set_clean, num_clean)]
            
            if isinstance(card_data, pd.DataFrame):
                card_data = card_data.iloc[0]
                
            return {
                "success": True,
                "match_type": "exact",
                "api_id": card_data['api_id'],
                "name": card_data['name'],
                "set_id": card_data['set_id']
            }
            
        except KeyError:
            return {
                "success": False,
                "match_type": "none",
                "error": f"Card not found: {set_clean} {num_clean} ({lang_clean})"
            }

    def smart_guess_card(self, language, card_number, printed_total):
        """Uses the denominator (n) to guess the card without a Set ID!"""
        lang_clean = str(language).strip().lower()
        num_clean = str(card_number).strip().lower()
        total_clean = int(printed_total)
        
        # Filter the database: "Show me all cards with this number AND this total"
        possible_matches = self.df[
            (self.df['language'] == lang_clean) & 
            (self.df['card_number'] == num_clean) & 
            (self.df['printed_total'] == total_clean)
        ]
        
        if len(possible_matches) == 1:
            # BINGO! The set size is entirely unique.
            card = possible_matches.iloc[0]
            return {
                "success": True,
                "match_type": "smart_guess",
                "api_id": card['api_id'],
                "name": card['name'],
                "set_id": card['set_id']
            }
            
        elif len(possible_matches) > 1:
            # A tie! Two sets have the same printed total. 
            sets = possible_matches['set_id'].unique().tolist()
            return {
                "success": False,
                "match_type": "tie",
                "possible_sets": sets,
                "error": f"Tie breaker needed! Could be from sets: {sets}"
            }
            
        else:
            return {
                "success": False,
                "match_type": "none",
                "error": f"No card found with number {num_clean}/{total_clean} ({lang_clean})"
            }

# --- Quick Test ---
if __name__ == "__main__":
    # Make sure to run build_db.py first so the CSV has the new printed_total column!
    db = CardDatabase("./data/local_cards_db.csv")
    
    print("\n--- Test 1: Direct Lookup (We know the Set ID from a Japanese card) ---")
    print(db.find_card(language="jp", set_id="sv8a", card_number="012"))

    print("\n--- Test 2: Smart Guess (We only know the number and total from an English card) ---")
    # Simulating finding your exact English card: 16/185
    print(db.smart_guess_card(language="en", card_number="16", printed_total=185))