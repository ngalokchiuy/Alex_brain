import os
import glob
import genanki
import markdown
import html

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
MODEL_ID = 1607392319
DECK_ID = 2059400110

SOURCE_CARDS_DIR = "source_cards"
IMAGES_DIR = "images"
OUTPUT_FILE = "Alex_Brain.apkg"

# ==========================================
# ANKI MODEL DEFINITION (HTML/CSS)
# ==========================================
html_template = """
<div class="card-content">
    [[FIELD]]
</div>
"""

css_style = """
.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
    text-align: left;
    color: #2c3e50;
    background-color: #ffffff;
    padding: 20px;
}
.card-content {
    max-width: 800px;
    margin: 0 auto;
}
h1, h2, h3 { color: #2980b9; }
code {
    background-color: #f8f9fa;
    padding: 2px 4px;
    border-radius: 4px;
    font-family: "Courier New", Courier, monospace;
    font-size: 0.95em;
    color: #c0392b;
}
pre {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
}
pre code { color: #2c3e50; background: none; }

/* Light Mode Blockquote */
blockquote {
    background: #f1f8ff;
    border-left: 5px solid #2980b9;
    margin: 20px 0 0 0;
    padding: 15px;
    border-radius: 0 6px 6px 0;
    font-size: 0.95em;
    color: #1c2833;
}

/* Dark Mode (Night Mode) Support */
.nightMode .card {
    background-color: #2c2c2c;
    color: #e0e0e0;
}
.nightMode blockquote {
    background: #1a242f; 
    border-left: 5px solid #3498db;
    color: #ecf0f1; 
}
.nightMode code, .nightMode pre {
    background-color: #1e1e1e;
    color: #e74c3c;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 15px 0;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
hr { border: 0; border-top: 1px solid #ecf0f1; margin: 20px 0; }
"""

anki_model = genanki.Model(
    MODEL_ID,
    'Alex Brain Model',
    fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
    ],
    templates=[
        {
            'name': 'Standard Card',
            'qfmt': html_template.replace('[[FIELD]]', '{{Question}}'),
            'afmt': html_template.replace('[[FIELD]]', '{{FrontSide}}<hr id="answer">{{Answer}}'),
        },
    ],
    css=css_style
)

anki_deck = genanki.Deck(DECK_ID, 'Alex Brain - Master Engineering')

# ==========================================
# PARSING & COMPILATION (STATE MACHINE)
# ==========================================

def process_text(text):
    text = text.replace('src="images/', 'src="')
    
    result = []
    math_blocks = []
    i = 0
    n = len(text)
    
    # 1. FSM to safely extract LaTeX and replace with placeholders
    while i < n:
        if text[i] == '`':
            count = 0
            while i + count < n and text[i + count] == '`':
                count += 1
                
            j = i + count
            match_found = False
            
            if count >= 3:
                while j < n:
                    if text[j] == '`':
                        close_count = 0
                        while j + close_count < n and text[j + close_count] == '`':
                            close_count += 1
                        if close_count >= count:
                            match_found = True
                            break
                        j += close_count
                    else:
                        j += 1
            else:
                while j < n:
                    if text.startswith("\n\n", j):
                        break
                    if text[j] == '`':
                        close_count = 0
                        while j + close_count < n and text[j + close_count] == '`':
                            close_count += 1
                        if close_count == count:
                            match_found = True
                            break
                        j += close_count
                    else:
                        j += 1
                        
            if match_found:
                result.append(text[i:j + close_count])
                i = j + close_count
            else:
                result.append('`' * count)
                i += count
                
        elif text.startswith("$$", i):             
            j = i + 2             
            while j < n and not text.startswith("$$", j):
                j += 1
            
            if j < n:
                math_content = text[i+2:j]
                placeholder = f"zzMATHBLOCK{len(math_blocks)}zz"
                # html.escape ensures characters like < or > in math don't break Anki's HTML
                escaped_math = html.escape(math_content) 
                math_blocks.append((placeholder, f"\\[{escaped_math}\\]"))
                result.append(placeholder)
                i = j + 2
            else:
                result.append("$$")
                i += 2
                
        elif text.startswith("$", i):
            j = i + 1
            while j < n:
                # Allow escaped dollar signs inside the inline math block
                if text[j] == '\\' and j + 1 < n and text[j+1] == '$':
                    j += 2
                    continue
                if text[j] == '$':
                    break
                j += 1
            
            if j < n:
                math_content = text[i+1:j]
                placeholder = f"zzMATHINLINE{len(math_blocks)}zz"
                escaped_math = html.escape(math_content)
                math_blocks.append((placeholder, f"\\({escaped_math}\\)"))
                result.append(placeholder)
                i = j + 1
            else:
                result.append("$")
                i += 1
                
        else:
            result.append(text[i])
            i += 1
            
    # 2. Run Markdown on the text (which now only contains safe placeholders)
    text_with_placeholders = "".join(result)
    html_output = markdown.markdown(text_with_placeholders, extensions=['fenced_code', 'tables'])
    
    # 3. Inject the untouched MathJax strings back into the final HTML
    for placeholder, math_html in math_blocks:
        html_output = html_output.replace(placeholder, math_html)
        
    return html_output
def parse_card_block(chunk_lines):
    tags = []
    q_lines = []
    a_lines = []
    
    state = "NONE" # States: TAGS, QUESTION, ANSWER
    
    for line in chunk_lines:
        stripped = line.strip()
        # Remove trailing newline only to preserve intentional Markdown indentation
        clean_line = line.rstrip('\n') 
        
        if stripped.startswith("Tags:"):
            state = "TAGS"
            # Slice rather than global replace
            tags = stripped[5:].strip().split() 
            continue
            
        if stripped.startswith("**Q:**"):
            state = "QUESTION"
            content = stripped[6:].strip()
            if content:
                q_lines.append(content)
            continue
            
        if stripped.startswith("**A:**"):
            state = "ANSWER"
            content = stripped[6:].strip()
            if content:
                a_lines.append(content)
            continue
            
        if state == "QUESTION":
            q_lines.append(clean_line)
        elif state == "ANSWER":
            a_lines.append(clean_line)
            
    return tags, "\n".join(q_lines).strip(), "\n".join(a_lines).strip()
def process_markdown_cards():
    if not os.path.exists(SOURCE_CARDS_DIR):
        print(f"Error: {SOURCE_CARDS_DIR} directory not found.")
        return

    card_count = 0
    
    for filepath in glob.glob(f"{SOURCE_CARDS_DIR}/*.md"):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Group lines into chunks separated by '---'
        chunks = []
        current_chunk = []
        for line in lines:
            if line.strip() == "---":
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
            else:
                current_chunk.append(line)
        if current_chunk:
            chunks.append(current_chunk)
            
        for chunk_lines in chunks:
            # Skip inventory blocks or non-card chunks
            joined_check = "".join(chunk_lines)
            if "Tags:" not in joined_check:
                continue
                
            raw_tags, q_text, a_text = parse_card_block(chunk_lines)
            
            if q_text and a_text:
                clean_tags = [t.replace('::', '_') for t in raw_tags]
                
                q_html = process_text(q_text)
                a_html = process_text(a_text)
                
                note = genanki.Note(
                    model=anki_model,
                    fields=[q_html, a_html],
                    tags=clean_tags
                )
                anki_deck.add_note(note)
                card_count += 1

    print(f"Successfully compiled {card_count} cards from markdown.")

def package_deck():
    package = genanki.Package(anki_deck)
    
    media_files = []
    if os.path.exists(IMAGES_DIR):
        for img_path in glob.glob(f"{IMAGES_DIR}/*"):
            if os.path.isfile(img_path):
                media_files.append(img_path)
                
    package.media_files = media_files
    package.write_to_file(OUTPUT_FILE)
    print(f"Deck exported to {OUTPUT_FILE} with {len(media_files)} media files.")

if __name__ == "__main__":
    print("Building Anki Deck...")
    process_markdown_cards()
    package_deck()
    print("Done! Double click Alex_Brain.apkg to import into Anki.")