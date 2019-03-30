from urllib import request,parse
from html.parser import HTMLParser

class RatesHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.tags=['div','table','tr','td']
        self.level=0
        self.item=[]
        self.items=[]
      
    def handle_starttag(self,tag,attrs):
        if self.level<len(self.tags) and tag==self.tags[self.level]:
            if self.level==0:
                for key,value in attrs:
                    if key=='class' and value=='BOC_main publish':
                        self.level=self.level+1
            else:
                self.level=self.level+1;
      
                
    def handle_data(self,data):
        if self.level==4:
            self.item.append(data)

    def handle_endtag(self,tag):
        if self.level>0 and tag==self.tags[self.level-1]:
            if self.level==3:
                if len(self.item)>0:
                    self.items.append(self.item)
                    self.item=[]
            self.level=self.level-1
        
    def getItems(self):
        return self.items


def getExchangeRate(): 
    url= 'http://srh.bankofchina.com/search/whpj/search.jsp'

    parms={'erectDate':'21','nothing':'2016-07-12','pjname':'1316'}
    querystring=parse.urlencode(parms)
   
    req=request.urlopen(url,querystring.encode('ascii'))
    resp=req.read().decode('utf-8')

    parser=RatesHTMLParser()
    parser.feed(resp)
    parser.close()
    return parser.getItems()

if __name__== '__main__':
    getExchangeRate()

