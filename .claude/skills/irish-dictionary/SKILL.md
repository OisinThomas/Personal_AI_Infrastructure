---
name: irish-dictionary
description: Irish-English dictionary database with 346,201 entries from 3 sources - everyday phrases (11k), technical terms (250k), and usage examples (68k). Provides bidirectional translation, FTS5 full-text search, semantic similarity search (vector embeddings), technical terminology lookup, and contextual examples. USE WHEN user wants to translate English to Irish, translate Irish to English, find similar/related Irish phrases, search Irish dictionary, find Irish word usage examples, look up technical Irish terms, learn Irish phrases in context, or explore Irish language resources.
---

# Irish Dictionary Skill

**Database**: 346,201 entries across 3 sources
- **11,423 everyday phrases** → 16,811 Irish translations
- **250,037 technical terms** → 189,354 concepts (legal, medical, tech, etc.)
- **67,930 usage examples** with contextual phrases

**Technology**: SQLite with FTS5 full-text search + optional vector embeddings (OpenAI), pure Python functions

## When to Use This Skill

Activate when user says:
- "Translate [word/phrase] to Irish"
- "What is [word] in Irish?"
- "Irish word for [word]"
- "How do you say [phrase] in Irish?"
- "Translate [Irish word] to English"
- "What does [Irish word] mean?"
- "Search Irish dictionary for [query]"
- "Find examples of [word] in Irish"
- "Irish usage examples for [word]"
- "Technical Irish term for [word]"
- "Find similar Irish phrases to [word]" *(semantic search)*
- "What Irish words are related to [word]?" *(semantic search)*
- "Irish synonyms for [word]" *(semantic search)*

## Which Function to Use? (Decision Tree)

**IMPORTANT**: Don't overuse `smart_translate()` - it searches ALL sources and is slower. Use targeted functions for better performance.

### For English→Irish Translation

**Simple everyday translation** (most common):
```python
# Use hybrid search if embeddings available (BEST)
results = hybrid_search_translation(conn, "hello", limit=5)

# OR use FTS5 if no embeddings
results = search_translation(conn, "hello", limit=5)
```

**Technical/specialized vocabulary**:
```python
# Go straight to technical search (faster than smart_translate)
results = search_technical_term(conn, "database", limit=5)

# With domain filter
results = search_technical_term(conn, "court", domain="legal", limit=5)
```

**Need both everyday + technical** (rare - only when specifically asked):
```python
# Only use when user explicitly wants "all sources"
results = smart_translate(conn, "water", limit=5)
```

### For Irish→English Translation

**Reverse lookup**:
```python
# Hybrid reverse (BEST if embeddings available)
results = hybrid_search_reverse(conn, "dia duit", limit=5)

# OR FTS5 reverse if no embeddings
results = search_reverse(conn, "dia duit", limit=5)
```

### For "Find Similar" / Semantic Queries

**When user asks for similar/related/synonyms**:
```python
# For English input
results = semantic_search_english(conn, "happy", limit=5)

# For Irish input
results = semantic_search_irish(conn, "áthas", limit=5)
```

### For Usage Examples

**Find contextual usage**:
```python
# Search examples (works for both English and Irish)
examples = search_examples(conn, "love", limit=5, language='both')
```

### Summary Table

| User Request | Best Function | Alternative |
|-------------|---------------|-------------|
| "Translate X to Irish" | `hybrid_search_translation()` | `search_translation()` |
| "What's X in Irish?" | `hybrid_search_translation()` | `search_translation()` |
| "Technical term for X" | `search_technical_term()` | - |
| "Translate [Irish] to English" | `hybrid_search_reverse()` | `search_reverse()` |
| "Find similar to X" | `semantic_search_english()` | - |
| "Words related to X" | `semantic_search_english()` | `hybrid_search_translation()` |
| "Examples of X" | `search_examples()` | - |
| "Search everything for X" | `smart_translate()` | - |

**Rule of Thumb**:
- Use **hybrid** functions (hybrid_search_translation, hybrid_search_reverse) for most queries
- Use **search_technical_term** directly for technical vocabulary
- Use **smart_translate** ONLY when user wants comprehensive results from all sources
- Use **semantic_search** for "similar/related" queries

## Quick Start

### Setup Connection
```python
import sqlite3
import sys

# Add database path to Python path
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')

# Import functions
from dictionary_functions import (
    smart_translate, find_translation, search_translation,
    find_reverse, search_reverse, find_technical_term,
    search_technical_term, get_domains, get_stats
)
from example_functions import (
    search_examples, find_examples, find_examples_by_headword,
    get_random_examples, get_unique_headwords
)
from embedding_functions import (
    semantic_search_english, semantic_search_irish,
    hybrid_search_translation, hybrid_search_reverse,
    get_embedding_stats
)

# Connect to database
conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')
```

### Basic Translation
```python
# Quick English→Irish translation (RECOMMENDED: use hybrid search)
results = hybrid_search_translation(conn, "hello", limit=5)

print("English→Irish translations:")
for item in results:
    score = item['hybrid_score'] * 100
    print(f"  {item['english']} → {' || '.join(item['irish_translations'])} (score: {score:.1f})")

# Get usage examples too
examples = search_examples(conn, "hello", limit=3)
print("\nUsage examples:")
for ex in examples:
    print(f"  EN: {ex['english']}")
    print(f"  GA: {ex['irish']}\n")

conn.close()
```

---

## Complete API Reference

### Translation Functions (dictionary_functions.py)

#### 1. `smart_translate(conn, query, limit=10)`
**Smart search across all sources** - Searches BOTH everyday language AND technical terms

```python
results = smart_translate(conn, "water", limit=5)
# Returns: {
#   'query': 'water',
#   'everyday': [{'english': '...', 'irish_translations': [...], 'source': 'focloir'}, ...],
#   'technical': [{'english': '...', 'irish': '...', 'domain': '...', 'source': 'tearma.ie'}, ...]
# }
```

**Use when**: User explicitly asks for comprehensive results from all sources, or when you need to compare everyday vs technical translations

**Don't use for**: Regular translation queries - use `hybrid_search_translation()` or `search_translation()` instead (faster)

---

#### 2. `find_translation(conn, english)`
**Exact English→Irish lookup** (everyday language only)

```python
result = find_translation(conn, "hello")
# Returns: {
#   'phrase_id': 123,
#   'english': 'hello',
#   'irish_translations': ['dia duit', 'haigh'],
#   'source': 'focloir',
#   'source_file': 'h.txt'
# }
# Returns None if not found
```

**Use when**: User wants exact everyday phrase translation

---

#### 3. `search_translation(conn, query, limit=10)`
**FTS5 full-text search** of English phrases (fuzzy matching)

```python
results = search_translation(conn, "water", limit=10)
# Returns: [
#   {'english': 'water absorption', 'irish_translations': ['ionsú uisce'], ...},
#   {'english': 'hot water', 'irish_translations': ['uisce te'], ...},
#   ...
# ]
```

**Use when**: User query might not be exact, needs fuzzy matching

---

#### 4. `find_reverse(conn, irish)`
**Exact Irish→English lookup** (reverse translation)

```python
result = find_reverse(conn, "dia duit")
# Returns: {
#   'translation_id': 456,
#   'irish': 'dia duit',
#   'english': 'hello',
#   'source': 'focloir',
#   'source_file': 'h.txt'
# }
```

**Use when**: User provides Irish word/phrase, wants English meaning

---

#### 5. `search_reverse(conn, query, limit=10)`
**FTS5 search of Irish phrases** (fuzzy reverse lookup)

```python
results = search_reverse(conn, "uisce", limit=5)
# Returns: [
#   {'irish': 'ionsú uisce', 'english': 'water absorption', ...},
#   {'irish': 'uisce te', 'english': 'hot water', ...},
#   ...
# ]
```

**Use when**: Searching Irish text with partial/fuzzy matching

---

#### 6. `find_technical_term(conn, english, domain=None)`
**Technical terminology lookup** (from tearma.ie)

```python
# Without domain filter
result = find_technical_term(conn, "database")
# Returns: {
#   'term_id': 789,
#   'english': 'database',
#   'irish': 'bunachar sonraí',
#   'concept_id': 12345,
#   'domain': 'technical',
#   'source': 'tearma.ie'
# }

# With domain filter
result = find_technical_term(conn, "court", domain="legal")
```

**Use when**: User needs official/technical terminology

---

#### 7. `search_technical_term(conn, query, domain=None, limit=10)`
**FTS5 search of technical terms**

```python
results = search_technical_term(conn, "computer", limit=5)
# Returns: [
#   {'english': 'computer science', 'irish': 'ríomheolaíocht', 'domain': 'technical', ...},
#   {'english': 'computer network', 'irish': 'líonra ríomhairí', 'domain': 'technical', ...},
#   ...
# ]

# With domain filter
results = search_technical_term(conn, "judge", domain="legal", limit=5)
```

**Use when**: Searching technical vocabulary in specific domain

---

#### 8. `search_technical_reverse(conn, query, domain=None, limit=10)`
**Irish technical term → English** (reverse technical lookup)

```python
results = search_technical_reverse(conn, "bunachar sonraí", limit=5)
# Returns: [
#   {'irish': 'bunachar sonraí', 'english': 'database', 'domain': 'technical', ...},
#   ...
# ]
```

**Use when**: Looking up Irish technical terminology in English

---

#### 9. `get_domains(conn)`
**List all technical domains** with term counts

```python
domains = get_domains(conn)
# Returns: [
#   ('legal', 16000),
#   ('medical', 12000),
#   ('technical', 8000),
#   ...
# ]
```

**Use when**: User wants to browse available domains or show statistics

---

#### 10. `get_stats(conn)`
**Database statistics**

```python
stats = get_stats(conn)
# Returns: {
#   'english_phrases': 11423,
#   'irish_translations': 16811,
#   'technical_terms': 250037,
#   'unique_concepts': 189354,
#   'usage_examples': 67930
# }
```

**Use when**: User asks about database size, coverage, or capabilities

---

### Example Functions (example_functions.py)

#### 11. `search_examples(conn, query, limit=10, language='both')`
**FTS5 search of usage examples** - Find contextual usage

```python
examples = search_examples(conn, "love", limit=5, language='both')
# Returns: [
#   {
#     'example_id': 123,
#     'headword': 'love',
#     'example_contains': 'love',
#     'english': "there's no accounting for love",
#     'irish': 'is ait an mac an grá',
#     'context_id': 'ctx_456',
#     'source_file': 'love.txt'
#   },
#   ...
# ]

# Search only English examples
examples = search_examples(conn, "hello", language='english')

# Search only Irish examples
examples = search_examples(conn, "grá", language='irish')
```

**Use when**: User wants to see word usage in real sentences

---

#### 12. `find_examples(conn, word, limit=10)`
**Find examples by exact word match**

```python
examples = find_examples(conn, "hello", limit=5)
# Returns same format as search_examples
```

**Use when**: Looking for examples of specific word

---

#### 13. `find_examples_by_headword(conn, headword, limit=10)`
**Get all examples for a dictionary headword**

```python
examples = find_examples_by_headword(conn, "water", limit=20)
# Returns all examples where 'water' is the main dictionary entry
```

**Use when**: User wants comprehensive examples for a specific headword

---

#### 14. `get_random_examples(conn, limit=10)`
**Random examples for learning/practice**

```python
examples = get_random_examples(conn, limit=5)
# Returns: [random selection of examples]
```

**Use when**: User wants to practice or explore random phrases

---

#### 15. `get_unique_headwords(conn, limit=None)`
**List all headwords that have examples**

```python
headwords = get_unique_headwords(conn, limit=100)
# Returns: ['hello', 'water', 'love', 'house', ...]
```

**Use when**: Browsing available entries or autocomplete

---

#### 16. `count_examples_by_headword(conn, headword)`
**Count examples for a headword**

```python
count = count_examples_by_headword(conn, "water")
# Returns: 45
```

**Use when**: Checking coverage before fetching examples

---

### Semantic Search Functions (embedding_functions.py)

**Note**: These functions require embeddings to be generated first. Check coverage with `get_embedding_stats()`.

#### 17. `semantic_search_english(conn, query, limit=10)`
**Find semantically similar English phrases** using vector embeddings

```python
results = semantic_search_english(conn, "happy", limit=5)
# Returns: [
#   {
#     'phrase_id': 123,
#     'english': 'joyful',
#     'irish_translations': ['áthasach', 'lúcháireach'],
#     'similarity': 0.95,  # 0-1, higher = more similar
#     'source': 'focloir',
#     'source_file': 'j.txt'
#   },
#   {'english': 'glad', 'similarity': 0.92, ...},
#   {'english': 'cheerful', 'similarity': 0.89, ...},
#   ...
# ]
```

**Use when**: User wants synonyms, related concepts, or phrases with similar meanings (not just keyword matches)

**Examples**:
- "Find Irish words similar to 'happy'" → returns joyful, glad, cheerful, delighted
- "What Irish phrases are related to 'ocean'?" → returns sea, water, marine, waves

---

#### 18. `semantic_search_irish(conn, query, limit=10)`
**Find semantically similar Irish phrases** using vector embeddings

```python
results = semantic_search_irish(conn, "áthas", limit=5)
# Returns: [
#   {
#     'translation_id': 456,
#     'irish': 'lúcháir',
#     'english': 'joy',
#     'similarity': 0.96,
#     'source': 'focloir',
#     'source_file': 'j.txt'
#   },
#   {'irish': 'sonas', 'english': 'happiness', 'similarity': 0.94, ...},
#   ...
# ]
```

**Use when**: User wants to find Irish words with similar meanings

**Examples**:
- "Find Irish words similar to 'grá' (love)" → returns cion, searc, gean
- "What Irish words are related to 'uisce' (water)?" → returns related water/liquid terms

---

#### 19. `hybrid_search_translation(conn, query, limit=10, fts_weight=0.4, semantic_weight=0.6)`
**Hybrid search combining FTS5 keyword matching + semantic similarity**

```python
results = hybrid_search_translation(conn, "water", limit=5)
# Returns: [
#   {
#     'phrase_id': 789,
#     'english': 'water',
#     'irish_translations': ['uisce'],
#     'fts_score': 1.0,      # Keyword match score
#     'semantic_score': 0.8,  # Semantic similarity score
#     'hybrid_score': 0.88,   # Combined weighted score
#     'source': 'focloir'
#   },
#   ...
# ]
```

**Use when**: User wants best of both worlds - exact matches AND semantically related terms

**Advantages**:
- Finds exact keyword matches (high FTS score)
- Also finds related concepts (high semantic score)
- Intelligently ranks results by combined relevance

---

#### 20. `hybrid_search_reverse(conn, query, limit=10, fts_weight=0.4, semantic_weight=0.6)`
**Hybrid reverse search** (Irish→English with FTS5 + semantic)

```python
results = hybrid_search_reverse(conn, "uisce", limit=5)
# Returns same format as hybrid_search_translation but for Irish queries
```

**Use when**: Searching Irish text with both keyword and semantic matching

---

#### 21. `get_embedding_stats(conn)`
**Check embedding coverage** - see how many phrases have embeddings

```python
stats = get_embedding_stats(conn)
# Returns: {
#   'english_phrases': {
#     'total': 11423,
#     'embedded': 11423,
#     'coverage_pct': 100.0
#   },
#   'irish_translations': {
#     'total': 16811,
#     'embedded': 16811,
#     'coverage_pct': 100.0
#   }
# }
```

**Use when**: Checking if semantic search is available before using it

**Important**: If coverage is 0%, embeddings need to be generated first. See setup instructions in `/Users/oisinthomas/Desktop/gaeilge/database/EMBEDDINGS.md`

---

## Common Usage Patterns

### Pattern 1: Comprehensive Translation Response (RECOMMENDED)
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from embedding_functions import hybrid_search_translation
from example_functions import search_examples

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

# Get translations using hybrid search (best results)
results = hybrid_search_translation(conn, "hello", limit=5)

# Get examples
examples = search_examples(conn, "hello", limit=3)

# Format response
print("TRANSLATIONS:")
for item in results[:5]:
    score = item['hybrid_score'] * 100
    print(f"  {item['english']} → {' || '.join(item['irish_translations'])} (score: {score:.1f})")

print("\nUSAGE EXAMPLES:")
for ex in examples[:3]:
    print(f"  EN: {ex['english']}")
    print(f"  GA: {ex['irish']}\n")

conn.close()
```

---

### Pattern 2: Technical Terminology Lookup
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from dictionary_functions import search_technical_term, get_domains

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

# Show available domains
domains = get_domains(conn)
print("Available domains:")
for domain, count in domains[:5]:
    print(f"  {domain}: {count:,} terms")

# Search technical terms
results = search_technical_term(conn, "database", limit=5)
for term in results:
    print(f"{term['english']} → {term['irish']} ({term['domain']})")

conn.close()
```

---

### Pattern 3: Reverse Lookup (Irish→English)
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from embedding_functions import hybrid_search_reverse

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

# Use hybrid reverse search for best results
results = hybrid_search_reverse(conn, "uisce", limit=5)

print(f"Irish word 'uisce' translations:")
for item in results:
    score = item['hybrid_score'] * 100
    print(f"  {item['irish']} → {item['english']} (score: {score:.1f})")

conn.close()
```

---

### Pattern 4: Learning with Random Examples
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from example_functions import get_random_examples

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

examples = get_random_examples(conn, limit=5)

print("Random Irish phrases to learn:")
for i, ex in enumerate(examples, 1):
    print(f"\n{i}. {ex['headword']}")
    print(f"   EN: {ex['english']}")
    print(f"   GA: {ex['irish']}")

conn.close()
```

---

### Pattern 5: Semantic Similarity Search
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from embedding_functions import semantic_search_english, get_embedding_stats

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

# Check if embeddings are available
stats = get_embedding_stats(conn)
if stats['english_phrases']['coverage_pct'] > 0:
    # Find semantically similar phrases
    results = semantic_search_english(conn, "happy", limit=5)
    
    print("Phrases with similar meaning to 'happy':")
    for item in results:
        similarity_pct = item['similarity'] * 100
        print(f"  {item['english']} ({similarity_pct:.1f}% similar)")
        print(f"    → {' || '.join(item['irish_translations'])}\n")
else:
    print("Embeddings not generated yet. Using keyword search instead.")
    from dictionary_functions import search_translation
    results = search_translation(conn, "happy", limit=5)

conn.close()
```

---

### Pattern 6: Hybrid Search (Best Results)
```python
import sqlite3
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
from embedding_functions import hybrid_search_translation, get_embedding_stats

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

# Check embedding availability
stats = get_embedding_stats(conn)

if stats['english_phrases']['coverage_pct'] > 50:  # At least 50% coverage
    # Use hybrid search for best results
    results = hybrid_search_translation(conn, "water", limit=10)
    
    print("Hybrid search results (keyword + semantic):")
    for item in results:
        hybrid_score = item['hybrid_score'] * 100
        print(f"{item['english']} (score: {hybrid_score:.1f})")
        print(f"  → {' || '.join(item['irish_translations'])}")
        print(f"  [Keyword: {item['fts_score']*100:.0f}%, Semantic: {item['semantic_score']*100:.0f}%]\n")
else:
    # Fall back to FTS5 search
    from dictionary_functions import search_translation
    results = search_translation(conn, "water", limit=10)

conn.close()
```

---

## CLI Tools (Alternative to Python API)

For quick lookups without writing Python code:

### Dictionary CLI
```bash
cd /Users/oisinthomas/Desktop/gaeilge/database

# English→Irish
python dictionary.py translate hello

# Irish→English
python dictionary.py reverse "dia duit"

# Smart search (all sources)
python dictionary.py smart water

# Technical terms
python dictionary.py technical database --domain technical

# List domains
python dictionary.py domains

# Show stats
python dictionary.py stats

# Semantic search (requires embeddings)
python dictionary.py similar happy
python dictionary.py similar-irish áthas

# Hybrid search (FTS5 + semantic)
python dictionary.py hybrid water --verbose
python dictionary.py hybrid-reverse uisce

# Check embedding coverage
python dictionary.py embedding-stats
```

### Examples CLI
```bash
cd /Users/oisinthomas/Desktop/gaeilge/database

# Search examples
python examples.py search love

# Find by headword
python examples.py headword water

# Random examples
python examples.py random 5

# List headwords
python examples.py list --limit 50

# Count examples
python examples.py count water
```

---

## Semantic Search Setup (Optional)

The semantic search features require vector embeddings to be generated. This is optional but provides powerful similarity-based search.

### Check if Embeddings are Available
```bash
cd /Users/oisinthomas/Desktop/gaeilge/database
python dictionary.py embedding-stats
```

### Generate Embeddings (if needed)
```bash
# Requires OpenAI API key in .env file
cd /Users/oisinthomas/Desktop/gaeilge/database

# Generate all embeddings (~$0.01 cost, 5-10 minutes)
python generate_embeddings.py

# Or test with limited sample first
python generate_embeddings.py --limit 100
```

**See full setup guide**: `/Users/oisinthomas/Desktop/gaeilge/database/EMBEDDINGS.md`

---

## Database Details

**Location**: `/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db`

**Statistics**:
- Total entries: **346,201**
- English phrases: **11,423** (with optional embeddings)
- Irish translations: **16,811** (with optional embeddings)
- Technical terms: **250,037**
- Unique concepts: **189,354**
- Usage examples: **67,930**
- Database size: **101 MB** (158 MB with embeddings)

**Sources**:
1. **irish-focloir** - Everyday language phrases
2. **tearma.ie** - Official technical terminology (legal, medical, tech, etc.)
3. **irish-words** - Usage examples with context

**Technology**:
- SQLite database with FTS5 full-text search
- Optional vector embeddings (OpenAI text-embedding-3-large, 512 dims)
- sqlite-vec extension for vector similarity search
- Pure Python functions (no classes, no state)
- Fast queries (<10ms for FTS5, <200ms for semantic search)

---

## Key Principles

1. **Always close connections**: Use `conn.close()` when done
2. **Prefer hybrid search**: Use `hybrid_search_translation()` and `hybrid_search_reverse()` for most queries (best results)
3. **Don't overuse smart_translate()**: Only use when user explicitly wants all sources (everyday + technical)
4. **Go direct for technical terms**: Use `search_technical_term()` instead of smart_translate for technical queries
5. **Combine translation + examples**: Richer learning experience with `search_examples()`
6. **Check domains for technical terms**: Filter by domain for more accurate results
7. **Check embedding availability**: Use `get_embedding_stats()` before semantic search
8. **Path management**: Always add database path to sys.path

---

## Error Handling

```python
import sqlite3
import sys

try:
    sys.path.append('/Users/oisinthomas/Desktop/gaeilge/database')
    from embedding_functions import hybrid_search_translation
    from example_functions import search_examples

    conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/database/irish_dictionary.db')

    # Get translations
    results = hybrid_search_translation(conn, user_query, limit=5)

    # Get examples
    examples = search_examples(conn, user_query, limit=3)

    # Process results...

except Exception as e:
    print(f"Error querying Irish dictionary: {e}")
finally:
    if 'conn' in locals():
        conn.close()
```

---

## Supplementary Resources

- **Database README**: `/Users/oisinthomas/Desktop/gaeilge/database/README.md`
- **Embedding Setup Guide**: `/Users/oisinthomas/Desktop/gaeilge/database/EMBEDDINGS.md`
- **Pure Functions Source**: `/Users/oisinthomas/Desktop/gaeilge/database/dictionary_functions.py`
- **Embedding Functions Source**: `/Users/oisinthomas/Desktop/gaeilge/database/embedding_functions.py`
- **Example Functions Source**: `/Users/oisinthomas/Desktop/gaeilge/database/example_functions.py`
- **Database Schema (FTS5)**: `/Users/oisinthomas/Desktop/gaeilge/database/schema_v3_fts.sql`
- **Database Schema (Embeddings)**: `/Users/oisinthomas/Desktop/gaeilge/database/schema_embeddings_safe.sql`
