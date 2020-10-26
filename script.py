import os

import pdfplumber
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
