from urllib import request, parse
from html.parser import HTMLParser


class RatesHTMLParser(HTMLParser):
    tags = ['div', 'table', 'tr', 'td', None]
    keys = ['class', None, None, None]
    values = ['BOC_main publish', None, None, None]
    matches = [False, False, False, False]

    def __init__(self):
        HTMLParser.__init__(self)
        self.__level = 0
        self.__item = []
        self.__items = []

    def handle_starttag(self, tag, attrs):
        if tag == self.tags[self.__level]:
            if self.keys[self.__level] == None:
                self.matches[self.__level] = True
            else:
                for key, value in attrs:
                    if key == self.keys[self.__level] and value == self.values[self.__level]:
                        self.matches[self.__level] = True
        if self.matches[0]:
            self.__level = self.__level + 1

    def handle_data(self, data):
        if all(self.matches):
            self.__item.append(data)

    def handle_endtag(self, tag):
        if self.matches[0]:
            self.__level = self.__level - 1
            if self.matches[-1] == False and len(self.__item) > 0:
                self.__items.append(self.__item)
                self.__item = []
            self.matches[self.__level] = False

    def getItems(self):
        return self.__items


def getExchangeRate():
    url = 'http://srh.bankofchina.com/search/whpj/search.jsp'

    parms = {'erectDate': '2019-03-01', 'nothing': '2019-03-10', 'pjname': '1316'}
    querystring = parse.urlencode(parms)

    req = request.urlopen(url, querystring.encode('ascii'))
    resp = req.read().decode('utf-8')

    # print(resp)
    parser = RatesHTMLParser()
    parser.feed(resp)
    parser.close()
    return parser.getItems()


if __name__ == '__main__':
    items = getExchangeRate()
    for item in items:
        print(item)

