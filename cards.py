import os
import time
import random
from google import genai
try:
    import pyperclip
except ImportError:
    pyperclip = None

# Import your deterministic tools (assuming they exist in tools.py)
from tools import (
    get_heirarchy, add_tags, update_nav_index, 
    get_conventions, get_card_inventory, update_card_inventory,
    get_anki_compiler_prompt
)

# Initialize the GenAI client
client = genai.Client()

def _generate_with_retry(model_name, contents, config=None, max_retries=5, base_delay=2):
    """Wraps API calls with an exponential backoff loop and random jitter."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
        except Exception as e:
            error_str = str(e)
            
            # Fast-fail for hard tier lockouts so we don't waste time retrying
            if "limit: 0" in error_str:
                raise RuntimeError(f"\n[Error] The model '{model_name}' is not available on your current Free Tier (Quota Limit: 0).")
                
            # Catch server overload (503) or standard rate limit (429)
            if "503" in error_str or "429" in error_str or "UNAVAILABLE" in error_str:
                if attempt == max_retries - 1:
                    raise e  # Max retries reached, fail out
                
                # Exponential backoff with 0-1s random jitter to avoid thundering herd
                sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"   [Notice] API busy. Retrying in {sleep_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(sleep_time)
            else:
                raise e

def _get_notes_input(note_file: str = None, line_range: tuple = None) -> str:
    """Handles file reading with optional line ranges, or falls back to clipboard."""
    if note_file:
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if line_range:
                    # Line ranges (1-indexed for user, converting to 0-indexed)
                    start, end = line_range[0] - 1, line_range[1]
                    return "".join(lines[start:end])
                return "".join(lines)
        except Exception as e:
            raise FileNotFoundError(f"Failed reading {note_file}: {e}")
    else:
        if pyperclip:
            print("No file provided. Reading from clipboard...")
            return pyperclip.paste()
        else:
            raise ImportError("pyperclip is required for clipboard support. Run: pip install pyperclip")

def _first_pass_tag_identification(notes: str) -> list[str]:
    """LLM Pass 1: Analyzes notes against current hierarchy to output applicable tags."""
    current_hierarchy = get_heirarchy("all") 
    
    prompt = f"""
You are a classification routing tool. The goal is to categorize notes using a heirarchy of tags for flashcard implementation. You are able to apply tags already existing in the user's heirarchy or create new tags as needed in order to maximize consistency with the level of hierachies presented. Include as many tags as needed; If a concept fits cleanly under multiple tags, include all that are relevant.

CRITICAL RULES:
1. PRIORITIZE EXISTING TAGS: If the concept fits into an existing tag in the CURRENT HIERARCHY, use it exactly as written.
2. PROPOSING NEW TAGS: Using the context of the exist heirarchy to support your decision, proprose new tags either at an increased depth ie. `category::subcatgory::new-subcategory-depth::node` or under an existing subcategory or category ie. `category::subcategory-b::node`.
3. FORMAT: Strict `category::subcategory1::subcategory2::node` kebab-case. There is no restriction on depth, the only goal is to maximize consistency. 

CURRENT HIERARCHY:
{current_hierarchy}

NOTES TO CLASSIFY:
{notes}

OUTPUT FORMAT: Return ONLY a comma-separated list of tags. No markdown.
"""
    
    # Using the stable latest alias for Flash
    response = _generate_with_retry(
        model_name="gemini-flash-latest",
        contents=prompt,
    )
        
    # Parse the LLM output directly into a Python list
    tags = [tag.strip() for tag in response.text.split(",") if tag.strip()]
    return tags

def gen_cards(note_file: str = None, line_range: tuple = None):
    """
    The main generation pipeline:
    1. Ingest notes
    2. LLM identifies tags
    3. Deterministic tooling updates hierarchy and fetches context
    4. LLM compiles flashcards
    5. Automates writing to source_cards/ and re-indexes inventory
    """
    print("1. Fetching notes...")
    notes_content = _get_notes_input(note_file, line_range)
    
    print("2. LLM Pass 1: Identifying Tags...")
    identified_tags = _first_pass_tag_identification(notes_content)
    print(f"   Tags identified: {identified_tags}")
    
    print("3. Executing Deterministic Pipeline...")
    add_tags(identified_tags)
    update_nav_index()
    
    conventions_text = get_conventions(identified_tags)
    inventory_text = get_card_inventory(identified_tags)
    system_prompt = get_anki_compiler_prompt()
    
    print("4. LLM Pass 2: Generating Cards...")
    payload = ""
    if conventions_text:
        payload += f"USER CONVENTIONS:\n{conventions_text}\n\n"
    if inventory_text:
        payload += f"EXISTING CARDS IN THIS HIERARCHY (DO NOT REPEAT):\n{inventory_text}\n\n"
        
    payload += f"RAW NOTES TO COMPILE:\n{notes_content}"
    
    # Using the stable latest alias for Pro, with a Flash fallback
    try:
        response = _generate_with_retry(
            model_name="gemini-pro-latest",
            contents=payload,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
        )
    except Exception as e:
        print(f"   [Notice] Pro model unavailable ({e}). Falling back to flash...")
        response = _generate_with_retry(
            model_name="gemini-flash-latest",
            contents=payload,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
        )
        
    generated_cards = response.text
    
    print("\n--- GENERATED CARDS ---\n")
    print(generated_cards)
    
    # ==========================================
    # 5. AUTOMATED FILE WRITING & INVENTORY SYNC
    # ==========================================
    if identified_tags:
        primary_tag = identified_tags[0]
        parts = primary_tag.split("::")
        # Format cpe::hdl::systemc -> cpe_hdl.md
        filename = f"{parts[0]}_{parts[1]}.md" if len(parts) >= 2 else "misc.md"
        target_filepath = os.path.join("source_cards", filename)
    else:
        target_filepath = os.path.join("source_cards", "misc.md")

    print(f"\n5. Automating file write and inventory sync for: {target_filepath}")
    
    # Ensure source_cards directory exists
    os.makedirs("source_cards", exist_ok=True)
    
    mode = 'a' if os.path.exists(target_filepath) else 'w'
    with open(target_filepath, mode, encoding='utf-8') as f:
        if mode == 'a':
            f.write("\n---\n")
        f.write(generated_cards.strip() + "\n")
        
    print(f"   Successfully appended cards to {target_filepath}")
    
    # Run the Python tool to rebuild the # Card Inventory header block
    update_card_inventory(target_filepath)
    print("   Card inventory successfully re-indexed.")
    
    return generated_cards


# ==========================================
# CLI Execution 
# ==========================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        gen_cards()
    else:
        file_path = sys.argv[1]
        range_tuple = None
        if len(sys.argv) == 3 and "-" in sys.argv[2]:
            start, end = sys.argv[2].split("-")
            range_tuple = (int(start), int(end))
            
        gen_cards(note_file=file_path, line_range=range_tuple)