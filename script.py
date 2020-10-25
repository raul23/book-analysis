import os

import ebooklib
import pdfplumber
from ebooklib import epub
from epub_conversion.utils import open_book, convert_epub_to_lines

import ipdb

data_dp = os.path.expanduser("~/Data/book-analysis")
epub_fp = os.path.join(data_dp, "The Governance of China by Xi Jinping - First Edition (2014).epub")
# epub_fp = os.path.join(data_dp, "The Governance of China by Xi Jinping - Second Edition (2018).epub")
pdf_fp = os.path.join(data_dp, "The Governance of China by Xi Jinping - First Edition (2014).pdf")


if __name__ == '__main__':
    ipdb.set_trace()

    # pdf-to-text
    pdf = pdfplumber.open(pdf_fp)
    page = pdf.pages[0]
    text = page.extract_text()
    print(text)
    pdf.close()

    # ------------
    # epub to text
    # ------------
    # References:
    # - https://stackoverflow.com/a/55180536 : ebooklib's sample code (2019)
    # - https://stackoverflow.com/q/56410564 : how to parse text from each chapter in epub? (2019)
    # - https://askubuntu.com/a/102475 : Calibre's ebook-convert (2012)

    # Method 1: epub_conversion
    # References:
    # - https://github.com/JonathanRaiman/epub_conversion : epub_conversion's GitHub
    # - https://pypi.org/project/epub-conversion/ : epub_conversion's PyPI (Released: Mar 18, 2020)
    book = open_book(epub_fp)
    lines = convert_epub_to_lines(book)
    for line in lines:
        pass

    # Method 2: ebooklib
    # NOTE: need to install xml_cleaner (see https://pypi.org/project/xml-cleaner/)
    # References:
    # - https://github.com/aerkalov/ebooklib : EbookLib’s GitHub
    # - https://pypi.org/project/EbookLib/ : EbookLib’s PyPI (Released: Jan 3, 2019)
    # - http://docs.sourcefabric.org/projects/ebooklib/en/latest/ : EbookLib’s documentation
    book = epub.read_epub(epub_fp)
    for doc in book.get_items():
        pass
    for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        pass
