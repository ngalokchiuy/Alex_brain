import os
import sys
import re
try:
    import pyperclip
except ImportError:
    pyperclip = None

from tools import add_tags, update_nav_index, update_card_inventory

def ingest_cards(input_file: str = None):
    """
    Reads pre-generated markdown cards (from a file or clipboard), 
    updates the tag hierarchy, routes to the correct file, and syncs the inventory.
    """
    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: Could not find file {input_file}")
            return
    else:
        if pyperclip:
            print("Reading generated cards from clipboard...")
            content = pyperclip.paste()
        else:
            raise ImportError("pyperclip is required for clipboard support. Run: pip install pyperclip")

    # Basic validation to ensure it's a card block
    if "Tags:" not in content:
        print("Error: No 'Tags:' line found in the provided text. Is this a valid card block?")
        return

    # 1. Extract all unique tags to update the hierarchy
    # (Matches any line starting with 'Tags:')
    tag_lines = re.findall(r'^Tags:\s*(.*)', content, re.MULTILINE)
    all_identified_tags = set()
    primary_tag = None

    for line in tag_lines:
        tags = line.split()
        for t in tags:
            all_identified_tags.add(t)
            # The primary tag is the first one with '::' that isn't a meta or concept tag
            if "::" in t and not t.startswith("meta::") and not t.startswith("concept::"):
                if not primary_tag: 
                    primary_tag = t

    print(f"Identified Tags: {list(all_identified_tags)}")
    
    # 2. Sync hierarchy
    print("Syncing tag hierarchy in tags.md...")
    add_tags(list(all_identified_tags))
    update_nav_index()

    # 3. Determine file routing based on the primary tag
    if primary_tag:
        parts = primary_tag.split("::")
        # Example: math::series::taylor -> math_series.md
        filename = f"{parts[0]}_{parts[1]}.md" if len(parts) >= 2 else "misc.md"
        target_filepath = os.path.join("source_cards", filename)
    else:
        target_filepath = os.path.join("source_cards", "misc.md")

    print(f"Routing cards to: {target_filepath}")

    # 4. Append to file safely
    os.makedirs("source_cards", exist_ok=True)
    mode = 'a' if os.path.exists(target_filepath) else 'w'
    
    with open(target_filepath, mode, encoding='utf-8') as f:
        if mode == 'a':
            f.write("\n---\n")
        f.write(content.strip() + "\n")
        
    print("Cards successfully appended.")

    # 5. Re-index inventory
    print("Re-indexing card inventory...")
    update_card_inventory(target_filepath)
    print("Done! Repository fully synced.")

if __name__ == "__main__":
    # If a file is passed as an argument, use it. Otherwise, use clipboard.
    if len(sys.argv) > 1:
        ingest_cards(sys.argv[1])
    else:
        ingest_cards()