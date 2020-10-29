import os
# Third-party
import dill
# Own
import conf


def load_pickle(filepath):
    # TODO: raise IOError
    with open(filepath, 'rb') as f:
        return dill.load(f)


def save_pickle(obj, filepath, protocal=dill.HIGHEST_PROTOCOL):
    # TODO: raise IOError
    with open(filepath, 'wb') as f:
        dill.dump(obj, f, protocol=protocal)


class Config:
    def __init__(self):
        self.settings = self._get_settings()

    def _get_settings(self):
        settings = {}
        for opt_name, opt_value in conf.__dict__.items():
            if not opt_name.startswith('__') and not opt_name.endswith('__'):
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
