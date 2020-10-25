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
* Codes sample:

  .. code-block:: python
   
     pdf = pdfplumber.open(pdf_fp)
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

References
----------

.. URLs
.. _How to extract text from pdf in python 3.7.3 (stackoverflow): https://stackoverflow.com/q/55767511
.. _How to read simple text from a PDF file with Python? (stackoverflow): https://stackoverflow.com/q/59894592
.. _pdfplumber's GitHub: https://github.com/jsvine/pdfplumber
.. _pdfplumber's PyPI: https://pypi.org/project/pdfplumber/

