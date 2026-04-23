import os
import json
import pandas as pd

def compile_card_data(repo_path, output_path):
    cards_list = []
    cards_dir = os.path.join(repo_path, 'cards')
    sets_dir = os.path.join(repo_path, 'sets')

    print("Step 1: Loading Set Data to find printed totals...")
    set_totals = {}
    if os.path.exists(sets_dir):
        # Walk the sets/ directory to map set_ids to their printed_totals
        for root, _, files in os.walk(sets_dir):
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        try:
                            sets_json = json.load(f)
                            for s in sets_json:
                                set_totals[s.get('id')] = s.get('printedTotal', 0)
                        except json.JSONDecodeError:
                            pass

    print(f"Step 2: Scanning Card JSON files in {cards_dir}...")
    for root, _, files in os.walk(cards_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                
                # The language is the folder name (e.g., 'en')
                language = os.path.basename(os.path.dirname(file_path))
                
                # The Set ID is just the filename without the .json extension!
                set_id = file.replace('.json', '')
                
                # Grab the total we found in Step 1
                printed_total = set_totals.get(set_id, 0)

                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        set_cards = json.load(f)
                        for card in set_cards:
                            cards_list.append({
                                'api_id': card.get('id'), 
                                'name': card.get('name'),
                                'set_id': set_id,  # <-- FIXED
                                'card_number': card.get('number'), 
                                'printed_total': printed_total, # <-- FIXED
                                'language': language
                            })
                    except json.JSONDecodeError:
                        print(f"Error reading {file_path}")

    # Convert to Pandas DataFrame
    df = pd.DataFrame(cards_list)
    
    # Save to CSV in the data folder
    df.to_csv(output_path, index=False)
    
    print(f"\nSuccess! Compiled {len(df)} cards into {output_path}.")
    return df

if __name__ == "__main__":
    REPO_DIR = './data/pokemon-tcg-data' 
    OUTPUT_FILE = './data/local_cards_db.csv'
    
    if os.path.exists(REPO_DIR):
        df = compile_card_data(REPO_DIR, OUTPUT_FILE)
        print("\nFirst 5 cards in your FIXED database:")
        print(df.head())
    else:
        print(f"Error: Could not find {REPO_DIR}.")