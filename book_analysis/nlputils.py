import string
# Third-party
import nltk


def cleanup_tokens(tokens, remove_punctuations=True, remove_stopwords=True):
    tokens_to_remove = set()
    puncs1 = ['``', '--', "''"]
    puncs2 = [p for p in string.punctuation]
    # diff_puncs1_puncs2 = set(puncs1).difference(puncs2)
    # diff_puncs2_puncs1 = set(puncs2).difference(puncs1)
    nltk.download('stopwords', quiet=True)
    stopwords = nltk.corpus.stopwords.words('english')
    if remove_punctuations:
        tokens_to_remove.update(set(puncs1))
        tokens_to_remove.update(set(puncs2))
    if remove_stopwords:
        tokens_to_remove.update(set(stopwords))
    cleaned_tokens = [token for token in tokens if token not in tokens_to_remove]
    # diff = set(tokens).difference(cleaned_tokens)
    return cleaned_tokens
