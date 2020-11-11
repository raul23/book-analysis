# -- PDFBook setup -----------------------------------------------------------

# Data directory path where the pdf files are saved
data_dirpath = "~/Data/book-analysis"

# File path to the ebook file. You can either give:
# - a file path RELATIVE to the data directory path `data_dirpath`, or
# - an ABSOLUTE file path
pdf_filepath = "The Governance of China by Xi Jinping - First Edition (2014).pdf"

book_title = 'The Governance of China by Xi Jinping'

# Tokenizer config
TOKENIZER = {
    'CATEGORY': 'TreebankWordTokenizer',
    'PREPROCESSING': {
        'lower_text': True,
        'replace': [("\t", " ")]
    },
    'FILTERS': {
        'remove_punctuations': True,
        'remove_stopwords': True
    },
    'SAVE_TOKENS': {
        'per_book': True,
        'per_page': True
    }
}

# Cache results from book analysis, e.g. list of tokens. If cache is enabled,
# past results will be reused but only if the ... TODO
CACHE = {
    'ENABLE_CACHE': True,
    'DATA_TO_CACHE': {
        'lexicon': True,
        'pages': True,
        'word_counts': True
    }
}


# -- PDFBook.analyze() -------------------------------------------------------

# Range of pages to process (inclusive)
# Example: ['0-5', '10-20', '30', '40-50', '100-last']
# Use `last` in the range for the last page of the ebook
pages = ['28-30']

# What book parts to include in the book processing
include_book_parts = {
    'include_appendix': False,
    'include_notes': False,
    'include_picture_captions': False
}

# Tokens shuffling
# Otherwise, tokens will be sorted
shuffle_tokens = False
random_seed = 1234


# -- PDFBook.save_pickle() ---------------------------------------------------

save_pickle = True
# File path where the Pickle file will be saved
pickle_filepath = "pdfbook.pkl"


# -- PDFBook.save_report() ---------------------------------------------------

save_report = True

# File path where the report will be saved
# TODO: specify other type of reports (e.g. json)
report_filepath = "../docs/report.rst"

filter_words_in_report = {
    'k_most_common': 50,
    'k_least_common': 50
}
