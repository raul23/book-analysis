import os
import re
import string
from collections import Counter

import nltk
from nltk.tokenize import TreebankWordTokenizer
import pdfplumber
import ipdb

from genutils import config

GET_TOKENIZER = {'TreebankWordTokenizer': TreebankWordTokenizer}


def cleanup_tokens(tokens, remove_puncs=True, remove_stopwords=True):
    tokens_to_remove = set()
    puncs1 = ['``', '--', "''"]
    puncs2 = [p for p in string.punctuation]
    # diff_puncs1_puncs2 = set(puncs1).difference(puncs2)
    # diff_puncs2_puncs1 = set(puncs2).difference(puncs1)
    nltk.download('stopwords', quiet=True)
    stopwords = nltk.corpus.stopwords.words('english')
    if remove_puncs:
        tokens_to_remove.update(set(puncs1))
        tokens_to_remove.update(set(puncs2))
    if remove_stopwords:
        tokens_to_remove.update(set(stopwords))
    cleaned_tokens = [token for token in tokens if token not in tokens_to_remove]
    # diff = set(tokens).difference(cleaned_tokens)
    return cleaned_tokens


class Page:
    def __init__(self, page_number, page_type, page_tokens):
        self.page_number = page_number
        self.page_type = page_type
        self.page_tokens = page_tokens

    def __repr__(self):
        return "<Page:{}>".format(self.page_number)


class PDFBook:
    def __init__(self, pdf_filepath, title='__auto__', tokenizer='TreebankWordTokenizer',
                 remove_puncs=True, remove_stopwords=True, enable_cache=True):
        self.pdf_filepath = pdf_filepath
        if title == '__auto__':
            self.title = os.path.basename(pdf_filepath).split('.pdf')
        else:
            self.title = title
        self.pdf = pdfplumber.open(pdf_filepath)
        self.number_pages = len(self.pdf.pages)
        self.tokenizer_name = tokenizer
        self.tokenizer = GET_TOKENIZER.get(tokenizer, TreebankWordTokenizer)()
        self.remove_puncs = remove_puncs
        self.remove_stopwords = remove_stopwords
        self.enable_cache = enable_cache
        # e.g. October 23, 2014
        # TODO: make date regex more precise
        self.date_regex = r"([a-zA-Z]+) (\d{1,2}), (\d\d\d\d)"
        self.pages = {}
        self.cached_pages = {}
        self.all_page_numbers = set()
        self.book_tokens = []
        self.lexicon = set()
        self.word_counts = {}
        self.last_saved_config = {}

    # pages = ['0-5', '10', '20-22', '30', '80-last']
    def analyze(self, pages=None):
        report = ""
        self.all_page_numbers = self._get_all_page_numbers(pages)
        use_cache = False if self._setup_cache() == 1 else True
        if self.pages:
            # Nothing changed. Two configs (previous and current) are identical
            return report
        # TODO: use thread (multiprocess?)
        for page_number in self.all_page_numbers:
            # TODO: add progress bar
            print(page_number)
            if use_cache:
                page = self.cached_pages.get(page_number)
                if page:
                    # Page found in cache
                    self.pages.setdefault(page_number, page)
                    self.book_tokens += page.page_tokens
                    continue
                else:
                    # Page NOT found in cache
                    # TODO: add logging
                    pass
            page = self.pdf.pages[page_number - 1]
            # pdf-to-text conversion
            text = page.extract_text()
            if text:
                # Text found on given page
                text = page.extract_text().replace("\t", " ")
                page_type = self._get_page_type(text)
                page_tokens = cleanup_tokens(
                    tokens=self.tokenizer.tokenize(text.lower()),
                    remove_puncs=self.remove_puncs,
                    remove_stopwords=self.remove_stopwords)
                self.pages.setdefault(page_number, Page(page_number, page_type, page_tokens))
                self.book_tokens += page_tokens
            else:
                # No text found on given page
                # TODO: add logging instead of pass
                pass
        self.book_tokens = sorted(self.book_tokens)
        self.word_counts = Counter(self.book_tokens)
        self.lexicon = sorted(set(self.book_tokens))
        self._save_config()
        self._cache_pages()
        return report

    def close(self):
        # TODO: reset book data and cache
        self.pdf.close()

    def _cache_pages(self):
        self.cached_pages.update(self.pages)

    def _diff_between_configs(self):
        # Get current config
        difference = []
        current_config = self._get_config()
        if not self.last_saved_config:
            return current_config
        for config_name, current_config_value in current_config.items():
            if self.last_saved_config[config_name] != current_config_value:
                difference.append(config_name)
        return difference

    def _get_all_page_numbers(self, pages):
        all_page_numbers = []
        for page_range in pages:
            page_range = page_range.replace('last', str(self.number_pages))
            range_ends = page_range.split("-")
            page_numbers = self._get_page_numbers_from_range(range_ends)
            all_page_numbers += page_numbers
        return sorted(set(all_page_numbers))

    def _get_config(self):
        _config = {}
        attr_names_to_keep = ['all_page_numbers', 'pdf_filepath', 'remove_puncs',
                              'remove_stopwords', 'tokenizer_name']
        for k, v in self.__dict__.items():
            if k in attr_names_to_keep:
                _config[k] = v
        return _config

    # range_ends is a list, e.g. ['0-5', '10', '20-22', '30', '80-last']
    # or ['2'] or ['last']
    # returns a list, e.g. ['1']
    def _get_page_numbers_from_range(self, range_ends):
        if len(range_ends) == 2:
            low_end = int(range_ends[0])
            high_end = int(range_ends[1])
            # Inclusive both ends
            page_numbers = range(low_end, high_end + 1)
        elif len(range_ends) == 1:
            low_end = int(range_ends[0])
            high_end = low_end
            page_numbers = [int(low_end)]
        else:
            # TODO: add error message
            raise ValueError("")
        assert low_end <= high_end, \
            "Invalid page range: [{}-{}]".format(low_end, high_end)
        assert low_end > 0, "Page number can't be 0"
        assert high_end <= self.number_pages, \
            "Invalid page number: {} is higher than the total number of pages " \
            "({})".format(high_end, self.number_pages)
        return page_numbers

    def _get_page_type(self, text):
        page_type = ""
        if text.count("\n") == 2 and "." not in text:
            page_type = "titled_page"
        elif "*" in text and re.search(self.date_regex, text):
            page_type = "start_speech_page"
        elif text.find("Notes") != -1 and text.find("[1]") != -1:
            page_type = "start_notes_page"
        elif "Appendix" == text.split("\n")[-1]:
            page_type = "appendix_page"
        else:
            pass
        return page_type

    def _reset_book_data(self):
        self.pages = {}
        self.book_tokens = []
        self.lexicon = set()
        self.word_counts = {}

    def _save_config(self):
        self.last_saved_config = self._get_config()

    def _setup_cache(self):
        retcode = 1
        if self.enable_cache:
            diff = self._diff_between_configs()
            if len(diff) == 0:
                retcode = 0
            elif len(diff) == 1 and diff[0] == 'all_page_numbers':
                retcode = 0
                self._reset_book_data()
            else:
                retcode = 1
        if retcode == 1:
            # Reset cache
            self.cached_pages = {}
            self._reset_book_data()
        return retcode

    def __repr__(self):
        return "<Book:{}>".format(os.path.basename(self.pdf_filepath))


if __name__ == '__main__':
    book = PDFBook(pdf_filepath=config.pdf_filepath,
                   tokenizer=config.tokenizer,
                   remove_puncs=config.remove_punctuations,
                   remove_stopwords=config.remove_stopwords,
                   enable_cache=config.enable_cache)
    book.analyze(config.pages)
    book.analyze(['30-35'])
    book.analyze(['36-38'])
    ipdb.set_trace()
    book.analyze(['30-38'])
    ipdb.set_trace()
    book.close()
