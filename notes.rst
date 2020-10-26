=====
Notes
=====

.. contents:: **Table of contents**
   :depth: 3
   :local:

pdf-to-text
===========
Method 1: ``pdfplumber``
------------------------
* `pdfplumber's GitHub`_
* `pdfplumber's PyPI`_: Released on Oct 20, 2020
* **Codes sample**:

  .. code-block:: python
   
     import pdfplumber

     pdf = pdfplumber.open("book.pdf")
     page = pdf.pages[0]
     text = page.extract_text()
     print(text)
     pdf.close()

References
----------
* `How to extract text from pdf in python 3.7.3 (stackoverflow)`_:  2019-2020

  * code sample for ``pdfplumber`` and ``tika``
* `How to read simple text from a PDF file with Python? (stackoverflow)`_: 2020

  * OP tried many solutions but ``pdfminer`` seems to work; also provides code sample for pdf-to-text conversion using ``pdfminer``

epub-to-text
============
Method 1: ``epub_conversion``
-----------------------------
* `epub_conversion's GitHub`_
* `epub_conversion's PyPI`_: Released on Mar 18, 2020
* **Codes sample**:

  .. code-block:: python

     from epub_conversion.utils import open_book, convert_epub_to_lines

     book = open_book(epub_fp)
     lines = convert_epub_to_lines(book)

Method 2: ``ebooklib``
----------------------
**NOTE:** you need to install first ``xml_cleaner`` (see https://pypi.org/project/xml-cleaner)

* `EbookLib’s GitHub`_
* `EbookLib’s PyPI`_: Released on Jan 3, 2019
* `EbookLib’s documentation`_
* **Codes sample**:

  .. code-block:: python

     import ebooklib
     from ebooklib import epub

     book = epub.read_epub(epub_fp)
     for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
         pass

References
----------
* `Ebooklib's sample code (stackoverflow)`_: 2019
* `How to parse text from each chapter in epub? (stackoverflow)`_: 2019
* `Calibre's ebook-convert (askubuntu)`_: 2012


.. URLs
.. _Calibre's ebook-convert (askubuntu): https://askubuntu.com/a/102475
.. _EbookLib’s documentation: http://docs.sourcefabric.org/projects/ebooklib/en/latest
.. _EbookLib’s GitHub: https://github.com/aerkalov/ebooklib
.. _EbookLib’s PyPI: https://pypi.org/project/EbookLib
.. _Ebooklib's sample code (stackoverflow): https://stackoverflow.com/a/55180536
.. _epub_conversion's GitHub: https://github.com/JonathanRaiman/epub_conversion
.. _epub_conversion's PyPI: https://pypi.org/project/epub-conversion
.. _How to extract text from pdf in python 3.7.3 (stackoverflow): https://stackoverflow.com/q/55767511
.. _How to parse text from each chapter in epub? (stackoverflow): https://stackoverflow.com/q/56410564
.. _How to read simple text from a PDF file with Python? (stackoverflow): https://stackoverflow.com/q/59894592
.. _pdfplumber's GitHub: https://github.com/jsvine/pdfplumber
.. _pdfplumber's PyPI: https://pypi.org/project/pdfplumber

