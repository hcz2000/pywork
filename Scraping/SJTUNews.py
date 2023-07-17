from urllib import request,parse
from html.parser import HTMLParser
import urllib


class NewsHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.entitydefs={}
        self.items=[]
        self.row_start=False
        self.table_start=False
    def handle_starttag(self,tag,attrs):
        if tag=='table':
            for key,value in attrs:
                if key=='class' and value=='winstyle1335':
                    self.table_start=True
        if self.table_start==True and tag=='span':
            for key,value in attrs:
                if key=='class' and value=='titlestyle1335':
                    self.row_start=True
            
    def handle_data(self,data):
        if self.row_start==True:
            self.text=data
            self.items.append(data)


    def handle_endtag(self,tag):
        if self.table_start==True and tag=='table':
            self.table_start=False
        if self.row_start==True and tag=='span':
            self.row_start=False
      
    def getItems(self):
        return self.items

def getNews():
    url='http://news.sjtu.edu.cn/jdkx.htm'
    fd=request.urlopen(url)
    parser=NewsHTMLParser();
    parser.feed(fd.read().decode('utf-8'))
    items=parser.getItems()
    for text in items:
        print(text)
    parser.close()
    
