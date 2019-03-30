from urllib import request,parse
from html.parser import HTMLParser
import urllib


class NewsHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.entitydefs={}
        self.link=""
        self.text=""
        self.items=[]
        self.flag=False
        self.article_start=False
        self.notice_start=False
    def handle_starttag(self,tag,attrs):
        if tag=='ul' and attrs:
            for key,value in attrs:
                if key=='class' and value=='article-list with-tag':
                    self.notice_start=True
        if self.notice_start==True and tag=='span':
            for key,value in attrs:
                if key=='class' and value=='post':
                    self.article_start=True
        if  self.article_start==True and  tag=='a':
            self.flag=True
            
    def handle_data(self,data):
        if self.flag==True:
            self.text=data
            self.items.append(data)


    def handle_endtag(self,tag):
        if self.notice_start==True and tag=='ul':
            self.notice_start=False
        if self.article_start==True and tag=='span':
            self.article_start=False
        if self.flag==True and tag=='a':
            self.flag=False
 
    def getItems(self):
        return self.items

def getNews():
    url='http://www.teach.ustc.edu.cn/category/notice'
    fd=request.urlopen(url)
    parser=NewsHTMLParser();
    parser.feed(fd.read().decode('utf-8'))
    items=parser.getItems()
    for text in items:
        print(text)
    parser.close()

if __name__== '__main__':
    getNews()


    
