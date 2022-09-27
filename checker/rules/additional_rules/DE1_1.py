from html.parser import HTMLParser

name_informal = """ No \\n in URL """
description = """ Checks whether an http, https, or ftp url contains a newline. """

class DE1(HTMLParser):

    def __init__(self, *, convert_charrefs=True, debug=False):
        super().__init__(convert_charrefs=convert_charrefs)
        self._debug = debug
        self._valid = True

    def handle_starttag(self, tag, attrs):
        if tag == "srcset":
            return
            
        for key, value in attrs:
            if not value: continue
            if ((value.startswith("https://") or
                    value.startswith("http://") or
                    value.startswith("ftp://") or
                    value.startswith("//"))
                    and "\n" in value):
                if self._debug:
                    print(f"Leak: {tag} {key}={value}")
                self._valid = False

    def is_valid(self):
        return self._valid


def run_rule(html, debug=False):
    de1_1 = DE1(debug=debug)
    de1_1.feed(html)
    res = de1_1.is_valid()
    del de1_1
    return res
