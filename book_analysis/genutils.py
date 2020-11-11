import os
# Third-party
import dill
# Custom
import conf


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
    def __init__(self):
        self.cache = {}

    def reset_cache(self):
        self.cache = {}

    # TODO: specify that data should be a dict or set (with update function)
    def update_cache(self, data, data_type):
        if self.cache.get(data_type):
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
                # TODO: add epub_filepath in list
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
