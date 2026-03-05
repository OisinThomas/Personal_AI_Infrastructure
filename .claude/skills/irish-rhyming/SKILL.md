---
name: irish-rhyming
description: Irish (Gaeilge) rhyming dictionary with pure functional API and CLI. Find rhymes, check rhyme compatibility, pattern match, and validate rhyme schemes for Irish language translations and poetry. USE WHEN translating to Irish, writing Irish poetry, checking if Irish words rhyme, or finding rhyming alternatives for better verse.
---

# Irish Rhyming Dictionary Skill

## Overview

A SQLite-based rhyming dictionary for Irish (Gaeilge) with 31,673 words organized into 4,702 rhyme groups. Provides both a Python API with pure, composable functions and a command-line interface for rhyme lookups, pattern matching, and rhyme scheme validation.

## When to Activate This Skill

**Primary Use Cases:**
- "Do these Irish words rhyme?"
- "Find rhymes for [Irish word]"
- "Check if my Irish translation has good rhyme scheme"
- "Find Irish words that rhyme with [word]"
- "Suggest rhyming alternatives for [Irish word]"
- "Validate ABAB rhyme scheme in Irish"
- "Find words ending in -aidh"
- "What rhymes with 'ceol' in Irish?"

**The Goal:** Help with Irish language rhyming for translations, poetry, song lyrics, and creative writing.

## 🎯 System Architecture

### Database Statistics
- **31,673 Irish words** indexed and searchable
- **4,702 rhyme groups** organized by phonetic similarity
- **6.7 average words per rhyme group**
- **Largest group: 444 words** (group #1510)
- **SQLite backend** with indexes for instant lookups

### Pure Functional API

All functions in `rhyme_functions.py` are pure (no side effects) and composable:

**Core Functions:**
- `find_word(conn, word)` - Look up a specific word
- `find_rhymes(conn, word)` - Get all rhyming words
- `find_group(conn, group_id)` - Get all words in a rhyme group
- `find_partial(conn, pattern)` - Pattern matching (SQL LIKE with wildcards)
- `suggest_similar(conn, word)` - Fuzzy matching using Levenshtein distance
- `smart_lookup(conn, word)` - Intelligent lookup with automatic fallbacks (exact → partial → fuzzy)
- `get_group_info(conn, group_id)` - Get group metadata
- `get_all_groups(conn)` - List all groups

### CLI Interface

```bash
python rhyme.py find <word>       # Find rhymes for a word
python rhyme.py group <id>        # List all words in a rhyme group
python rhyme.py pattern <pattern> # Find words matching a pattern
python rhyme.py suggest <word>    # Suggest similar words (fuzzy)
python rhyme.py smart <word>      # Smart lookup (auto-fallback)
```

## 📚 Setup & Installation

### Initial Setup (One-Time)

The rhyming dictionary system is located in your project at:
```
~/Desktop/gaeilge/rhyming_dictionary/
```

**Prerequisites:**
- Python 3.7+ (standard library only, no external dependencies)
- SQLite3 (built into Python)

**Database Setup:**

```bash
cd ~/Desktop/gaeilge/rhyming_dictionary

# Load the rhyming dictionary data into SQLite (one-time setup)
python load_database.py "../rhyming dictionary.md"

# This will:
# - Parse the rhyming dictionary MD file
# - Create rhyme_dictionary.db
# - Load 4,702 rhyme groups
# - Load 31,673 words
# - Create indexes for fast queries
```

**Verify Installation:**

```bash
cd ~/Desktop/gaeilge/rhyming_dictionary

# Test the parser
python parser.py "../rhyming dictionary.md"

# Quick CLI test
python rhyme.py find ceol
```

## 🚀 Usage Examples

### CLI Usage

**Find rhymes for a word:**
```bash
cd ~/Desktop/gaeilge/rhyming_dictionary
python rhyme.py find ceol

# Output:
# Found 'ceol' in group #2918
# Rhymes for 'ceol' (30 found):
# --------------------------------------------------
#   1. acomhal
#   2. aerasól
#   3. alcól
#   ... and 27 more
```

**Pattern matching (wildcards):**
```bash
# Words ending in -aidh
python rhyme.py pattern "*aidh"

# Words starting with sean
python rhyme.py pattern "sean*"

# Words containing aí
python rhyme.py pattern "*aí*"
```

**Browse a rhyme group:**
```bash
python rhyme.py group 2918

# Output:
# Rhyme Group #2918
# Total words: 31
# Words: acomhal, aerasól, alcól, barrsheol, ...
```

**Smart lookup (automatic fallback):**
```bash
python rhyme.py smart gaol

# Method: exact
# ✓ Found exact match in group #1538
# Rhymes: aol, baol, caol, díol, saol, ...
```

**Fuzzy matching suggestions:**
```bash
python rhyme.py suggest ceoil

# Similar words to 'ceoil' (20 found):
#   1. caoil (distance: 1)
#   2. ceil (distance: 1)
#   3. ceol (distance: 1)
#   ... (edit distance shown)
```

### Python API Usage

**Import the module:**
```python
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary')

import sqlite3
import rhyme_functions as rf

# Connect to database
conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')
```

**Check if words rhyme together:**
```python
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

# Your translation candidates
words = ['ceol', 'saol', 'gaol']
groups = set()

for word in words:
    info = rf.find_word(conn, word)
    if info:
        groups.add(info['group_id'])
        print(f"{word}: group #{info['group_id']}")

if len(groups) == 1:
    print("✓ All words rhyme!")
else:
    print(f"✗ Words in different groups: {groups}")

conn.close()

# Output:
# ceol: group #2918
# saol: group #1538
# gaol: group #1538
# ✗ Words in different groups: {1538, 2918}
```

**Smart lookup with automatic fallbacks:**
```python
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

result = rf.smart_lookup(conn, 'ceol')

if result['method'] == 'exact':
    print(f"Found! {len(result['rhymes'])} rhyming words")
    print(f"Rhymes: {result['rhymes'][:5]}")
elif result['method'] == 'partial':
    print(f"Partial matches: {len(result['suggestions'])} found")
elif result['method'] == 'fuzzy':
    print(f"Similar words: {result['suggestions'][:3]}")

conn.close()
```

**Translation rhyme checking workflow:**
```python
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

# Your translation pairs
translations = {
    'music': 'ceol',
    'life': 'saol',
    'love': 'grá'
}

# Check rhyme compatibility
for eng, irish in translations.items():
    info = rf.find_word(conn, irish)
    if info:
        rhymes = rf.find_rhymes(conn, irish)
        print(f"{eng} ({irish}): group #{info['group_id']}, {len(rhymes)} rhymes")

        # Show a few alternatives from same rhyme group
        print(f"  Alternatives: {rhymes[:5]}")
    else:
        # Try to find similar words
        suggestions = rf.suggest_similar(conn, irish, max_distance=2, limit=5)
        print(f"{eng} ({irish}): NOT FOUND")
        if suggestions:
            print(f"  Did you mean: {[w for w, d in suggestions]}")

conn.close()

# Output:
# music (ceol): group #2918, 30 rhymes
#   Alternatives: ['acomhal', 'aerasól', 'alcól', 'barrsheol', 'casaról']
# life (saol): group #1538, 21 rhymes
#   Alternatives: ['aol', 'baol', 'caol', 'díol', 'gaol']
# love (grá): group #3007, 369 rhymes
#   Alternatives: ['á', 'ábhraíteá', 'ábhrófá', 'achaineofá', 'achainíteá']
```

**Find rhyming alternatives for better poetry:**
```python
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

# You want a word that rhymes with 'lá'
target_word = 'lá'

# Find what it rhymes with
target_info = rf.find_word(conn, target_word)
if target_info:
    # Get all words in that rhyme group
    group = rf.find_group(conn, target_info['group_id'])

    print(f"Words that rhyme with '{target_word}' ({group['word_count']} total):")
    for rhyme_word in group['words'][:20]:
        print(f"  - {rhyme_word}")

    if group['word_count'] > 20:
        print(f"  ... and {group['word_count'] - 20} more")

conn.close()
```

## 🎨 Integration with Translation Workflow

### When Claude is Translating Irish Text

When you're translating English text to Irish and need to maintain rhyme schemes:

1. **After translation, use the API to verify rhymes:**
```python
import sys
sys.path.append('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary')
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

# Your translated lines (ABAB rhyme scheme)
lines = {
    'A1': 'ceol',
    'B1': 'grá',
    'A2': 'eol',
    'B2': 'slá'
}

# Verify A lines rhyme
a1_info = rf.find_word(conn, lines['A1'])
a2_info = rf.find_word(conn, lines['A2'])

if a1_info and a2_info and a1_info['group_id'] == a2_info['group_id']:
    print("✓ A lines rhyme!")
else:
    print("✗ A lines don't rhyme, need alternatives")
    # Suggest alternatives
    if a1_info:
        alternatives = rf.find_rhymes(conn, lines['A1'])
        print(f"Words that rhyme with {lines['A1']}: {alternatives[:10]}")

conn.close()
```

2. **Use CLI for quick checks:**
```bash
# Quick check during translation
cd ~/Desktop/gaeilge/rhyming_dictionary
python rhyme.py smart ceol
python rhyme.py smart eol
```

3. **Find better rhyming alternatives:**
```python
# If a word doesn't rhyme, find alternatives from the target rhyme group
import sqlite3
import rhyme_functions as rf

conn = sqlite3.connect('/Users/oisinthomas/Desktop/gaeilge/rhyming_dictionary/rhyme_dictionary.db')

# You need a word meaning X that rhymes with 'ceol'
ceol_info = rf.find_word(conn, 'ceol')
if ceol_info:
    # Get all rhyming candidates
    rhymes = rf.find_rhymes(conn, 'ceol')
    print(f"Choose from these {len(rhymes)} rhyming options:")
    for rhyme in rhymes[:20]:
        print(f"  - {rhyme}")

conn.close()
```

## 📖 File Structure

```
~/Desktop/gaeilge/rhyming_dictionary/
├── README.md                    # Full documentation
├── USAGE_EXAMPLES.md           # Detailed usage examples
├── requirements.txt            # No dependencies (stdlib only)
├── schema.sql                  # Database schema
├── parser.py                   # Pure parsing functions
├── load_database.py           # Database loading script
├── rhyme_functions.py         # Pure lookup functions (API)
├── rhyme.py                   # CLI interface
├── rhyme_dictionary.db        # SQLite database (created by load_database.py)
└── test_api.py                # API test examples
```

## 🔧 Troubleshooting

**Database not found:**
```bash
cd ~/Desktop/gaeilge/rhyming_dictionary
python load_database.py "../rhyming dictionary.md"
```

**Check if database is loaded:**
```bash
cd ~/Desktop/gaeilge/rhyming_dictionary
python rhyme.py smart ceol
```

**Re-parse the data:**
```bash
cd ~/Desktop/gaeilge/rhyming_dictionary
python parser.py "../rhyming dictionary.md"
```

## 🎯 Common Workflows

### 1. Quick Rhyme Check
```bash
cd ~/Desktop/gaeilge/rhyming_dictionary
python rhyme.py find [word]
```

### 2. Translation Validation
```python
# Use the API to check rhyme compatibility
# See "Python API Usage" section above
```

### 3. Pattern Discovery
```bash
# Find all words with a specific ending
cd ~/Desktop/gaeilge/rhyming_dictionary
python rhyme.py pattern "*[ending]"
```

### 4. Rhyme Scheme Validation
```python
# Check ABAB, AABB, or other rhyme schemes
# See "Integration with Translation Workflow" section above
```

## 💡 Tips

- **Use `smart_lookup()`** for best results - it automatically tries exact → partial → fuzzy matching
- **Pattern matching is powerful** - use `*` wildcards to find words by prefix, suffix, or substring
- **All API functions are pure** - they can be chained and composed for complex queries
- **No external dependencies** - the system uses only Python standard library (sqlite3, re, argparse, os, typing)
- **Database is fast** - indexed for instant lookups even with 31k+ words

## 📚 References

- **Documentation**: `~/Desktop/gaeilge/rhyming_dictionary/README.md`
- **Usage Examples**: `~/Desktop/gaeilge/rhyming_dictionary/USAGE_EXAMPLES.md`
- **Source Data**: `~/Desktop/gaeilge/rhyming dictionary.md` (566KB, 4,702 groups)

## 🎓 Learning Resources

For detailed examples and workflows, see:
- `USAGE_EXAMPLES.md` - Comprehensive examples
- `test_api.py` - Working code examples
- `rhyme_functions.py` - API function reference (with docstrings)
