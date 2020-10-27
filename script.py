import re
import string
from collections import Counter

import nltk
from nltk.tokenize import TreebankWordTokenizer
import pdfplumber
import ipdb

from genutils import config


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


class Book:
    def __init__(self):
        self.pdf = pdfplumber.open(config.pdf_filepath)
        self.number_pages = len(self.pdf.pages)
        # e.g. October 23, 2014
        self.date_regex = r"([a-zA-Z]+) (\d{1,2}), (\d\d\d\d)"
        self.all_page_tokens = []

    # pages = ['0-5', '10', '20-22', '30', '80-last']
    def analyze(self, pages=None):
        all_page_numbers = self._get_all_page_numbers(pages)
        ipdb.set_trace()
        for page_number in all_page_numbers:
            page = self.pdf.pages[page_number - 1]
            # pdf-to-text conversion
            text = page.extract_text()
            if text:
                # Text found on given page
                text = page.extract_text().replace("\t", " ")
            else:
                # No text found on given page
                continue

    def close(self):
        self.pdf.close()

    def _get_all_page_numbers(self, pages):
        all_page_numbers = []
        for page_range in pages:
            page_range = page_range.replace('last', str(self.number_pages))
            range_ends = page_range.split("-")
            page_numbers = self._get_page_numbers_from_range(range_ends)
            all_page_numbers += page_numbers
        return all_page_numbers

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
            # TODO: error message
            raise ValueError("")
        # TODO: assert message
        assert low_end <= high_end, \
            "Invalid page range: [{}-{}]".format(low_end, high_end)
        assert low_end > 0, "Page number can't be 0"
        assert high_end <= self.number_pages, \
            "Invalid page number: {} is higher than the total number of pages " \
            "({})".format(high_end, self.number_pages)
        return page_numbers

    def _get_page_type(self, page_number):
        pass


if __name__ == '__main__':
    book = Book()
    book.analyze(config.pages)
    book.close()

    """
    pdf = pdfplumber.open(PDF_FP)
    tokenizer = TreebankWordTokenizer()
    regex = r"([a-zA-Z]+) (\d{1,2}), (\d\d\d\d)"
    found_start_page = False
    page_tokens = []
    all_page_tokens = []
    page = pdf.pages[343]
    pages_type = {}
    ipdb.set_trace()
    # for page in pdf.pages:
    for page in [page]:
        if not nb_pages:
            break
        if True or page.page_number == start_page:
            found_start_page = True
        if found_start_page:
            # pdf-to-text conversion
            # text = page.extract_text()
            text = page.extract_text().replace("\t", " ")
            if not pages_type.get(page.page_number - 1):
                prev_page = pdf.pages[page.page_number - 1]
                prev_page_text = prev_page.extract_text().replace("\t", " ")

            if text.count("\n") == 2 and "." not in text:
                pages_type[page.page_number] = "titled_page"
            elif "*" in text and re.search(regex, text):
                pages_type[page.page.page_number] = "start_speech_page"
            elif text.find("Notes") != -1 and text.find("[1]") != -1:
                # 390
                notes_pos = text.find("Notes")
                text = text[:notes_pos]
                pages_type[page.page_number] = "start_notes_page"
            elif pages_type[page.page_number - 1] \
                    in ["start_notes_page", "next_notes_page"]:
                # 344
                pages_type[page.page_number] = "next_notes_page"
            elif "Appendix"==text.split("\n")[-1]:
                if include_appendix:
                    pages_type[page.page_number] = "appendix_page"
                else:
                    break
            else:
                pages_type[page.page_number] = "next_speech_page"
            page_tokens = cleanup_tokens(tokenizer.tokenize(text.lower()))
            all_page_tokens += page_tokens
            # print(text)
            nb_pages -= 1
    ipdb.set_trace()
    word_counts = Counter(all_page_tokens)
    lexicon = sorted(set(all_page_tokens))
    pdf.close()
    """
