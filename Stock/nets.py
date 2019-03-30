from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup

def getTitle(url):
    try:
        html=urlopen(url)
    except HTTPError as e:
        print(e)
        return None

    try:
        bsObj=BeautifulSoup(html.read())
        title=bsObj.head.title
    except AttributeError as e:
        return None
    return title

def main():
    title=getTitle("http://finance.sina.com.cn/roll/2016-11-19/doc-ifxxwsix4111905.shtml")
    if title==None:
        print("Title could not be found")
    else:
        print(title)

if __name__=="__main__":
    main()