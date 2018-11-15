#!/usr/bin/python

import psycopg2

class SQLFetcher:
    conn=None
    frame=None
    def __init__(self,database,user,password,host,port):
        self.conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
      
    def __del__(self):
        self.conn.close()

    def get_create_sql(self,tablename):
        cur=self.conn.cursor()

        try:
	        table_name = tablename.lower().split('.')[1]
	        table_schema = tablename.lower().split('.')[0]
        except (IndexError):
	        return 'Please input "tableschema.table_name" '

        get_table_oid = "select oid, reloptions, relkind from pg_class where oid='%s':: regclass"%(tablename)

        try:
            cur.execute( get_table_oid)
            rv_oid=[r for r in cur]
            cur.close()
            if not rv_oid:
		        return 'Did not find any relation named "'+ tablename +'".'
        except(Error):
            return 'Did not find any relation named "'+ tablename +'".'

        table_oid = rv_oid[0]['oid']
        rv_reloptions = rv_oid[ 0]['reloptions']
        rv_relkind= rv_oid[0]['relkind']
        
        return table_oid

fetcher=SQLFetcher("gpDB","gpadmin","gppass","192.168.3.5","5432")
table=fetcher.get_create_sql('public.test')

