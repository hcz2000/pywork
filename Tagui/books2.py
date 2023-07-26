from lxml import etree
import urllib.request
import time
import pymysql

class BookInfo():

    def __init__(self,database,user,password,host,port):
        self.conn=pymysql.connect(database=database, user=user, password=password, host=host, port=port)

    def __del__(self):
        self.conn.close()

    def queryDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            result=cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            print(e)

    def updateDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
            cur.close()
            return
        except Exception as e:
            print(e)

    def getInfo(self,bookno):
        url="https://m.23sk.net/files/article/html/"+bookno[:len(bookno)-3]+"/"+bookno+"/"
        #print(url)
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            response = urllib.request.urlopen(request,timeout=30)
            content=response.read().decode('utf-8')
        except Exception as e:
            print(e)
            return

        html=etree.HTML(content)

        elements = html.xpath("//div[@class='block_txt2']/p")
        name = elements[0].findtext("a/h2")

        author = elements[1].text[3:]
        type = elements[2].findtext("a")
        update = elements[4].text[3:]
        info = html.xpath("//div[@class='intro_info']/text()")[0]
        #print(info)
        print(bookno+','+name+','+author+','+type+','+update)
        if len(info)>256:
            info=info[:255]
        sql="insert into book values('"+bookno+"','"+name+"','"+author+"','"+type+"','"+info+"')"
        #print(sql)
        self.updateDB(sql)


if __name__ == '__main__':
    store = BookInfo("book", "root", "root", "localhost", 3306)
    for no in range(13273,999999):
        store.getInfo(str(no))
        time.sleep(1)