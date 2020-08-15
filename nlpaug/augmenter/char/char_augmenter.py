import string
import re

from nlpaug.util import Method
from nlpaug import Augmenter
from nlpaug.util import WarningException, WarningName, WarningCode, WarningMessage


class CharAugmenter(Augmenter):
    TOKENIZER_REGEX = re.compile(r'(\W)')
    DETOKENIZER_REGEXS = [
        (re.compile(r'\s([.,:;?!%]+)([ \'"`])'), r'\1\2'), # End of sentence
        (re.compile(r'\s([.,:;?!%]+)$'), r'\1'), # End of sentence
        (re.compile(r'\s([\[\(\{\<])\s'), r' \g<1>'), # Left bracket
        (re.compile(r'\s([\]\)\}\>])\s'), r'\g<1> '), # right bracket
    ]

    def __init__(self, action, name='Char_Aug', min_char=2, aug_char_min=1, aug_char_max=10, aug_char_p=0.3,
                 aug_word_min=1, aug_word_max=10, aug_word_p=0.3, tokenizer=None, reverse_tokenizer=None,
                 stopwords=None, device='cpu', verbose=0, stopwords_regex=None, include_special_char=True,
                 include_detail=False):
        super().__init__(
            name=name, method=Method.CHAR, action=action, aug_min=None, aug_max=None, device=device, verbose=verbose,
            include_detail=include_detail)
        self.aug_p = None
        self.aug_char_min = aug_char_min
        self.aug_char_max = aug_char_max
        self.aug_char_p = aug_char_p
        self.aug_word_min = aug_word_min
        self.aug_word_max = aug_word_max
        self.aug_word_p = aug_word_p
        self.min_char = min_char

        self.tokenizer = tokenizer or self._tokenizer
        self.reverse_tokenizer = reverse_tokenizer or self._reverse_tokenizer
        self.stopwords = stopwords
        self.stopwords_regex = re.compile(stopwords_regex) if stopwords_regex is not None else stopwords_regex
        self.include_special_char = include_special_char

    @classmethod
    def _tokenizer(cls, text):
        tokens = cls.TOKENIZER_REGEX.split(text)
        return [t for t in tokens if len(t.strip()) > 0]

    @classmethod
    def token2char(cls, word):
        return list(word)

    @classmethod
    def _reverse_tokenizer(cls, tokens):
        text = ' '.join(tokens)
        for regex, sub in cls.DETOKENIZER_REGEXS:
            text = regex.sub(sub, text)
        return text.strip()

    @classmethod
    def clean(cls, data):
        return data.strip()

    @classmethod
    def is_duplicate(cls, dataset, data):
        for d in dataset:
            if d == data:
                return True
        return False

    def skip_aug(self, token_idxes, tokens):
        return token_idxes

    def pre_skip_aug(self, tokens, tuple_idx=None):
        results = []
        for token_idx, token in enumerate(tokens):
            if tuple_idx is not None:
                _token = token[tuple_idx]
            else:
                _token = token
            # skip punctuation
            if _token in string.punctuation and not self.include_special_char:
                continue
            """
                TODO: cannot skip word that were split by tokenizer
            """
            # skip stopwords by list
            if self.stopwords is not None and _token in self.stopwords:
                continue

            # skip stopwords by regex
            if self.stopwords_regex is not None and (
                    self.stopwords_regex.match(_token) or self.stopwords_regex.match(' '+_token+' ') or
                    self.stopwords_regex.match(' '+_token) or self.stopwords_regex.match(_token+' ')):
                continue

            results.append(token_idx)

        return results

    def _get_aug_idxes(self, tokens, aug_min, aug_max, aug_p, mode):
        if mode == Method.CHAR:
            # If word is too short, do not augment it.
            if len(tokens) < self.min_char:
                return None

        aug_cnt = self._generate_aug_cnt(len(tokens), aug_min, aug_max, aug_p)

        if mode == Method.WORD:
            idxes = self.pre_skip_aug(tokens)
        elif mode == Method.CHAR:
            idxes = [i for i, t in enumerate(tokens)]
            idxes = self.skip_aug(idxes, tokens)

        if len(idxes) == 0:
            if self.verbose > 0:
                exception = WarningException(name=WarningName.OUT_OF_VOCABULARY,
                                             code=WarningCode.WARNING_CODE_002, msg=WarningMessage.NO_WORD)
                exception.output()
            return None
        if len(idxes) < aug_cnt:
            aug_cnt = len(idxes)
        aug_idxes = self.sample(idxes, aug_cnt)
        return aug_idxes
