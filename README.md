# Alex brain

## Environment for Alex:
```sh
conda create -n anki_env python=3.9
conda activate anki_env
which pip #make sure this is the pip in you conda env if you use conda
pip install -r requirements.txt
```
Add this to bashrc or run in terminal
```sh
export GEMINI_API_KEY="api_key"
```

## How to generate cards
```sh
python cards.py class_notes.md 10-45 #specifying line range is optionals
python cards.py #USE ctrl-c to copy notes to clipboard first!!!
```

## Compiling final deck to anki
```sh
python build_deck.py #compiles to .apkg file directly to anki
```

## Repo Structure
- Repo is located *within* the personal notes folder. Do not bloat it with class notes unstructured for cards.
- `source_cards/` location of source md files to be processed into cards. formatting shown below
- `build_deck.py` converts to anki format
- `images/` location of images used in flashcards
- `Anki_plan.md` Plan for card format and heirarchy structure of tags
- `tags.md` tag heirarchy
- `tools.py` Python tools to help parse and navigate the repo
- `conventions.md` Supports personal notes of how I like to process my knowledge for card explanations. 
- `cards.py` calls gemini api to follow system prompt to inject notes and generate flash cards.
- `manual_cards.py` allows for card generation the gemini web ui as needed 

---

## tags.md
- all tags are hyphonated with no capital letters, spaced with '::'
- [line: ###] is used to mark where 2nd level headers start
- [cross-ref: <tag>]

```md
### NAVIGATION INDEX
[line: 001] Navigation Index
[line: 045] math::series
[line: 052] math::calculus
[line: 055] math::diff-eq
[line: 059] math::linear-algebra
...

---

ee::signals::transforms [cross-ref: math::diff-eq]
	ee::signals::transforms::laplace-transform
		ee::signals::transforms::laplace-transform::double-sided-laplace
	ee::signals::transforms::fourier-transform
    ...

meta::source::class::ECEN###
meta::source::self-taught
```
> TODO: add meta::card-type::<type>
---

## Conventions.md
# Mental Models & Conventions

### cs::dsa::complexity
- Always explain Big-O space/time complexity using combinatorics and state-space counting principles (e.g., explain $O(n^2)$ by mapping it to "choosing 2 items from a set of $n$", or $n \choose 2$).

### ee::signals::transforms
- Explain transforms as geometric projections. Tie the integral back to the intuition of taking a "dot product" between the signal and a complex exponential basis vector to find resonance.

### cpe::hdl::systemc
- When explaining SystemC simulation phases (evaluate/update), explicitly draw direct comparisons to the Verilog stratified event queue (Active, Inactive, NBA regions) to bridge my existing knowledge.

### math::diff-eq
- Prefer visual/vector-field explanations for differential equations over pure analytical derivations when explaining the "why".
---

## source_cards Markdown File Format
- md files should be sorted by 2nd level heirarchy tags. ie. `math::series` and named `math_series.md`
- Use capital letters for frequency domain, use "~" for complex values/phasors
- All equations should be renderable in Latex
- Every card MUST include a `concept::[kebab-case-description]` tag to enable inventory tracking.
- Every card MUST use the two-part answer format containing a blockquote Explanation.

## Card Types Taxonomy
Card types (`meta::card_type::<type>`) represent the specific **cognitive task** required to answer the flashcard. They are heavily domain-specific to avoid generic, unhelpful testing.

### Universal (Cross-Domain)
- `meta::card_type::concept`: Declarative knowledge and definitions (e.g., "What defines a causal system?").
- `meta::card_type::equation`: Pure mathematical relationships and formulas.
- `meta::card_type::common_errors`: Pitfalls, false assumptions, or debugging rules.

### Math & Physics (`math::`, `physics::`)
- `meta::card_type::theorem_condition`: Testing the prerequisites to apply a rule (e.g., "What are the Dirichlet conditions?").
- `meta::card_type::geometric_intuition`: Visualizing the math (e.g., "Geometrically, what does a dot product represent?").
- `meta::card_type::physical_analog`: Bridging math to reality (e.g., "What physical property does the second spatial derivative represent?").
- `meta::card_type::derivation_step`: Testing a specific "trick" or leap in a well-known proof.

### Computer Science (`cs::`)
- `meta::card_type::syntax`: Exact language rules, standard libraries, and declarations.
- `meta::card_type::complexity`: Big-O space/time analysis (explained via state-space counting).
- `meta::card_type::algorithm_step`: Tracing the logic of an algorithm (e.g., Kernighan-Lin swap rules).
- `meta::card_type::memory_map`: Testing heap/stack placement, pointers, and memory leaks.

### Computer Engineering / Digital (`cpe::`, `ee::digital-logic`)
- `meta::card_type::waveform`: Tracing timing diagrams, event queues, and clock edges.
- `meta::card_type::rtl_inference`: Testing what physical hardware is synthesized from a block of HDL code.
- `meta::card_type::state_machine`: Testing FSM transitions, Mealy vs. Moore logic, and state encoding.
- `meta::card_type::arch_diagram`: Identifying components in a datapath, ALU, or cache hierarchy based on a visual.

### Electrical Engineering / Analog (`ee::analog`, `ee::signals`)
- `meta::card_type::schematic_analysis`: Identifying topologies or feedback networks from an image.
- `meta::card_type::small_signal_model`: Translating between large-signal schematics and hybrid-pi/T-models.
- `meta::card_type::transfer_function`: Bode plots, poles/zeros, and filter characteristics.
- `meta::card_type::device_physics`: Operating regions, IV curves, and physical threshold conditions.

Source code example for `<high-level-tag>_<secondary_tag>.md`
```md
# Card Inventory
<!-- AUTOMATICALLY GENERATED BY tools.py - DO NOT EDIT MANUALLY -->
*   **cpe::hdl::systemc**
    *   `meta::card_type::syntax`
        *   active-low-chip-enable-declaration (1)
        *   memory-depth-macro (1)
    *   `meta::card_type::concept`
        *   evaluate-vs-update-phases (1)
*   **cpe::hdl::verilog**
    *   `meta::card_type::code_trace`
        *   fork-join-intra-assignment-delays (3) 
        *   blocking-vs-non-blocking-race-conditions (2)
    *   `meta::card_type::waveform`
        *   setup-time-violations (2)
---
Tags: cpe::hdl::systemc meta::source::class::468 meta::card_type::syntax concept::active-low-chip-enable-declaration

**Q:** What is the syntax to declare an active-low chip enable in SystemC?
**A:** `sc_in<bool> CE_b;`

> **Explanation:** The `sc_in<>` template defines an input port. The `_b` suffix is a common hardware naming convention denoting "bar" or active-low logic.
---
Tags: cpe::hdl::systemc meta::card_type::concept concept::memory-depth-macro

**Q:** How do you define a memory depth macro bit-shift in SystemC?
**A:** `#define RAM_DEPTH (1 << ADDR_WIDTH)`

> **Explanation:** Shifting `1` to the left by `ADDR_WIDTH` is mathematically equivalent to $2^{\text{ADDR\_WIDTH}}$, which calculates the total addressable locations in memory.
---
Tags: cpe::hdl::verilog meta::card_type::waveform concept::fork-join-intra-assignment-delays

**Q:** Look at the execution trace below. When does the RHS evaluate in a `fork...join` block with intra-assignment delays (`<= #`)?
<img src="fork_join_trace.png">
**A:** The RHS evaluates immediately at the current simulation time, but the assignment is scheduled for later in the event queue.

> **Explanation:** In Verilog, the Right-Hand Side (RHS) of a non-blocking assignment is evaluated in the Active region of the current time step, while the actual update is deferred to the Non-Blocking Assign (NBA) region.
```

---

## AI tools for Card Generation:

> TODO: Implement cross references into tag processing [cross-ref: cs::algorithms]. 

Desired flow: 
1. Ingest unstructured notes, usually as md
2. LLM pass 1 identifies tags, prioritizing existing heirarchy, but extending as needed
3. Deterministic tooling updates tag hierarchy in tag.md
4. LLM compiles flashcards
5. Automates writing to source_cards/ and re-indexes inventory


### **anki-compiler** 
#### (phase 1) Tag Identification via API calls (card.py)
```py
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
```
#### (phase 1) Using web interface
Web interface will not inherently have access to `conventions.md`, `tags.md` or the source cards inventory.

```md
Role: Spaced Repetition Card Compiler for Advanced Engineering, Physics, Math, and Computer Science.
Objective: Convert verbose technical notes into highly atomic, retrieval-focused Anki flashcards compatible with a genanki Markdown parser.

## Phase 1 - Note classification
The goal is to categorize notes using a heirarchy of tags for flashcard implementation. You are able to apply tags already existing in the user's heirarchy or create new tags as needed in order to maximize consistency with the level of hierachies presented. Include as many tags as needed; If a concept fits cleanly under multiple tags, include all that are relevant.

CRITICAL RULES:
1. PRIORITIZE EXISTING TAGS: If the concept fits into an existing tag in the CURRENT HIERARCHY, use it exactly as written.
2. PROPOSING NEW TAGS: Using the context of the exist heirarchy to support your decision, proprose new tags either at an increased depth ie. `category::subcatgory::new-subcategory-depth::node` or under an existing subcategory or category ie. `category::subcategory-b::node`.
3. FORMAT: Strict `category::subcategory1::subcategory2::node` kebab-case. There is no restriction on depth, the only goal is to maximize consistency. 

If the user has not provided the current tag heirarchy, request it first before proceeding. If you have access to the tag heirarchy, still prompt the user if they want to update it.

## Phase 2 - Card generation

<attach prompt from below>
- if the user provides specific images or image placeholders, please use placeholders  `images/` (e.g., `<img src="images/CMOS_inverter.png">`)
```

#### (phase 2) Card generation
- usually requires higher thinking modesl

```md
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
```


---

# Code 

## tools.py
```py
def update_nav_index() -> None:
    """Scans tags.md, finds all 2nd-level tags, grabs their line numbers, and rewrites the NAVIGATION INDEX block at the top."""

def get_heirarchy(tag: str) -> str:
    """Finds a specific tag in tags.md and returns it along with all its indented sub-tags."""

def add_tags(tags: list[str]) -> None:
    """Checks if tags exist in tags.md. If not, appends them and updates the navigation index."""

def get_conventions(tags: list[str]) -> str:
    """Scans conventions.md for any headers matching the provided tags (or their parent tags) and returns the specific mental models."""

def update_card_inventory(filepath: str) -> None:
    """Scans a specific .md file in source_cards/, counts occurrences of card_types and concepts, and rewrites the # Card Inventory block at the top."""

def get_card_inventory(tags: list[str]) -> str:
    """Returns a string representation of the current card inventory for the specified tags."""

def get_cards_by_concept(tag: str, concept: str) -> list[str]:
    """Returns the exact markdown text of all existing cards matching a concept."""

def get_cards_by_tag(tag: str) -> list[str]:
    """Returns all cards under a specific tag."""

def get_anki_compiler_prompt() -> str:
    """Simply returns system prompt for card generations."""
```

## Cards.py
```py
def _get_notes_input(note_file: str = None, line_range: tuple = None) -> str:
    """Handles file reading with optional line ranges, or falls back to clipboard via pyperclip."""

def _first_pass_tag_identification(notes: str) -> list[str]:
    """LLM Pass 1 (Gemini-Flash): Analyzes notes against current hierarchy to output applicable tags."""

def gen_cards(note_file: str = None, line_range: tuple = None) -> str:
    """
    Main pipeline: Ingests notes, calls LLM Pass 1 for tags, runs deterministic tooling 
    (add_tags, get_conventions, get_card_inventory), and calls LLM Pass 2 (Gemini-Pro) to compile cards.
    """
```

## manual_cards.py
```py
def ingest_cards(input_file: str = None):
    """
    Reads pre-generated markdown cards (from a file or clipboard), 
    updates the tag hierarchy, routes to the correct file, and syncs the inventory.
    """
```

## build_deck.py
```py
# TODO: updates anki deck when ran as main
```