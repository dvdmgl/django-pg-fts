
class TranslationDictionary(object):
    """
    TranslationDictionary

    """
    def __init__(self, dictionaries=None, default=None):
        self.dictionaries = dictionaries or {
            'pt': ('portuguese', _('Portuguese')),
            'en': ('english', _('English')),
            'es': ('spanish', _('Spanish')),
            'de': ('german', _('German')),
            'da': ('danish', _('Danish')),
            'nl': ('dutch', _('Dutch')),
            'fi': ('finnish', _('Finnish')),
            'fr': ('french', _('French')),
            'hu': ('hungarian', _('Hungarian')),
            'it': ('italian', _('Italian')),
            'nn': ('norwegian', _('Norwegian')),
            'ro': ('romanian', _('Romanian')),
            'ru': ('russian', _('Russian')),
            'sv': ('swedish', _('Swedish')),
            'tr': ('turkish', _('Turkish')),
        }

        self.default = default or ('simple', _('Simple'))

    def get_dictionary_tuple(self, language):
        return self.dictionaries.get(language.split('-')[0], self.default)

    def get_dictionary_pg(self, language):
        return self.get_dictionary_tuple(language)[0]

    def get_dictionaries(self, languages=None):
        if languages:
            return tuple(self.get_dictionary(l) for l in self.dictionaries)
        return self.dictionaries.values()
