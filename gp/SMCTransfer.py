#!/usr/bin/python

import pymysql
import re

class GPTransfer:
    #conn=None
    #dblink=None
    def __init__(self,database,user,password,host,port):
        self.conn=pymysql.connect(database=database, user=user, password=password, host=host, port=port)
        self.dblink='hostaddr=%s port=%s dbname=%s user=%s password=%s'%(host,port,database,user,password)
      
    def __del__(self):
        self.conn.close()

    def queryDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            #result=[r for r in cur]
            result=cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            print(e)


    def get_smc_script(self):
        smc_orgs = "select orgid,orgname,ehrno,parent_name,parent_ehrno from org_smc order by innerno"
        rv_orgs=self.queryDB(smc_orgs)
        if not rv_orgs or not rv_orgs[0]:
            return "no smc record"

        issuefile = open('smc/smc_issue.txt', 'w',encoding='utf-8')
        for org in rv_orgs:
            if not self.record_match(org[2],org[4]):
                issuefile.write(str(org[0])+','+org[1]+'\n')
            else:
                print(org[1]+' 匹配\n')
        issuefile.close()



    def record_match(self,ehrno, parent_ehrno):
        query = "select * from org_executive where org_refno='%s' and parent_refno='%s' limit 5"%(ehrno,parent_ehrno)
        rv_rows=self.queryDB(query)
        if rv_rows and rv_rows[0]:
            return True
        else:
            return False



tools=GPTransfer("test", "root", "", "localhost", 3306)

tools.get_smc_script()
