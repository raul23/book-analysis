import copy
import json
import os
import random
from collections import Counter

import pdfplumber
import ipdb

from default_values import CACHE, TOKENIZER
from genutils import Cache
from nlputils import Tokenizer


# Cache field names
CACHE_LEXICON = 'lexicon'
CACHE_LEXICON_PN = 'lexicon_page_numbers'
CACHE_PAGES = 'pages'
CACHE_WORD_COUNTS_PN = 'word_counts_page_numbers'
CACHE_WORD_COUNTS = 'word_counts'


class Page:
    def __init__(self, page_number, page_type, page_tokens):
        self.page_number = page_number
        self.page_tokens = page_tokens
        # Private because it works only for one specific book
        self._page_type = page_type

    def __repr__(self):
        return "<Page:{}>".format(self.page_number)


class PDFBook:
    def __init__(self, pdf_filepath, book_title='__auto__',
                 tokenizer_cfg=TOKENIZER, cache_cfg=CACHE):
        self.pdf_filepath = pdf_filepath
        if book_title == '__auto__':
            self.book_title = os.path.basename(pdf_filepath).split('.pdf')[0]
        else:
            self.book_title = book_title
        # TODO: log loading msg
        print('Loading "{}" ...'.format(self.book_title))
        self.pdf = pdfplumber.open(pdf_filepath)
        self.total_number_pages = len(self.pdf.pages)
        self.save_tokens = None
        self.tokenizer_cfg = None
        self.tokenizer = None
        self.update_tokenizer(tokenizer_cfg)
        # Pages where text was found and tokens extracted
        self.pages = {}
        self.book_tokens = self._init_book_tokens()
        # Pages that are processed, i.e. text and tokens extracted
        self.processed_page_numbers = set()
        # Include book parts
        self.include_appendix = False
        self.include_notes = False
        self.include_picture_captions = False
        # Create cache
        self.cache_cfg = cache_cfg
        self.enable_cache = cache_cfg.get('ENABLE_CACHE', True)
        self.cache = Cache(self._init_cache())
        # e.g. October 23, 2014
        # TODO: explain this attribute
        self.last_saved_config = {}
        # TODO: explain these private attributes
        # TODO: make date regex more precise
        self._date_regex = r"([a-zA-Z]+) (\d{1,2}), (\d\d\d\d)"
        self._default_explore_nb_pages = 2
        self._explore_nb_pages = 2
        self._enable_tokens_shuffling = True
        self._random_seed = None
        # Must not be altered by users
        self._report = None

    # pages = ['0-5', '10', '20-22', '30', '80-last']
    def analyze(self, pages, include_appendix=False, include_notes=False,
                include_picture_captions=False, shuffle_tokens=True,
                random_seed=None):
        self._explore_nb_pages = self._default_explore_nb_pages
        self.processed_page_numbers = set()
        self.include_appendix = include_appendix
        self.include_notes = include_notes
        self.include_picture_captions = include_picture_captions
        self.processed_page_numbers = self._get_page_numbers_to_process(pages)
        self._setup_cache()
        if self.pages and list(self.pages.keys()) == self.processed_page_numbers:
            # Nothing changed. Two configs (previous and current) are identical
            # TODO: add logging for assert
            assert self._report is not None
            return self._report
        else:
            # TODO: assert that self.book_tokens should be empty
            # TODO: use thread (multiprocess?)
            print("\nProcessing {} pages".format(len(self.processed_page_numbers)))
            for page_number in self.processed_page_numbers:
                # TODO: add progress bar
                print("Page {} ...".format(page_number))
                # Check first in self.pages
                page = self.pages.get(page_number)
                if page:
                    # Page found in self.pages
                    self._update_book_tokens(page_number, page.page_tokens)
                    continue
                # Not found in self.pages
                # Then, check in cache
                page = self.cache.get_item(page_number, CACHE_PAGES)
                if page:
                    # Page found in cache
                    self._update_pages(page)
                    self._update_book_tokens(page_number, page.page_tokens)
                    continue
                else:
                    # Page NOT found in cache
                    # TODO: add logging
                    pass
                # Page neither found in cache nor in self.pages
                # Then, process page from PDF book to extract tokens
                pdf_page = self.pdf.pages[page_number - 1]
                if pdf_page.images and not include_picture_captions:
                    # Text caption for image to be ignored
                    # TODO: add logging that text will be skipped because it
                    # is part of an image's caption
                    continue
                # pdf-to-text conversion
                text = pdf_page.extract_text()
                if text:
                    # Text found on given page
                    text = self._preprocessing(text)
                    page_type = self._get_page_type(text, page_number)
                    # TODO (IMPORTANT): problem if beginning analysis from an
                    # appendix page that is not the titled appendix page
                    if page_type.endswith('appendix_page') and \
                            not include_appendix:
                        # Ignore appendix page
                        # TODO: add logging that we are ignoring an appendix page
                        break
                    elif page_type == 'next_notes_page' and \
                            not include_notes:
                        # Ignore notes-only page
                        # TODO: add logging that we are ignoring a notes-only page
                        continue
                    elif page_type == 'start_notes_page':
                        notes_pos = text.find("Notes")
                        text = text[:notes_pos]
                        if text:
                            page_type = 'next_speech_page_and_' + page_type
                    page_tokens = self.tokenizer.tokenize(
                        text=text, **self.tokenizer_cfg['FILTERS'])
                    self._update_book_tokens(page_number, page_tokens)
                    page = Page(page_number, page_type, page_tokens)
                    self._update_pages(page)
                    self._update_pages_to_cache(page)
                else:
                    # No text found on given page
                    # TODO: add logging instead of pass
                    pass
            # TODO: assert len(self.book_tokens) == sum(page_tokens from each page in self.pages)
            if shuffle_tokens:
                if random_seed:
                    random.seed(random_seed)
                random.shuffle(self.book_tokens['tokens'])
            else:
                self.book_tokens['tokens'] = sorted(self.book_tokens['tokens'])
            self._save_config()
        self._report = self.get_report('dict')
        return self._report

    def close(self):
        # TODO: reset book data and cache
        self.pdf.close()

    def get_lexicon(self):
        return sorted(set(self.book_tokens['tokens']))

    def get_report(self, report_type='dict', k_most_common=25, k_least_common=25):
        if self._report:
            report = self._report
            if len(report['most_common_words']) != k_most_common:
                most_common = self.get_most_common_words(k_most_common)
                report.update({'most_common_words': most_common})
            if len(report['least_common_words']) != k_least_common:
                least_common = self.get_least_common_words(k_least_common)
                report.update({'least_common_words': least_common})
        else:
            report = {}
            attrs_to_include = [str, bool, int, float]
            for k, v in self.__dict__.items():
                # No private attributes
                if not k.startswith('_') and type(v) in attrs_to_include:
                    report.setdefault(k, v)
            report.setdefault("number_pages_processed", len(self.processed_page_numbers))
            report.setdefault("number_tokens_extracted", len(self.book_tokens['tokens']))
            # TODO: use lexicon from cache if it is already there
            lexicon = sorted(set(self.book_tokens['tokens']))
            report.setdefault("lexicon_size", len(lexicon))
            most_common = self.get_most_common_words(k_most_common)
            least_common = self.get_least_common_words(k_least_common)
            report.setdefault("most_common_words", most_common)
            report.setdefault("least_common_words", least_common)
            report.setdefault("tokenizer_category", self.tokenizer.category)
            report.setdefault("remove_punctuations", self.tokenizer_cfg['FILTERS']['remove_punctuations'])
            report.setdefault("remove_stopwords", self.tokenizer_cfg['FILTERS']['remove_stopwords'])
        if report_type == 'rst':
            return self._convert_report_to_rst(report)
        elif report_type == 'json':
            return json.dumps(report)
        else:
            return report

    def get_least_common_words(self, k_least_common):
        return self.get_word_counts().most_common()[-k_least_common:]

    def get_most_common_words(self, k_most_common):
        return self.get_word_counts().most_common(k_most_common)

    def get_word_counts(self):
        return Counter(self.book_tokens['tokens'])

    def save_report(self, filepath, k_most_common=25, k_least_common=25):
        report_type = self._get_report_type_from_file(filepath)
        report = self.get_report(report_type, k_most_common, k_least_common)
        with open(filepath, 'w') as f:
            if report_type == 'json':
                json.dump(report, f)
            elif report_type == 'rst':
                f.write(report)
            else:
                # TODO: raise error: unsupported report file extension
                pass

    def update_tokenizer(self, tokenizer_cfg):
        self.save_tokens = tokenizer_cfg.pop('SAVE_TOKENS')
        self.tokenizer_cfg = tokenizer_cfg
        self.tokenizer = Tokenizer(
            category=tokenizer_cfg.get('CATEGORY', 'TreebankWordTokenizer'))

    @staticmethod
    def _convert_report_to_rst(report):
        def get_msg(msg_type):
            msg_types = {
                'appendix': ('Appendix {}included', report['include_appendix']),
                'notes': ('Notes {}included', report['include_notes']),
                'captions': ('Picture captions {}included', report['include_picture_captions']),
                'puncs': ('Punctuations {}removed', report['remove_punctuations']),
                'stopwords': ('Stopwords {}removed', report['remove_stopwords'])}
            msg_type = msg_types[msg_type]
            msg = msg_type[0]
            cond = msg_type[1]
            return msg.format("") if cond else msg.format("not ")

        def get_rst_common_list(common_type):
            if common_type == 'most':
                # TODO: sort according to word occurrences ???
                word_counts = report['most_common_words']
            else:
                # TODO: sort according to word occurrences (fine if all 1)
                word_counts = sorted(report['least_common_words'])
            msg = ""
            for word, count in word_counts:
                # TODO: remove newline if last item. Then add newline in report after {most_common_words_list}
                msg += "- {}: {}\n".format(word, count)
            return msg

        most_common_line = "{} most common words".format(len(report['most_common_words']))
        least_common_line = "{} least common words".format(len(report['least_common_words']))
        report = """======
    Report
    ======
    - **Title:** {title}
    - **Total number of pages:** {total_number_pages}
    - **Tokenizer:** {tokenizer}
    - **Number of pages processed:** {nb_pages_processed}
    - **Number of tokens extracted:** {nb_tokens_extracted}
    - **Size of lexicon:** {lexicon_size}
    - **{remove_punctuations}**
    - **{remove_stopwords}**
    - **{include_picture_captions}**
    - **{include_notes}**
    - **{include_appendix}**

    {most_common_line}
    {n_dashes_most_common}
    {most_common_words_list}
    {least_common_line}
    {n_dashes_least_common}
    {least_common_words_list}""".format(
            title=report['book_title'],
            total_number_pages=report['total_number_pages'],
            tokenizer=report['tokenizer_category'],
            nb_pages_processed=report['number_pages_processed'],
            nb_tokens_extracted=report['number_tokens_extracted'],
            lexicon_size=report['lexicon_size'],
            remove_punctuations=get_msg('puncs'),
            remove_stopwords=get_msg('stopwords'),
            include_picture_captions=get_msg('captions'),
            include_notes=get_msg('notes'),
            include_appendix=get_msg('appendix'),
            most_common_line=most_common_line,
            n_dashes_most_common=len(most_common_line) * "-",
            most_common_words_list=get_rst_common_list('most'),
            least_common_line=least_common_line,
            n_dashes_least_common=len(least_common_line) * '-',
            least_common_words_list=get_rst_common_list('least')
        )
        return report

    def _diff_between_configs(self):
        # Get current config
        difference = []
        current_config = self._get_config()
        if not self.last_saved_config:
            return list(current_config.keys())
        for config_name, current_config_value in current_config.items():
            if self.last_saved_config[config_name] != current_config_value:
                difference.append(config_name)
        return difference

    @staticmethod
    def _find_items_in_list(items, _list):
        for item in items:
            if item in _list:
                return True
        return False

    def _get_config(self):
        _config = {}
        # TODO: use MD5 instead of pdf_filepath to check if you are processing the same ebook again
        attr_names_to_keep = ['pdf_filepath', 'processed_page_numbers',
                              'include_appendix', 'include_notes',
                              'include_picture_captions', 'tokenizer_cfg']
        for k, v in self.__dict__.items():
            if k in attr_names_to_keep:
                _config[k] = copy.deepcopy(v)
        # TODO: log msg for assert
        assert len(_config) == len(attr_names_to_keep)
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
        assert high_end <= self.total_number_pages, \
            "Invalid page number: {} is higher than the total number of pages " \
            "({})".format(high_end, self.total_number_pages)
        return page_numbers

    def _get_page_numbers_to_process(self, pages):
        page_numbers_to_process = []
        for page_range in pages:
            page_range = page_range.replace('last', str(self.total_number_pages))
            range_ends = page_range.split("-")
            page_numbers = self._get_page_numbers_from_range(range_ends)
            page_numbers_to_process += page_numbers
        # TODO: explain why page numbers should be unique (avoid processing the same page more than once)
        return sorted(set(page_numbers_to_process))

    @staticmethod
    def _get_page_type(text, page_number):
        return None

    @staticmethod
    def _get_report_type_from_file(filepath):
        ext = filepath.split('.')[-1]
        if ext in ['', 'json']:
            # No extension defaults to json file
            return 'json'
        elif ext == 'rst':
            return 'rst'
        else:
            # TODO: raise error: unsupported report file extension
            raise ValueError("")

    @staticmethod
    def _init_book_tokens():
        return {'page_numbers': set(), 'tokens': []}

    @staticmethod
    def _init_cache():
        return {CACHE_PAGES: {},
                CACHE_LEXICON: set(),
                CACHE_LEXICON_PN: set(),
                CACHE_WORD_COUNTS: Counter(),
                CACHE_WORD_COUNTS_PN: set()}

    def _preprocessing(self, text):
        if self.tokenizer_cfg['PREPROCESSING'].get('lower_text', True):
            text = text.lower()
        replacements = self.tokenizer_cfg['PREPROCESSING'].get('replace')
        if replacements:
            for old, new in replacements:
                text = text.replace(old, new)
        return text

    def _reset_book_data(self, keep_pages=False):
        if keep_pages:
            pages = {}
            for k, v in self.pages.items():
                if k in self.processed_page_numbers:
                    pages.setdefault(k, v)
            self.pages = pages
        else:
            self.pages = {}
        self.book_tokens = self._init_book_tokens()
        self._report = None

    def _save_config(self):
        self.last_saved_config = self._get_config()

    def _setup_cache(self):
        # TODO: log assert msg error
        assert len(self.processed_page_numbers)
        # Difference between current config and last saved config
        diff = self._diff_between_configs()
        if len(diff) == 0:
            case = 'no_diff'
        elif self._find_items_in_list(['tokenizer_cfg', 'pdf_filepath'], diff):
            case = 'reset_everything'
        else:
            # Keep necessary pages in self.pages
            case = 'reset_book_data'
        if self.enable_cache:
            # Use cache
            if case == 'no_diff':
                # No difference between configs
                # TODO: log msg
                self._update_pages_to_cache(self.pages)
                # return 0
            elif case == 'reset_everything':
                # Tokenizer config changed
                # Reset cache
                self.cache.reset_cache(self._init_cache())
                self._reset_book_data()
                # TODO: log msg
                # return 1
            else:
                # e.g. process_page_numbers changed
                self._update_pages_to_cache(self.pages)
                self._reset_book_data(True)
                # TODO: log msg
                # return 0
        else:
            # Don't use cache
            if case == 'reset_everything':
                # Tokenizer config changed
                self.cache.reset_cache(self._init_cache())
                self._reset_book_data()
                # TODO: log msg
            elif case == 'reset_book_data':
                # e.g. process_page_numbers changed
                self._reset_book_data(True)
                # TODO: log msg
            else:
                # TODO: log msg
                pass
            # return 1

    def _update_book_tokens(self, page_number, page_tokens):
        if self.save_tokens.get('per_book'):
            if page_number not in self.book_tokens['page_numbers']:
                self.book_tokens['page_numbers'].add(page_number)
                self.book_tokens['tokens'] += page_tokens
            else:
                # TODO: add logging (page number already processed)
                pass

    def _update_cache(self, data_type, page):
        if self.enable_cache and self.cache_cfg['DATA_TO_CACHE'].get(data_type):
            # Check first duplicate page numbers
            if data_type == CACHE_LEXICON and \
                    self.cache.find_item(page.page_number, CACHE_LEXICON_PN):
                # TODO: log msg (duplicate lexicon, page number already found)
                pass
            elif data_type == CACHE_PAGES and \
                    self.cache.find_item(page.page_number, CACHE_PAGES):
                # TODO: log msg (duplicate pages, page number already found)
                pass
            elif data_type == CACHE_WORD_COUNTS and \
                    self.cache.find_item(page.page_number, CACHE_WORD_COUNTS_PN):
                # TODO: log msg (duplicate word counts, page number already found)
                pass
            else:
                data = {}
                if data_type == CACHE_LEXICON:
                    data = set(page.page_tokens)
                    self.cache.update_cache({page.page_number}, CACHE_LEXICON_PN)
                elif data_type == CACHE_PAGES:
                    data = {page.page_number: page}
                elif data_type == CACHE_WORD_COUNTS:
                    data = Counter(page.page_tokens)
                    self.cache.update_cache({page.page_number}, CACHE_WORD_COUNTS_PN)
                else:
                    # TODO: add logging (Error)
                    pass
                #  Specify that data should be a dict or set (with update function)
                self.cache.update_cache(data, data_type)

    def _update_pages(self, page):
        if not self.save_tokens.get('per_page'):
            page.page_tokens = []
        self.pages.update({page.page_number: page})

    def _update_pages_to_cache(self, pages):
        data_types = [CACHE_LEXICON, CACHE_PAGES, CACHE_WORD_COUNTS]
        if isinstance(pages, Page):
            pages = {pages.page_number: pages}
        for page_number, page in pages.items():
            for dt in data_types:
                self._update_cache(dt, page)

    def __repr__(self):
        return "<Book:{}>".format(os.path.basename(self.pdf_filepath))
