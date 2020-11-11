from book import PDFBook
from genutils import config, load_pickle, save_pickle

import ipdb


if __name__ == '__main__':
    # ipdb.set_trace()
    book = PDFBook(
        pdf_filepath=config.settings.get('pdf_filepath'),
        book_title=config.settings.get('book_title'),
        tokenizer_cfg=config.settings.get('TOKENIZER'),
        cache_cfg=config.settings.get('CACHE')
    )
    report = book.analyze(
        **config.settings.get('include_book_parts'),
        pages=config.settings.get('pages'),
        shuffle_tokens=config.settings.get('shuffle_tokens'),
        random_seed=config.settings.get('random_seed')
    )
    if config.settings.get('save_pickle'):
        save_pickle(book, config.settings.get('pickle_filepath'))
    if config.settings.get('save_report'):
        book.save_report(
            **config.settings.get('filter_words_in_report'),
            filepath=config.settings.get('report_filepath'))
    book.close()
    book = load_pickle(config.settings.get('pickle_filepath'))
    book.close()
