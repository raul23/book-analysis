CACHE = {
    'ENABLE_CACHE': True,
    'DATA_TO_CACHE': {
        'cache_pages': True,
        'cache_lexicon': False,
        'cache_word_counts': False
    }
}

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
        'per_book': False,
        'per_page': True
    }
}
