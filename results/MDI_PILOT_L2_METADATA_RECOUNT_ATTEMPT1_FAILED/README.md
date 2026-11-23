# Metadata recount, attempt 1 (from 4f0f00d): 11/12, kept as failed

The only failed check was CHOICES.csv column A_size. JSOC returns the string "NA" for an unavailable size; the
runner writes it as such; the recount read the product CSV with pandas' default NA parsing, which turns "NA" into
NaN, while its own reconstruction kept the string "NA" (12 rows). This is a CSV reading defect of the recount, not
a data difference: every other product, the ledger and the query windows matched. Fix: read the product CSVs keeping
"NA" as a string (keep_default_na=False, only empty fields as missing). The receipt of this attempt is preserved
unchanged; a new receipt is written by the corrected recount.
