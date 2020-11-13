from governance_of_china import GovernancePDFBook
from genutils import config, load_pdf_book, save_pickle

import ipdb

# For debugging loading pickle files
LOAD = True


if __name__ == '__main__':
    # For debugging: testing loading a pickle instance of PDFBook
    if LOAD:
        ipdb.set_trace()
        book = load_pdf_book(config.settings.get('pickle_filepath'))
        report = book.analyze(pages=['28-50'])

        ipdb.set_trace()

        report = book.analyze(
            **config.settings.get('include_book_parts'),
            pages=['45', '50-55'],
            shuffle_tokens=config.settings.get('shuffle_tokens'),
            random_seed=config.settings.get('random_seed')
        )

        ipdb.set_trace()

    # Instantiate PDFBook
    book = GovernancePDFBook(
        pdf_filepath=config.settings.get('pdf_filepath'),
        book_title=config.settings.get('book_title'),
        tokenizer_cfg=config.settings.get('TOKENIZER'),
        cache_cfg=config.settings.get('CACHE')
    )

    # Analyze book
    report = book.analyze(
        **config.settings.get('include_book_parts'),
        pages=config.settings.get('pages'),
        shuffle_tokens=config.settings.get('shuffle_tokens'),
        random_seed=config.settings.get('random_seed')
    )

    ipdb.set_trace()

    book.enable_cache = False
    book.tokenizer_cfg['PREPROCESSING']['lower_text'] = False
    book.analyze(
        include_appendix=False,
        pages=['30-31'],
        shuffle_tokens=config.settings.get('shuffle_tokens'),
        random_seed=config.settings.get('random_seed')
    )

    ipdb.set_trace()

    book.enable_cache = True
    book.analyze(
        **config.settings.get('include_book_parts'),
        pages=['35-40'],
        shuffle_tokens=config.settings.get('shuffle_tokens'),
        random_seed=config.settings.get('random_seed')
    )

    ipdb.set_trace()

    book.enable_cache = True
    book.analyze(
        **config.settings.get('include_book_parts'),
        pages=['35-40'],
        shuffle_tokens=config.settings.get('shuffle_tokens'),
        random_seed=config.settings.get('random_seed')
    )

    # Pickle book object and save it
    if config.settings.get('save_pickle'):
        save_pickle(book, config.settings.get('pickle_filepath'))

    # Save report
    if config.settings.get('save_report'):
        book.save_report(
            **config.settings.get('filter_words_in_report'),
            filepath=config.settings.get('report_filepath'))

    ipdb.set_trace()

    # TODO: necessary?
    book.close()
