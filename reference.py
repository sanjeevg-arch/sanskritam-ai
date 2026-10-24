"""Small manually curated reference set; not a general Sanskrit parser."""
REFERENCE = {
    "रामः": {"lemma": "राम", "meaning": "Rama", "case": "nominative", "number": "singular", "gender": "masculine", "part_of_speech": "noun", "note": "Subject form"},
    "पुस्तकं": {"lemma": "पुस्तक", "meaning": "book", "case": "accusative", "number": "singular", "gender": "neuter", "part_of_speech": "noun", "note": "Object in the sample sentence; also nominative in other contexts"},
    "पठति": {"lemma": "पठ्", "meaning": "reads", "case": "not applicable", "number": "singular", "gender": "not applicable", "part_of_speech": "verb", "note": "Present indicative, third person, parasmaipada"},
    "कर्मणि": {"lemma": "कर्मन्", "meaning": "in action", "case": "locative", "number": "singular", "gender": "neuter", "part_of_speech": "noun", "note": "Locative singular"},
    "एव": {"lemma": "एव", "meaning": "only / indeed", "case": "not applicable", "number": "not applicable", "gender": "not applicable", "part_of_speech": "particle", "note": "Indeclinable"},
    "ते": {"lemma": "त्वद्", "meaning": "your / to you", "case": "context-dependent", "number": "singular", "gender": "not applicable", "part_of_speech": "pronoun", "note": "Enclitic form; interpretation depends on context"},
    "फलेषु": {"lemma": "फल", "meaning": "in fruits / results", "case": "locative", "number": "plural", "gender": "neuter", "part_of_speech": "noun", "note": "Locative plural"},
}

def lookup(word: str):
    return REFERENCE.get(word.strip('।,;:!? \n'))

def compare_words(words):
    """Check exact-token matches against curated forms only; never infer unseen forms."""
    checked=[]
    for item in words:
        if not isinstance(item,dict):
            continue
        word=str(item.get('word',''))
        entry=lookup(word)
        if entry:
            checked.append({'word':word,'reference':entry,'ai_grammar':str(item.get('grammar',''))})
    return checked
