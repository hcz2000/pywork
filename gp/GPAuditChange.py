#!/usr/bin/python

import time
import re
import os
from GPUtil import GPTools

def get_change_tables(gptools, schemas, start_time):
    table_operations = "select statime,schemaname,objname,usename,actionname from pg_catalog.pg_stat_operations " \
                  "where statime>'%s' and classname='pg_class' and subtype='TABLE'  order by statime desc "%(start_time)
    rv_oprs=gptools.queryDB(table_operations)
    if not rv_oprs:
        return
    for opr in rv_oprs:
        stat_time=opr[0]
        schema=opr[1]
        table=opr[2]
        user=opr[3]
        operation=opr[4]
        if schema not in schemas or operation not in['CREATE','ALTER']:
            continue
        if gptools.is_partition_child(table):
            continue

        schema_dir='change/'+schema;
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir)
            os.makedirs(schema_dir + '/table')
            os.makedirs(schema_dir + '/function')

        opr_date='%d-%02d-%02d'%(stat_time.year,stat_time.month,stat_time.day)
        print('--'+schema+'.'+table+': '+operation+' by '+user+'-'+opr_date )
        tabledef=gptools.get_table_ddl(schema, table)
        if tabledef:
            with open(schema_dir + '/table/' + table + '.' + opr_date + '.sql','w', encoding='utf-8') as f:
                f.write(tabledef)

def get_change_functions(gptools, schemas, start_time):
    #func_operations = "select logtime,loguser,logdebug from gp_toolkit.__gp_log_master_ext where logtime>='%s' and logmessage like 'execute: %%'" % (start_time)
    func_operations = "select logtime,loguser,logdebug from gp_toolkit.__gp_log_master_ext where logtime>='%s'" % (
        start_time)
    rv_funcs = gptools.queryDB(func_operations)
    if not rv_funcs:
        return
    for opr in rv_funcs:
        logtime = opr[0]
        user = opr[1]
        sql = opr[2]
        if not sql:
            continue
        match=re.match(r'^\s*(\/\*\*[\s\S]*\*\*\/)?\s*CREATE\s+(?:OR\s+REPLACE)?\s+FUNCTION\s+[\w\.]+\s*\(',sql,re.IGNORECASE)
        if match:
            funcs=match.group(0).split(r'FUNCTION',re.IGNORECASE)[1].lstrip()[:-1].split('.')
            if len(funcs)==2:
                schema=funcs[0]
                funcname=funcs[1]
            else:
                schema='public'
                funcname=funcs[0]
            if schema not in schemas :
                continue

            schema_dir='change/'+schema;
            if not os.path.exists(schema_dir):
                os.makedirs(schema_dir)
                os.makedirs(schema_dir + '/table')
                os.makedirs(schema_dir + '/function')

            opr_date = '%d-%02d-%02d' % (logtime.year, logtime.month, logtime.day)
            print('--' + schema+'.'+funcname+'create/update by '+user)
            funcdef = gptools.get_function_ddl(schema, funcname)
            if funcdef:
                with open(schema_dir + '/function/' +  funcname +'.'+ opr_date + '.sql', 'w', encoding='utf-8') as f:
                    f.write(funcdef)

#gptools=GPTools("gp","da_huangchangzhan","hczpass","21.136.30.147","5432")
gptools=GPTools("gp","gpadmin","gpadmin","192.168.3.6","5432")
schemas=['public','art','bmas','bmms','cid','cid','cidsqry','dep','east','grzl','gzfh','hdis','itsp','ivbk','maas','mpc','nccdw','ods','odsh','rid','ridh','ridsadm','ridsqry','rp','rscr','wdyj']
gptools.get_table_ddl('gp_toolkit','__gp_log_master_ext')
now=time.localtime()
start_time='%d-%02d-01'%(now.tm_year,now.tm_mon)
get_change_tables(gptools, schemas, start_time)
get_change_functions(gptools, schemas, start_time)
