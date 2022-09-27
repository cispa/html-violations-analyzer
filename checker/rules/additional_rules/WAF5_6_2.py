from html.parser import HTMLParser

name_informal = """ Unclosed Tag """
description = """ Checks whether an element contains an attribute with < in the name. This would indicate an unclosed tag """

class WAF4_5(HTMLParser):
    
    def __init__(self, *, convert_charrefs=True, debug=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self._valid = True
        self._debug = debug

    def handle_starttag(self, tag, attrs):
        for attr_name, _ in attrs:
            if "<" in attr_name:
                if self._debug:
                    print(f"{tag} -> {attrs}")
                self._valid = False

    def is_valid(self):
        return self._valid


def run_rule(html, debug=True):
    waf4_5_2 = WAF4_5(debug=debug)
    waf4_5_2.feed(html)
    res = waf4_5_2.is_valid()
    del waf4_5_2
    return res
