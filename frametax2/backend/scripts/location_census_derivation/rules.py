"""Pure text rules shared by the census derivation (tab.py) and its regression tests (no geospatial dependencies).

Codex EVD-002 (2026-10-07): a keyword hit only evidences a PRESENT-DAY environment. A property whose name marks it as a
fossil / palaeontological site never evidences one, and a sentence carrying geological-era or fossil wording is skipped."""
import re

PALAEO = re.compile(r"fossil|prehistoric|pal(a)?eo|million years|carboniferous|jurassic|cretaceous|triassic|devonian|permian|cambrian|petrified|extinct|pleistocene|quaternary|ice age", re.I)
PALAEO_SITE = re.compile(r"fossil|pal(a)?eontolog", re.I)


def present_match(rx, text, name=""):
    """(first present-environment match or None, excluded sentences)."""
    excluded = []
    if PALAEO_SITE.search(name):
        m = rx.search(text)
        return None, ([text[:160]] if m else [])
    for m in rx.finditer(text):
        start = text.rfind(".", 0, m.start()) + 1
        end = text.find(".", m.end())
        sentence = text[start:end if end >= 0 else len(text)]
        if PALAEO.search(sentence):
            excluded.append(sentence.strip())
            continue
        return m, excluded
    return None, excluded
