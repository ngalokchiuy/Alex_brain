import os
import re
import glob

# ==========================================
# CONSTANTS & FILE PATHS
# ==========================================
TAGS_FILE = "tags.md"
CONVENTIONS_FILE = "conventions.md"
SOURCE_CARDS_DIR = "source_cards"

# ==========================================
# TAG MANAGEMENT
# ==========================================

def update_nav_index():
    """
    Scans tags.md, finds all 2nd-level tags (e.g., math::series), grabs their
    line numbers, and rewrites the ### NAVIGATION INDEX block at the top.
    """
    if not os.path.exists(TAGS_FILE): return
    
    with open(TAGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the divider that separates the index from the actual tags
    try:
        divider_idx = lines.index("---\n")
    except ValueError:
        return # Malformed tags.md
        
    tag_body = lines[divider_idx+1:]
    
    # Identify 2nd level tags (no leading whitespace, contains one '::')
    nav_entries = []
    for i, line in enumerate(tag_body):
        clean_line = line.rstrip()
        # Regex: starts with word, has '::', has another word, no leading spaces
        if re.match(r'^[a-z\-]+::[a-z\-]+', clean_line):
            # Line number is (index in tag_body) + (divider_idx) + 1 (for 0-indexing) + 1 (for 1-indexing)
            actual_line_num = i + divider_idx + 2
            # Extract just the tag name, ignoring [cross-ref: ...]
            tag_name = clean_line.split()[0]
            nav_entries.append(f"[line: {actual_line_num:03d}] {tag_name}\n")

    # Rebuild the file
    new_index = ["### NAVIGATION INDEX\n", "[line: 001] Navigation Index\n"] + nav_entries + ["\n", "---\n"]
    
    with open(TAGS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_index + tag_body)
    print("Navigation index updated.")

def get_heirarchy(tag: str) -> str:
    """Finds a specific tag in tags.md and returns it along with all its indented sub-tags."""
    if not os.path.exists(TAGS_FILE): return ""
    
    with open(TAGS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if tag == "all":
        # Return everything after the divider
        return content.split("---")[-1].strip()

    lines = content.split("---")[-1].strip().split('\n')
    result = []
    capturing = False
    base_indent = 0
    
    for line in lines:
        if tag in line:
            capturing = True
            base_indent = len(line) - len(line.lstrip())
            result.append(line)
            continue
            
        if capturing:
            current_indent = len(line) - len(line.lstrip())
            # If we hit a blank line or a tag at the same/higher level, stop capturing
            if line.strip() == "" or current_indent <= base_indent:
                break
            result.append(line)
            
    return "\n".join(result)
def add_tags(tags: list[str]):
    """
    Places new tags properly in the hierarchy inside tags.md.
    Uses strict full-path inheritance to find the deepest existing parent,
    calculates its visual tab depth, and inserts the child appropriately.
    Ignores meta:: and concept:: tags entirely.
    """
    if not os.path.exists(TAGS_FILE): 
        print(f"Error: {TAGS_FILE} not found.")
        return
    
    with open(TAGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    content = "".join(lines)
    added_any = False
    
    # Find where the actual tags start (after the nav index)
    try:
        divider_idx = lines.index("---\n")
    except ValueError:
        divider_idx = 0
    
    for tag in tags:
        tag = tag.strip()
        
        # 1. Firewall: Ignore metadata and concept tracking tags
        if tag.startswith("meta::") or tag.startswith("concept::"):
            continue
            
        # 2. Extract just the tag name, stripping [cross-ref: ...] if present
        clean_tag = tag.split()[0]
            
        # 3. Check if it already exists anywhere in the file
        if clean_tag in content:
            continue
            
        parts = clean_tag.split('::')
        
        parent_tag = None
        parent_indent_level = 0
        insert_idx = len(lines) # Default to appending at the bottom if no parent exists
        
        # 4. Work backwards to find the longest matching parent path
        # E.g. for A::B::C::D, checks A::B::C, then A::B, then A
        for i in range(len(parts)-1, 0, -1):
            potential_parent = "::".join(parts[:i])
            
            for line_num, line in enumerate(lines):
                # Ignore the nav index and blank lines
                if line_num <= divider_idx or not line.strip():
                    continue
                    
                line_tag = line.strip().split()[0] 
                
                if line_tag == potential_parent:
                    parent_tag = potential_parent
                    # Calculate how many leading tabs the parent has
                    parent_indent_level = len(line) - len(line.lstrip('\t'))
                    insert_idx = line_num + 1
                    break
            
            if parent_tag:
                break
                
        # 5. Calculate indentation (Child gets exactly 1 more tab than Parent)
        if parent_tag:
            indent = "\t" * (parent_indent_level + 1)
        else:
            indent = "" # Brand new root-level category
            
        # 6. Insert into our list of lines
        lines.insert(insert_idx, f"{indent}{clean_tag}\n")
        content = "".join(lines) # Update live string so subsequent tags find this new parent
        added_any = True
        print(f"   [Tag Manager] Auto-nested new tag: {clean_tag} (under parent: {parent_tag or 'ROOT'})")
        
    # 7. Save and re-index if changes were made
    if added_any:
        with open(TAGS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        # Assuming update_nav_index() is defined elsewhere in tools.py
        update_nav_index()
# ==========================================
# CARD MANAGEMENT & CONVENTIONS
# ==========================================

def get_conventions(tags: list[str]) -> str:
    """
    Scans conventions.md. If a header (### tag) matches the requested tags 
    OR is a parent of the requested tags, it extracts those conventions.
    """
    if not os.path.exists(CONVENTIONS_FILE): return ""
    
    with open(CONVENTIONS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    blocks = re.split(r'###\s+', content)
    relevant_conventions = []
    
    for block in blocks[1:]: # Skip the first split (the title)
        lines = block.strip().split('\n')
        block_tag = lines[0].strip()
        
        for t in tags:
            # Check if the block_tag is a parent (or exact match) of our target tag
            # e.g., block_tag "cs::dsa" applies to target "cs::dsa::complexity"
            if t.startswith(block_tag):
                relevant_conventions.append(f"### {block_tag}\n" + "\n".join(lines[1:]))
                break # Avoid duplicating if multiple tags match the same block
                
    return "\n\n".join(relevant_conventions)

def update_card_inventory(filepath: str):
    """
    Scans a specific .md file in source_cards/, counts occurrences of card_types 
    and concepts, and rewrites the # Card Inventory block at the top.
    """
    if not os.path.exists(filepath): return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split the file by the markdown horizontal rule `---`
    parts = re.split(r'\n---\n', content)
    if len(parts) < 2: return # No cards found
    
    # The actual cards are everything after the first `---`
    cards = parts[1:]
    
    inventory = {}
    
    for card in cards:
        lines = card.strip().split('\n')
        if not lines[0].startswith("Tags:"):
            continue
            
        tags = lines[0].replace("Tags:", "").strip().split()
        
        primary_tag = None
        card_type = None
        concept = None
        
        for t in tags:
            if t.startswith("meta::card_type::"):
                card_type = t
            elif t.startswith("concept::"):
                concept = t.replace("concept::", "")
            elif "::" in t and not t.startswith("meta::"):
                primary_tag = t # Assumes the first standard tag is the primary hierarchy
                
        if primary_tag and card_type and concept:
            if primary_tag not in inventory:
                inventory[primary_tag] = {}
            if card_type not in inventory[primary_tag]:
                inventory[primary_tag][card_type] = {}
                
            inventory[primary_tag][card_type][concept] = inventory[primary_tag][card_type].get(concept, 0) + 1

    # Generate the Markdown Inventory
    inv_md = ["# Card Inventory\n<!-- AUTOMATICALLY GENERATED BY tools.py - DO NOT EDIT MANUALLY -->\n"]
    for p_tag, ctypes in inventory.items():
        inv_md.append(f"*   **{p_tag}**\n")
        for ctype, concepts in ctypes.items():
            inv_md.append(f"    *   `{ctype}`\n")
            for conc, count in concepts.items():
                inv_md.append(f"        *   {conc} ({count})\n")
                
    # Reassemble the file
    new_content = "".join(inv_md) + "---\n" + "\n---\n".join(cards)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Inventory updated for {filepath}")

def get_card_inventory(tags: list[str]) -> str:
    """Returns a string representation of the current card inventory for the specified tags."""
    # To keep it fast, we just read the pre-generated inventories from source_cards/
    inventory_summaries = []
    for filepath in glob.glob(f"{SOURCE_CARDS_DIR}/*.md"):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract just the inventory block
            match = re.search(r'# Card Inventory.*?(?=\n---)', content, re.DOTALL)
            if match:
                inv_block = match.group(0)
                # Check if any requested tag is in this inventory block
                if any(t in inv_block for t in tags):
                    inventory_summaries.append(inv_block)
                    
    return "\n".join(inventory_summaries)

def get_cards_by_concept(tag: str, concept: str) -> list[str]:
    """Returns the exact markdown text of all existing cards matching a concept."""
    matched_cards = []
    concept_marker = f"concept::{concept}"
    
    for filepath in glob.glob(f"{SOURCE_CARDS_DIR}/*.md"):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        cards = re.split(r'\n---\n', content)
        for card in cards:
            if card.startswith("Tags:") and tag in card and concept_marker in card:
                matched_cards.append(card.strip())
                
    return matched_cards

def get_cards_by_tag(tag: str) -> list[str]:
    """Returns all cards under a specific tag."""
    matched_cards = []
    
    for filepath in glob.glob(f"{SOURCE_CARDS_DIR}/*.md"):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        cards = re.split(r'\n---\n', content)
        for card in cards:
            if card.startswith("Tags:") and tag in card:
                matched_cards.append(card.strip())
                
    return matched_cards

# ==========================================
# PROMPTS
# ==========================================

def get_anki_compiler_prompt() -> str:
    """Returns the exact system prompt for the Anki Compiler."""
    return """
Role: Spaced Repetition Card Compiler for Advanced Engineering, Physics, Math, and Computer Science.
Objective: Convert verbose technical notes into highly atomic, retrieval-focused Anki flashcards compatible with a genanki Markdown parser.

Core Directives:
1. ATOMIC FOCUS: One testable fact, equation, or causal relationship per card. Only test multiple concepts if their relationship is the fact being tested.
2. TWO-PART ANSWERS: Every answer (`**A:**`) MUST have two distinct sections:
   - Part 1: The concise, direct answer (the target for recall).
   - Part 2: A visual break followed by a blockquote (`> **Explanation:**`) detailing the "why", the underlying mechanics, or the proof intuition. If showing a specific example, this should provide the generalized concept, ruling, or syntax behind it.
3. PERSONALIZED MENTAL MODELS: You will be provided with "User Conventions" corresponding to specific tags. You MUST strictly adhere to these conventions when writing the `> **Explanation:**` block. Match the user's cognitive style exactly.
4. MANDATORY TAGGING FORMAT: Every card's first line MUST start with `Tags: ` followed by a space-separated list containing exactly three types of tags:
   - The primary hierarchy tag (e.g., `cpe::hdl::systemc`). 
        - Depth of the heirarchy is not restricted, use what fits best based on how broad or specific a card is.
        - Cards can be taged with mutliple relevant primary hierarchies.
   - The specific card type using the full namespace (e.g., `meta::card_type::syntax`).
   - A tracking tag using strict kebab-case: `concept::[brief-kebab-case-description]` (e.g., `concept::active-low-chip-enable`).
5. OUTPUT FORMAT: Output raw Markdown blocks separated strictly by `---`. Every card must define its Tags on line 1, Question on line 2, and Answer on line 3+.

Domain-Specific Card Types (Select the most appropriate based on the notes):
- UNIVERSAL: `meta::card_type::concept` (definitions), `meta::card_type::equation` (formulas), `meta::card_type::common_errors` (pitfalls/debugging).
- MATH/PHYSICS: `meta::card_type::theorem_condition` (prerequisites), `meta::card_type::geometric_intuition` (visualizing math), `meta::card_type::physical_analog` (math to reality), `meta::card_type::derivation_step` (logical leaps in proofs).
- CS: `meta::card_type::syntax` (language rules), `meta::card_type::complexity` (Big-O state-space), `meta::card_type::algorithm_step` (logic tracing), `meta::card_type::memory_map` (heap/stack/pointers).
- CPE/DIGITAL: `meta::card_type::waveform` (timing/event queues), `meta::card_type::rtl_inference` (synthesized hardware), `meta::card_type::state_machine` (FSM transitions), `meta::card_type::arch_diagram` (datapath/ALU mapping).
- EE/ANALOG: `meta::card_type::schematic_analysis` (topologies/feedback), `meta::card_type::small_signal_model` (hybrid-pi/T-models), `meta::card_type::transfer_function` (bode plots/poles/zeros), `meta::card_type::device_physics` (IV curves/operating regions).

Engineering Notation Standards:
- All math MUST be enclosed in LaTeX (`$ $` for inline, `$$ $$` for block).
- Use strictly capital letters for frequency domain variables (e.g., $X(j\omega)$).
- Use the tilde `~` symbol for complex values and phasors (e.g., $\tilde{V}$).
- when capturing literal back ticks such as in Verilog, nest using `` `compiler-directive ``

Visual integration:
- use plain text snippets gaurded by "```" to illustrate concepts via ascii art as needed. 
"""