import sqlite3
import os

class SQLLiteTool:
    def __init__(self,dbfile):
        self.conn=sqlite3.connect(dbfile)

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
            return
        except Exception as e:
            print(e)


if __name__ == '__main__':
    tool = SQLLiteTool("data%swm.db"%os.path.sep)
    tool.updateDB('drop table netvalue')
    tool.updateDB("create table netvalue(code varchar(16), rpt_date varchar(10), value float, PRIMARY KEY(code,rpt_date))")
    tool.updateDB("insert into netvalue values('abcd1','2024-07-01', 1.01)")
    tool.updateDB("insert into netvalue values('abcd1','2024-07-02', 1.02)")
    tool.updateDB("insert into netvalue values('abcd1','2024-07-03', 1.03)")

    rows=tool.queryDB('select * from netvalue')
    for row in  rows:
        print(row[0],row[1],row[2])

    del tool
