import json
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


def cleanup_tokens(tokens, remove_punctuations=True, remove_stopwords=True):
    tokens_to_remove = set()
    puncs1 = ['``', '--', "''"]
    puncs2 = [p for p in string.punctuation]
    # diff_puncs1_puncs2 = set(puncs1).difference(puncs2)
    # diff_puncs2_puncs1 = set(puncs2).difference(puncs1)
    nltk.download('stopwords', quiet=True)
    stopwords = nltk.corpus.stopwords.words('english')
    if remove_punctuations:
        tokens_to_remove.update(set(puncs1))
        tokens_to_remove.update(set(puncs2))
    if remove_stopwords:
        tokens_to_remove.update(set(stopwords))
    cleaned_tokens = [token for token in tokens if token not in tokens_to_remove]
    # diff = set(tokens).difference(cleaned_tokens)
    return cleaned_tokens


class Page:
    def __init__(self, page_number, page_type, page_tokens, text):
        self.page_number = page_number
        self.page_type = page_type
        self.page_tokens = page_tokens
        self.text = text

    def __repr__(self):
        return "<Page:{}>".format(self.page_number)


class PDFBook:
    def __init__(self, pdf_filepath, title='__auto__',
                 tokenizer='TreebankWordTokenizer', remove_punctuations=True,
                 remove_stopwords=True, include_picture_captions=False,
                 include_notes=False, include_appendix=False, enable_cache=True,
                 **kwargs):
        self.pdf_filepath = pdf_filepath
        if title == '__auto__':
            self.title = os.path.basename(pdf_filepath).split('.pdf')[0]
        else:
            self.title = title
        self.pdf = pdfplumber.open(pdf_filepath)
        self.total_number_pages = len(self.pdf.pages)
        self.tokenizer_name = tokenizer
        self.tokenizer = GET_TOKENIZER.get(tokenizer, TreebankWordTokenizer)()
        self.remove_punctuations = remove_punctuations
        self.remove_stopwords = remove_stopwords
        self.include_picture_captions = include_picture_captions
        self.include_notes = include_notes
        self.include_appendix = include_appendix
        self.enable_cache = enable_cache
        # e.g. October 23, 2014
        # TODO: make date regex more precise
        self.date_regex = r"([a-zA-Z]+) (\d{1,2}), (\d\d\d\d)"
        # Pages where text was found and tokens extracted
        self.pages = {}
        self.cached_pages = {}
        # Pages that were processed, i.e. text and tokens extracted
        self.processed_page_numbers = set()
        self.book_tokens = []
        self.lexicon = set()
        self.word_counts = {}
        self.last_saved_config = {}

    # pages = ['0-5', '10', '20-22', '30', '80-last']
    def analyze(self, pages=None, report_type='json', topk_words=25,
                bottomk_words=25):
        self.processed_page_numbers = self._get_page_numbers_to_process(pages)
        use_cache = False if self._setup_cache() == 1 else True
        if not self.pages:
            # TODO: use thread (multiprocess?)
            for page_number in self.processed_page_numbers:
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
                if page.images and not self.include_picture_captions:
                    # Text caption for image to be ignored
                    # TODO: add logging that text will be skipped because it is part of an image's caption
                    continue
                # pdf-to-text conversion
                text = page.extract_text()
                if text:
                    # Text found on given page
                    text = text.replace("\t", " ")
                    page_type = self._get_page_type(text, page_number)
                    page_tokens = cleanup_tokens(
                        tokens=self.tokenizer.tokenize(text.lower()),
                        remove_punctuations=self.remove_punctuations,
                        remove_stopwords=self.remove_stopwords)
                    self.pages.setdefault(
                        page_number,
                        Page(page_number, page_type, page_tokens, text))
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
        else:
            # Nothing changed. Two configs (previous and current) are identical
            # TODO: add logging instead of pass
            pass
        return self.get_report(report_type, topk_words, bottomk_words)

    def close(self):
        # TODO: reset book data and cache
        self.pdf.close()

    def get_report(self, report_type='dict', k_most_common=25, k_least_common=25):
        if report_type == 'rst':
            return self._get_rst_report(k_most_common, k_least_common)
        else:
            report = {}
            # TODO: it is simpler to just ignore all keys that are neither
            # Boolean nor alphanumeric
            keys_to_ignore = {'pdf', 'tokenizer', 'date_regex', 'pages',
                              'cached_pages', 'book_tokens', 'word_counts',
                              'lexicon', 'last_saved_config', 'report'}
            for k, v in self.__dict__.items():
                if k in keys_to_ignore:
                    continue
                report.setdefault(k, v)
            most_common = self.word_counts.most_common(k_most_common)
            least_common = self.word_counts.most_common()[-k_least_common:]
            report.setdefault("most_common_words", most_common)
            report.setdefault("least_common_words", least_common)
            if report_type == 'json':
                return json.dumps(report)
            else:
                return report

    @staticmethod
    def _get_report_type_from_file(filepath):
        ext = filepath.split('.')[1]
        if ext in ['', 'json']:
            # No extension defaults to json file
            return 'json'
        elif ext == 'rst':
            return 'rst'
        else:
            # TODO: raise error: unsupported report file extension
            raise ValueError("")

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

    def _get_rst_report(self, k_most_common, k_least_common):
        def get_include_appendix_msg():
            msg = "Appendix {} included"
            return msg.format("was") if self.include_notes else \
                msg.format("was not")

        def get_include_notes_msg():
            msg = "Notes {} included"
            return msg.format("were") if self.include_appendix else \
                msg.format("were not")

        def get_removed_puncs_msg():
            msg = "Punctuations {} removed"
            return msg.format("were") if self.remove_punctuations else \
                msg.format("were not")

        def get_removed_stopwords_msg():
            msg = "Stopwords {} removed"
            return msg.format("were") if self.remove_punctuations else \
                msg.format("were not")

        def get_rst_least_common_list():
            msg = ""
            for word, count in self.word_counts.most_common()[-k_least_common:]:
                msg += "- {}: {}\n".format(word, count)
            return msg

        def get_rst_most_common_list():
            msg = ""
            for word, count in self.word_counts.most_common(k_most_common):
                msg += "- {}: {}\n".format(word, count)
            return msg

        most_common_line = "{} most common words".format(k_most_common)
        least_common_line = "{} least common words".format(k_least_common)
        report = """======
Report
======
- **Title:** {title}
- **Total number of pages:** {total_number_pages}
- **Tokenizer:** {tokenizer}
- **Number of pages processed:** {nb_pages_processed}
- **{remove_punctuations}**
- **{remove_stopwords}**
- **{include_notes}**
- **{include_appendix}**

{most_common_line}
{n_dashes_most_common}
{most_common_words_list}

{least_common_line}
{n_dashes_least_common}
{least_common_words_list}
""".format(
            title=self.title,
            total_number_pages=self.total_number_pages,
            tokenizer=self.tokenizer_name,
            nb_pages_processed=len(self.processed_page_numbers),
            remove_punctuations=get_removed_puncs_msg(),
            remove_stopwords=get_removed_stopwords_msg(),
            include_notes=get_include_notes_msg(),
            include_appendix=get_include_appendix_msg(),
            most_common_line=most_common_line,
            n_dashes_most_common=len(most_common_line) * "-",
            most_common_words_list=get_rst_most_common_list(),
            least_common_line=least_common_line,
            n_dashes_least_common=len(least_common_line) * '-',
            least_common_words_list=get_rst_least_common_list()
        )
        return report

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

    def _get_page_numbers_to_process(self, pages):
        page_numbers_to_process = []
        for page_range in pages:
            page_range = page_range.replace('last', str(self.total_number_pages))
            range_ends = page_range.split("-")
            page_numbers = self._get_page_numbers_from_range(range_ends)
            page_numbers_to_process += page_numbers
        return sorted(set(page_numbers_to_process))

    def _get_config(self):
        _config = {}
        attr_names_to_keep = ['processed_page_numbers', 'pdf_filepath',
                              'remove_puncs', 'remove_stopwords',
                              'tokenizer_name']
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
        assert high_end <= self.total_number_pages, \
            "Invalid page number: {} is higher than the total number of pages " \
            "({})".format(high_end, self.total_number_pages)
        return page_numbers

    def _get_page_type(self, text, page_number):
        page_type = "unknown"
        if "Appendix" == text.split("\n")[-1]:
            page_type = "start_appendix_page"
        elif text.count("\n") == 2 and "." not in text:
            page_type = "titled_page"
        elif "*" in text and re.search(self.date_regex, text):
            page_type = "start_speech_page"
        elif text.find("Notes") != -1 and text.find("[1]") != -1:
            page_type = "start_notes_page"
        else:
            prev_page_number = page_number - 1
            # TODO: treat case when page_number = 1
            prev_page = self.pages.get(prev_page_number)
            if prev_page:
                prev_page_type = prev_page.page_type
            else:
                prev_page = self.pdf.pages[prev_page_number - 1]
                prev_page_text = prev_page.extract_text()
                if not prev_page_text:
                    # TODO: catch this error (LookupError?)
                    raise LookupError("The type of the current page {} can't "
                                      "be identified because its previous page "
                                      "is empty.".format(page_number,
                                                         prev_page_number))
                prev_page_text = prev_page_text.replace("\t", " ")
                prev_page_type = self._get_page_type(prev_page_text,
                                                     prev_page_number)
                page_tokens = cleanup_tokens(
                    tokens=self.tokenizer.tokenize(prev_page_text.lower()),
                    remove_punctuations=self.remove_punctuations,
                    remove_stopwords=self.remove_stopwords)
                self.cached_pages.update({
                    prev_page_number: Page(prev_page_number, prev_page_type,
                                           page_tokens, prev_page_text)
                })
            if prev_page_type in ['start_speech_page', 'next_speech_page']:
                page_type = "next_speech_page"
            elif prev_page_type in ['start_notes_page', 'next_notes_page']:
                page_type = "next_notes_page"
            elif prev_page_type in ['start_appendix_page', 'next_appendix_page']:
                page_type = "next_appendix_page"
            else:
                # TODO: raise error (unknown page type)?
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
    book = PDFBook(**config.settings)
    report = book.analyze(config.settings.get('pages'), 'rst')
    ipdb.set_trace()
    # book.save_report("report.rst")
    # Pictures with captions
    book.analyze(['168-183', '345'])
    # p.227, no Notes title
    ipdb.set_trace()
    book.close()
