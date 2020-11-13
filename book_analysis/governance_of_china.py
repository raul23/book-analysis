import re

from book import CACHE_PAGES, Page, PDFBook

import ipdb


class GovernancePDFBook(PDFBook):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_page_type(self, text, page_number):
        page_type = "unknown"
        if "Appendix" == text.split("\n")[-1]:
            page_type = "start_appendix_page"
        elif text.count("\n") == 2 and "." not in text:
            page_type = "titled_page"
        elif "*" in text and re.search(self._date_regex, text):
            page_type = "start_speech_page"
        elif text.find("Notes") != -1 and text.find("[1]") != -1:
            page_type = "start_notes_page"
        elif not self._explore_nb_pages:
            self._explore_nb_pages = self._default_explore_nb_pages
            page_type = "next_speech_page"
        else:
            # Infer current's page type by looking to previous page's type
            prev_page_number = page_number - 1
            # TODO: treat case when page_number = 1
            prev_page = self.pages.get(prev_page_number)
            if prev_page:
                # Page found in self.pages
                self._update_book_tokens(prev_page_number, prev_page.page_tokens)
                # TODO: add book tokens in cache? (or they are supposed to already be there)
                prev_page_type = prev_page._page_type
            else:
                # Page not found in self.pages
                # Then, check in cache
                prev_page = self.cache.get_item(prev_page_number, CACHE_PAGES)
                if prev_page:
                    # Page found in cache
                    prev_page_type = prev_page._page_type
                else:
                    # Page not found in cache (neither in self.pages)
                    prev_pdf_page = self.pdf.pages[prev_page_number - 1]
                    prev_page_text = prev_pdf_page.extract_text()
                    if not prev_page_text:
                        # TODO: catch this error (LookupError?)
                        raise LookupError("The type of the current page {} can't "
                                          "be identified because its previous page "
                                          "is empty.".format(page_number,
                                                             prev_page_number))
                    self._explore_nb_pages -= 1
                    prev_page_text = self._preprocessing(prev_page_text)
                    prev_page_type = self._get_page_type(prev_page_text, prev_page_number)
                    prev_page_tokens = self.tokenizer.tokenize(
                        text=prev_page_text, **self.tokenizer_cfg['FILTERS'])
                    prev_page = Page(prev_page_number, prev_page_type, prev_page_tokens)
                    self._update_pages_to_cache(prev_page)
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
