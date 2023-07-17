#!/usr/bin/python

import psycopg2
import re
import os
from GPUtil import GPTools

def get_baseline(gptools, schema):
     #get_tables = "select a.relname from pg_class a,pg_namespace b where a.relnamespace=b.oid and a.relkind='r' and b.nspname='%s'"%(schema)
    get_tables = "select tablename from pg_tables where schemaname='%s' order by tablename"%(schema)
    rv_tables=gptools.queryDB(get_tables)
    if not rv_tables or not rv_tables[0]:
            return "Schema "+schema+" not exist or does not contain tables"

    schema_dir='baseline/'+schema;
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir)
        os.makedirs(schema_dir + '/table')
        os.makedirs(schema_dir + '/function')


    for table in rv_tables:
        print('--'+table[0])
        tabledef=gptools.get_table_ddl(schema, table[0])
        if tabledef:
            with open(schema_dir+'/table/'+table[0]+'.sql','w', encoding='utf-8') as f:
                f.write(tabledef)

    get_functions = "select proname from pg_proc t1,pg_namespace t2 where t1.pronamespace = t2.oid and t2.nspname='%s' order by proname" % (schema)
    rv_funcs=gptools.queryDB(get_functions)
    if not rv_funcs or not rv_funcs[0]:
        return "no function exist"

    for func in rv_funcs:
        print('--' + func[0])
        funcName=func[0]
        funcdef = gptools.get_function_ddl(schema, funcName)
        if funcdef:
            with open(schema_dir + '/function/' + funcName + '.sql', 'w', encoding='utf-8') as f:
                f.write(funcdef)

gptools=GPTools("gp","da_huangchangzhan","hczpass","21.136.30.147","5432")
schemas=['art','bmas','bmms','cid','cid','cidsqry','dep','east','grzl','gzfh','hdis','itsp','ivbk','maas','mpc','nccdw','ods','odsh','rid','ridh','ridsadm','ridsqry','rp','rscr','wdyj']
for schema in schemas:
    get_baseline(gptools, schema)
#gptools.get_table_ddl('ods','aas_astbgl_f')
#gptools.get_function_ddl('ods','fn_bancs_invm_f')
#gptools.get_view_ddl('pg_catalog','pg_stats')
