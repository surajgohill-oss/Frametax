import csv
with open('docs/validation/AG_32_FINAL_PROGRAM_RESEARCH.csv') as f:
    r = list(csv.DictReader(f))
    if len(r) != 32: raise ValueError('Not 32 final rows')
print('Validation passed')
