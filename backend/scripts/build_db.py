import os
import json
import pandas as pd

def compile_card_data(repo_path, output_path):
    """Crawls the pokemon-tcg-data repo and builds a Pandas DataFrame."""
    cards_list = []
    cards_dir = os.path.join(repo_path, 'cards')

    print(f"Scanning JSON files in {cards_dir}...")
    
    # Walk through all directories in the cards folder
    for root, _, files in os.walk(cards_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                
                # Extract language from the folder structure (e.g., 'en' or 'jp')
                language = os.path.basename(os.path.dirname(file_path))
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        set_cards = json.load(f)
                        for card in set_cards:
                            cards_list.append({
                                'api_id': card.get('id'), 
                                'name': card.get('name'),
                                'set_id': card.get('set', {}).get('id'), 
                                'card_number': card.get('number'), 
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
    # Paths are relative to the root pokemon_stream_tool directory
    REPO_DIR = './data/pokemon-tcg-data' 
    OUTPUT_FILE = './data/local_cards_db.csv'
    
    if os.path.exists(REPO_DIR):
        df = compile_card_data(REPO_DIR, OUTPUT_FILE)
        print("\nFirst 5 cards in your new database:")
        print(df.head())
    else:
        print(f"Error: Could not find {REPO_DIR}. Did you run the git clone command?")