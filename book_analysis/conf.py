# --------------
# General config
# --------------
# Cache results from book analysis, e.g. list of tokens. If cache is enabled,
# past results will be reused but only if the ... TODO
enable_cache = True

# ------------------------
# Directory and file paths
# ------------------------
# Data directory path where the epub and pdf files are saved
data_dirpath = "~/Data/book-analysis"
# File path to the epub file. You can either give:
# - a file path relative to the data directory path `data_dirpath`, or
# - an absolute file path
epub_filepath = "The Governance of China by Xi Jinping - First Edition (2014).epub"
# epub_filepath = "The Governance of China by Xi Jinping - Second Edition (2018).epub"
pdf_filepath = "The Governance of China by Xi Jinping - First Edition (2014).pdf"

# -------------------------------
# Include: pages, notes, appendix
# -------------------------------
# Range of pages to analyze (inclusive)
# Example: ['0-5', '10-20', '30', '40-50', '100-last']
# Use `last` in the rage for the last page of the ebook
pages = ['28-30']
# Include also the captions below pictures
include_picture_captions = False
# Include also the notes in the analysis
include_notes = False
# Include also the appendix in the analysis
include_appendix = False

# ----------------
# Tokenizer config
# ----------------
# Type of tokenizer
tokenizer = 'TreebankWordTokenizer'
remove_punctuations = True
remove_stopwords = True
