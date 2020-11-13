import os

import dill
import pdfplumber

import conf

import ipdb


def load_pdf_book(filepath):
    book = load_pickle(filepath)
    # TODO: add logging for loading
    print('Loading "{}" ...'.format(book.book_title))
    # Reload the PDF book again
    # If not, I get pdfminer.pdftypes.PDFNotImplementedError: Unsupported filter: /'FlateDecode'
    book.pdf = pdfplumber.open(book.pdf_filepath)
    return book


def load_pickle(filepath):
    # TODO: raise IOError
    with open(filepath, 'rb') as f:
        # TODO: log waiting msg for loading
        print("\nLoading pickle file ...")
        return dill.load(f)


# TODO: add overwrite parameter and check if file already exists
def save_pickle(obj, filepath, protocal=dill.HIGHEST_PROTOCOL):
    # TODO: raise IOError
    with open(filepath, 'wb') as f:
        # TODO: log waiting msg for dumping
        print("\nSaving pickle file ...")
        dill.dump(obj, f, protocol=protocal)


class Cache:
    def __init__(self, cache=None):
        if cache:
            self.cache = cache
        else:
            self.cache = {}

    def get_item(self, item_key, data_type):
        if isinstance(self.cache[data_type], dict):
            return self.cache[data_type].get(item_key)
        elif isinstance(self.cache[data_type], set):
            pass
        else:
            # TODO: raise Error (unsupported data type)
            return None

    def find_item(self, item_key, data_type):
        return item_key in self.cache[data_type]

    def reset_cache(self, cache=None):
        if cache:
            self.cache = cache
        else:
            self.cache = {}

    # TODO: specify that data should be a dict or set (with update function)
    def update_cache(self, data, data_type):
        if data_type in self.cache:
            self.cache[data_type].update(data)
        else:
            self.cache[data_type] = data


class Config:
    def __init__(self):
        self.settings = self._get_settings()

    def _get_settings(self):
        settings = {}
        for opt_name, opt_value in conf.__dict__.items():
            if not opt_name.startswith('__') and not opt_name.endswith('__'):
                # TODO: eventually add epub_filepath in list
                if opt_name in ['pdf_filepath']:
                    data_dirpath = os.path.expanduser(conf.data_dirpath)
                    ebook_filepath = os.path.expanduser(opt_value)
                    if os.path.exists(ebook_filepath):
                        # Absolute file path
                        opt_value = ebook_filepath
                    else:
                        # File path relative to the data directory path
                        opt_value = os.path.join(data_dirpath, ebook_filepath)
                    self.check_path(opt_value, False)
                elif opt_name == 'data_dirpath':
                    opt_value = os.path.expanduser(opt_value)
                settings.setdefault(opt_name, opt_value)
        return settings

    @staticmethod
    def check_path(path, isdir):
        if not os.path.exists(path):
            if isdir:
                raise FileNotFoundError("Directory not found: {}".format(path))
            else:
                raise FileNotFoundError("File not found: {}".format(path))


config = Config()
