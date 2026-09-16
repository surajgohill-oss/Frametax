import csv
import json

def val():
    # check 32 rows
    with open("AG_32_AUTHORITATIVE_PROGRAM_RESEARCH.csv") as cf:
        r = list(csv.DictReader(cf))
        if len(r) != 32:
            raise ValueError("Not 32 rows")
    # check log
    with open("AG_32_SOURCE_RETRIEVAL_LOG.jsonl") as jf:
        lines = jf.readlines()
        if len(lines) != 32:
            raise ValueError("Not 32 logs")
        
val()
