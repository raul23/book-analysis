import os

import conf
import ipdb


class Config:
    def __init__(self):
        self._set_attributes()

    def _set_attributes(self):
        for opt_name, opt_value in conf.__dict__.items():
            if opt_name.endswith('filepath'):
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
            self.__setattr__(opt_name, opt_value)

    @staticmethod
    def check_path(path, isdir):
        if not os.path.exists(path):
            if isdir:
                raise FileNotFoundError("Directory not found: {}".format(path))
            else:
                raise FileNotFoundError("File not found: {}".format(path))


config = Config()
