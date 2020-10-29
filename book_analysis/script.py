from book import PDFBook
from genutils import config, load_pickle, save_pickle

import ipdb


if __name__ == '__main__':
    pickle_fp = 'test.pkl'
    # book = load_pickle(pickle_fp)
    book = PDFBook(**config.settings)
    report = book.analyze(config.settings.get('pages'), 'rst')
    ipdb.set_trace()
    save_pickle(book, pickle_fp)
    ipdb.set_trace()
    book.save_report("../docs/report2.rst")
    # Pictures with captions: ['168-183', '345-356']
    # p.227, no Notes title
    book.close()
