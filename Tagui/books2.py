from lxml import etree
import urllib.request
import os

class BookInfo():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)

    def getInfo(self,bookno):
        url="https://m.23sk.net/files/article/html/"+bookno[:-len(bookno)+3]+"/"+bookno+"/"
        print(url)

        response = urllib.request.urlopen(url)
        content=response.read().decode('utf-8')
        #print(content)

        html=etree.HTML(content)

        names = html.xpath("//div[@class='block_txt2']/p")
        print(names)
        #elements= tree.xpath("//div[@class='block_txt2']/p")
        #author = elements[2]
        #print(author.text)
        #type = elements[3]
        #print(type.text)
        #update = elements[5]
        #print(update.text)
        info = html.xpath("//div[@class='intro_info']/text()")[0]
        #print(info)

if __name__ == '__main__':
    obj = BookInfo()
    obj.getInfo('127418')