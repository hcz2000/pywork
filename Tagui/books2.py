from lxml import etree
import urllib.request
import os
import time

class BookInfo():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)

    def getInfo(self,bookno):
        url="https://m.23sk.net/files/article/html/"+bookno[:len(bookno)-3]+"/"+bookno+"/"
        #print(url)
        response = urllib.request.urlopen(url)
        content=response.read().decode('utf-8')

        html=etree.HTML(content)

        elements = html.xpath("//div[@class='block_txt2']/p")
        name = elements[0].findtext("a/h2")

        author = elements[1].text[3:]
        type = elements[2].findtext("a")
        update = elements[4].text[3:]
        info = html.xpath("//div[@class='intro_info']/text()")[0]
        #print(info)
        print(bookno+','+name+','+author+','+type+','+update)


if __name__ == '__main__':
    store = BookInfo()
    #store.getInfo('127418')
    for no in range(10000,999999):
        store.getInfo(str(no))
        time.sleep(1)