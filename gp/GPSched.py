#!/usr/bin/python

import psycopg2
from datetime import datetime,timedelta
import re
import getopt
import sys

class Sched:
    def __init__(self,database,user,password,host,port):
        self.conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)

    def __del__(self):
        self.conn.close()

    def queryDB(self,sql):
        try:
            cur=self.conn.cursor()
            cur.execute(sql)
            result=cur.fetchall()
            cur.close()
            self.conn.commit();
            return result
        except Exception as e:
            self.conn.rollback()
            print(e)

    def initJobStatus(self,dt):
        run_sql = "insert into etl.job_status select '%s' dt,job_id,type,cmd,parameter_str,0 status from etl.job_inf"%dt
        print(run_sql)
        try:
            cur=self.conn.cursor()
            cur.execute(run_sql)
            result=cur.rowcount
            cur.close()
            self.conn.commit();
            return result
        except Exception as e:
            self.conn.rollback()
            print(e)
            return -1

    def runFunc(self,funcName,dt,jobId):
        run_sql = "select %s('%s','%s')"%(funcName,dt,jobId)
        try:
            cur=self.conn.cursor()
            cur.execute(run_sql)
            result=cur.fetchall()
            cur.close()
            self.conn.commit();
            return result[0][0]
        except Exception as e:
            self.conn.rollback()
            print(e)
            return -1

    def checkReady(self,dataSetId,dt):
        dep_tables_sql = "select table_name,field_name from etl.data_set where set_id='%s'"%(dataSetId)
        rv_tables = self.queryDB(dep_tables_sql)
        if rv_tables :
            ready_cnt=0
            for  (table_name,field_name) in rv_tables:
                check_sql="select *  from ODS.%s where %s='%s' limit 5"%(table_name,field_name,dt)
                rv_record=self.queryDB(check_sql)
                if rv_record and rv_record[0]:
                    ready_cnt =ready_cnt+1
            if ready_cnt==len(rv_tables):
                return 0
            else:
                return -1
        else:
            return -1;

    def updateJobStatus(self,jobId,dt,status):
        run_sql = "update etl.job_status set  status=%s  where job_id='%s' and dt='%s'"%(status,jobId,dt)
        print(run_sql)
        try:
            cur=self.conn.cursor()
            cur.execute(run_sql)
            result=cur.rowcount
            cur.close()
            self.conn.commit();
            return result-1
        except Exception as e:
            self.conn.rollback()
            print(e)
            return -1

    def load_jobs(self,dt):
        get_jobs = "select job_id,type,parameter_str from etl.job_status where dt='%s' and status=0 "%dt
        rv_jobs=self.queryDB(get_jobs)
        if not rv_jobs or not rv_jobs[0]:
            print('No job to do')
            return
        for i in range(0,len(rv_jobs)):
            job_id=rv_jobs[i][0]
            job_type=rv_jobs[i][1]
            job_parameter=rv_jobs[i][2]
            dep_jobs="select  t1.job_id from etl.job_status t1,etl.job_rln t2 where t1.job_id = t2.p_job_id and t1.status <> 1 and t2.job_id='%s'"%job_id
            rv_dep_jobs = self.queryDB(dep_jobs)
            if rv_dep_jobs and rv_dep_jobs[0]:
                print(rv_dep_jobs[0])
                continue
            if job_type==1:
                procname = job_parameter.lstrip( '<AC_DATE> ')
                print(procname)
                result=self.runFunc(procname,dt,job_id)
                if result==0:
                    self.updateJobStatus(job_id,dt,1)
                else:
                    self.updateJobStatus(job_id, dt,-1)
                    print('Run %s Result: %s'%(procname,result))
            if job_type==0:
                dataSetId = job_parameter.lstrip('<AC_DATE> ')
                print(dataSetId)
                if 0 == self.checkReady(dataSetId,dt):
                    self.updateJobStatus(job_id, dt, 1)

        return

def main():
    if len(sys.argv)>1:
        dt=sys.argv[1]
    else:
        dt=(datetime.now()+timedelta(days=-1)).strftime("%Y%m%d")
    #tools=Sched("cogp", "gpadmin", "gpPass@123", "21.136.64.238", "5432")
    tools = Sched("gpDB", "gpmon", "gpmon", "192.168.3.5", "5432")
    #tools.initJobStatus(dt)
    tools.load_jobs(dt)

if __name__=='__main__':
    main()