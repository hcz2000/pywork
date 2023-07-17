#!/usr/bin/python

import psycopg2
import re

class GPTransfer:
    #conn=None
    #dblink=None
    def __init__(self,database,user,password,host,port):
        self.conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
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

    def get_table_ddl(self,tablename):
        
        get_table_status = "select oid, reloptions,relhasoids,relstorage from pg_class where relkind='r' and oid='%s'::regclass"%(tablename)
        rv_table=self.queryDB(get_table_status)
        if not rv_table or not rv_table[0]:
            return None
        table_oid = rv_table[0][0]
        reloptions = rv_table[0][1]
        relhasoids = rv_table[0][2]
        relstorage = rv_table[0][3]
        if relstorage == 'x':
            get_extinfo = "select location,fmttype,fmtopts,encoding,writable from pg_exttable where reloid=%s" % (
                table_oid)
            rv_extinfo = self.queryDB(get_extinfo)
            if rv_extinfo:
                is_writable=rv_extinfo[0][4]
      
        get_columns ='''SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod),a.attnotnull as isnull,
                (SELECT substring(pg_catalog.pg_get_expr(d.adbin,d.adrelid) for 128) 
                    FROM pg_catalog.pg_attrdef d 
                    WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) as default 
                FROM pg_catalog.pg_attribute a 
                WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum;''' %(table_oid); 
        rv_columns = self.queryDB(get_columns)
        get_table_distribution1 = "SELECT attrnums FROM pg_catalog.gp_distribution_policy t WHERE localoid = %s" % table_oid 
        rv_distribution1 = self.queryDB(get_table_distribution1)
        rv_distribution2 = None
        if rv_distribution1 and rv_distribution1[0][0]:
            get_table_distribution2 = "SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum in ("%table_oid + str(rv_distribution1[0][0]).lstrip('{').rstrip('}').lstrip('[').rstrip(']') + ")"
            rv_distribution2 = self.queryDB(get_table_distribution2)

        if  relstorage == 'x':
            if is_writable:
                create_sql = 'create writable external table %s(\n' % (tablename)
            else:
                create_sql = 'create external table %s(\n' % (tablename)
        else:
            create_sql = 'create table %s(\n'%(tablename)
        get_index = "select pg_get_indexdef(indexrelid) AS indexdef from pg_index where indrelid=%s"%(table_oid)
        rv_index =self.queryDB(get_index)
        get_parinfo1 = "select attname as columnname from pg_attribute where attnum = (select paratts[0] from pg_partition where parrelid=%s) and attrelid=%s;"%( table_oid, table_oid)
        get_parinfo2 ='''SELECT pp.parrelid, pr1.parchildrelid, 
                    CASE    WHEN pp.parkind = 'h'::"char" THEN 'hash'::text 
				            WHEN pp.parkind = 'r'::"char" THEN 'range'::text 
				            WHEN pp.parkind = 'l'::"char" THEN 'list'::text 
				        ELSE NULL::text 
			        END AS partitiontype, 
			        pg_get_partition_rule_def(pr1.oid, true) AS partitionboundary 
			        FROM pg_partition pp, pg_partition_rule pr1 
			        WHERE pp.paristemplate = false AND pp.parrelid = %s AND pr1.paroid = pp.oid order by pr1.parname; '''%(table_oid);
        v_par_parent = self.queryDB(get_parinfo1)
        v_par_info = self.queryDB(get_parinfo2)
        for i in rv_columns:
            #att_name
            if i[0]:
                max_column_len = 10
                if max_column_len < i[0].__len__():
                    max_column_len = i[0].__len__()
                create_sql += ' ' + i[0].ljust( max_column_len + 6)
            #format_type
            if i[1]:
                max_type_len = 4
                if max_type_len < i[1].__len__():
                    max_type_len = i[1].__len__()
                create_sql += ' ' + i[1].ljust( max_type_len + 2) 
		    #isnull
            if i[2]:
                create_sql += ' ' + ' not null '.ljust(8)
            #default
            if i[3]:
                max_default_len= 4
                if max_default_len < i[3].__len__():
                    max_default_len = i[3].__len__()
                create_sql += ' default ' + i[3].ljust( max_default_len + 6)
            create_sql += ",\n"
        create_sql=create_sql.rstrip(',\n')+'\n)\n'

        if relstorage == 'x':
            #get_extinfo = "select location,fmttype,fmtopts,encoding,writable from pg_exttable where reloid=%s" % (table_oid)
            #rv_extinfo = self.queryDB(get_extinfo)
            if rv_extinfo:
                loc_list=rv_extinfo[0][0]
                create_sql += 'location ('
                loc_str=''
                for loc in loc_list:
                    loc_str +="'"+loc+"',"
                create_sql +=loc_str.rstrip(',')
                create_sql +=')\n'

                format_str=''
                if rv_extinfo[0][1] == 'b':
                    format_str += "format 'CUSTOM' ("
                    words = re.split(r"(\s+'(?:\w|\||\s)*'\s+)", rv_extinfo[0][2])[0:-1]
                    keys=words[::2]
                    values=words[1::2]
                    for i in range(0,len(keys)):
                        format_str += keys[i]+'='+values[i].replace("'\n'","E'\\n'")+','
                    format_str=format_str.rstrip(',')+')\n'
                else:
                    if rv_extinfo[0][1] == 't':
                        format_str="format 'TEXT'("+rv_extinfo[0][2].replace("escape '\\'","escape E'\\\\'")+')\n'
                    else:
                        if rv_extinfo[0][1] == 'c':
                            format_str = "format 'CSV'(" + rv_extinfo[0][2] + ')\n'
                        else:
                            if rv_extinfo[0][1] == 'a':
                                format_str="format 'AVRO'\n"
                            else:
                                if  rv_extinfo[0][1] == 'p':
                                    format_str = "format 'PARQUET'\n"

                create_sql += format_str;

                encoding_str=''
                if rv_extinfo[0][3] == 6:
                    encoding_str='UTF8'
                create_sql +="encoding  '" + encoding_str +  "'\n"

                if  not is_writable:
                    create_sql +="log errors into gp_load_error segment reject limit 100 rows\n"

        if reloptions:
            create_sql +="with("
            for option in reloptions:
                create_sql +=option+','
            #create_sql+=str(reloptions).lstrip('{').rstrip('}').lstrip('[').rstrip(']')+",\n"
            if relhasoids == True:
                create_sql += "OIDS=TRUE,"
            else:
                if relstorage != 'x':
                    create_sql += "OIDS=FALSE,"
            create_sql=create_sql.rstrip(',')+')\n'
        else:
            if relhasoids==True:
                create_sql+="with(\nOIDS=TRUE\n)\n"
            else:
                if relstorage != 'x':
                    create_sql+="with(\nOIDS=FALSE\n)\n"

        if rv_distribution2:
            create_sql += 'Distributed by ('
            for i in rv_distribution2:
                create_sql += i[0] + ','
            create_sql = create_sql.rstrip(',') + ')\n'
        elif rv_distribution1:
            if relstorage == 'x':
                if is_writable:
                    create_sql += 'Distributed randomly\n'
            else:
                create_sql += 'Distributed randomly\n'

        if v_par_parent:
            partitiontype = v_par_info[0][2]
            create_sql+='\nPARTITION BY ' + partitiontype + "("+v_par_parent[0][0]+")\n(\n";
            for i in v_par_info:
                create_sql+=" "+i[3]+',\n'
            create_sql = create_sql.rstrip(',\n')+ "\n)"
        create_sql += ";\n\n"

        for i in rv_index:
            create_sql += i[0]+';\n'
        get_table_comment="select 'comment on table %s is '''|| COALESCE (description,'')||'''' as comment from pg_description where objoid=%s and objsubid=0;"%(tablename, table_oid)
        get_column_comment="select 'comment on column %s.'|| b.attname ||' is ''' || COALESCE( a.description,'') ||''' ' as comment from pg_catalog.pg_description a, pg_catalog.pg_attribute b where objoid=% s and a.objoid= b.attrelid and a.objsubid= b.attnum;"%(tablename, table_oid) 
        rv_table_comment= self.queryDB(get_table_comment)
        rv_column_comment= self.queryDB(get_column_comment)
        for i in rv_table_comment:
            create_sql += i[0]+';\n'
        for i in rv_column_comment:
            create_sql += i[0]+';\n' 
               
        print(create_sql)
        return create_sql

    def get_view_ddl(self,viewname):

        get_view_oid = "select oid from pg_class where relkind='v' and oid='%s'::regclass"%(viewname)
        rv_oid=self.queryDB(get_view_oid)
        if not rv_oid or not rv_oid[0]:
            return "View "+viewname+" does not exist"

        view_oid = rv_oid[0][0]
        get_view_def="select pg_get_viewdef(%s,' t') as viewdef;"%(view_oid)
        rv_viewdef= self.queryDB(get_view_def)
        create_sql = 'create view %s as \n'%(viewname)
        create_sql += rv_viewdef[0]['viewdef']+'\n'	    
        return create_sql

    def get_function_ddl(self,schemaname,funcname):
        type_dict={  23:'integer',
                   1043:'character varying'}
        get_function = "select proname,pronargs,proargtypes,proargnames,prorettype,prosrc from pg_proc t1,pg_namespace t2 where t1.pronamespace = t2.oid and t2.nspname='%s' and  proname='%s'"%(schemaname,funcname)
        rv_func=self.queryDB(get_function)
        if not rv_func or not rv_func[0]:
            return "Funcion " +schemaname+'.'+funcname + " does not exist"
        procname=rv_func[0][0]
        nargs=rv_func[0][1]
        arg_types = rv_func[0][2].split(' ')
        arg_names=rv_func[0][3]
        arg_str = ''
        for i in range(0,nargs):
            arg_str +=arg_names[i]+' '+type_dict[int(arg_types[i])]+',\n'
        arg_str=arg_str.rstrip(',\n')
        ret_type=rv_func[0][4]
        procsrc=rv_func[0][5]
        create_sql = 'CREATE OR REPLACE FUNCTION  %s.%s (\n'%(schemaname,procname)
        create_sql +=arg_str+')\n'
        create_sql += 'RETURNS '+type_dict[ret_type] +' AS\n'
        create_sql += '$BODY$'+procsrc
        create_sql +='$BODY$ \n LANGUAGE plpgsql VOLATILE ;'
        #print(create_sql)

        return create_sql

    def get_schema_ddl(self,schema):
        #get_tables = "select a.relname from pg_class a,pg_namespace b where a.relnamespace=b.oid and a.relkind='r' and b.nspname='%s'"%(schema)
        get_tables = "select tablename from pg_tables where schemaname='%s'"%(schema)
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "Schema "+schema+" not exist or does not contain tables"

        for table in rv_tables:
            print('--'+table[0])
            tabledef=self.get_table_ddl(schema+'.'+table[0])
            with open('sql/'+table[0]+'.sql','w') as f:
                f.write(tabledef)

    def get_ddl_script(self, pattern):
        get_tables = "select schemaname,tablename from pg_tables where tablename like '%s' order  by schemaname,tablename"%(pattern)
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "no table matches pattern"

        cmdfile = open('sql/cmd.sh', 'w',encoding='utf-8')
        for table in rv_tables:
            print('--'+table[1])
            tabledef=self.get_table_ddl(table[0]+'.'+table[1])
            with open('sql/'+table[1]+'.sql','w',encoding='utf-8') as f:
                f.write('set search_path to %s;\n'%table[0])
                f.write('drop table %s.%s;\n' % (table[0],table[1]))
                f.write(tabledef)
            cmdfile.write('psql -d cogp -f '+table[1]+'.sql;\n')
        cmdfile.close()

    def get_transfer_script(self,pattern):
        get_tables = "select schemaname,tablename from pg_tables where tablename like '%s' order by schemaname,tablename"%(pattern)
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "no table matches pattern"

        cmdfile = open('sql/transfer.sh', 'w',encoding='utf-8')
        for table in rv_tables:
            cmdfile.write("echo 'Tranfering  %s';\n"%table[1])
            cmdfile.write("date;\n")
            cmdfile.write("psql -h 21.136.64.203 -p 5432 -U ridshcz -w huang056 -d gp -c 'copy %s.%s to STDOUT'| psql -d cogp -c 'copy %s.%s from STDIN';\n"%(table[0],table[1],table[0],table[1]))
        cmdfile.close()


    def generate_bancs_script(self):
        #get_tables = "select a.relname from pg_class a,pg_namespace b where a.relnamespace=b.oid and a.relkind='r' and b.nspname='%s'"%(schema)
        get_tables = "select schemaname,tablename from pg_tables where schemaname='ods' and tablename like 'bancs_%_f' and not (tablename like 'bancs_inct%' or tablename like 'bancs_inct%' or tablename like 'bancs_gect%' or tablename like 'bancs_boct%') order by schemaname,tablename"
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "no table exist"

        ddlFile = open('sql/ddl.sh', 'w', encoding='utf-8')
        for table in rv_tables:
            print('--' + table[1])
            if self.is_empty_table(table[0], table[1]):
               continue

            schemaName=table[0]
            table_f=table[1]
            self.write_ddl_file(schemaName,table_f)
            ddlFile.write('psql -d cogp -f ' + table_f+ '.sql;\n')
            self.write_function_file(schemaName,'fn_'+table_f)
            ddlFile.write('psql -d cogp -f ' + 'fn_'+table_f+ '.sql;\n')

            table_i=re.sub('_f$','_i',table_f)
            if self.is_table_exist(schemaName,table_i):
                self.write_ddl_file(schemaName, table_i)
                ddlFile.write('psql -d cogp -f ' + table_i+ '.sql;\n')

            table_ext=re.sub('_f$','_i_ext',table_f)
            if self.is_table_exist(schemaName,table_ext):
                self.write_ddl_file(schemaName, table_ext)
                ddlFile.write('psql -d cogp -f ' + table_ext+ '.sql;\n')

            table1_ext=re.sub('_f$','_f_ext',table_f)
            if self.is_table_exist(schemaName,table1_ext):
                self.write_ddl_file(schemaName, table1_ext)
                ddlFile.write('psql -d cogp -f ' + table1_ext+ '.sql;\n')

            table2_ext=re.sub('_f$','_i2_ext',table_f)
            if self.is_table_exist(schemaName,table2_ext):
                self.write_ddl_file(schemaName, table2_ext)
                ddlFile.write('psql -d cogp -f ' + table2_ext+ '.sql;\n')

            table3_ext=re.sub('_f$','_i3_ext',table_f)
            if self.is_table_exist(schemaName,table3_ext):
                self.write_ddl_file(schemaName, table3_ext)
                ddlFile.write('psql -d cogp -f ' + table3_ext+ '.sql;\n')

            table4_ext=re.sub('_f$','_i4_ext',table_f)
            if self.is_table_exist(schemaName,table4_ext):
                self.write_ddl_file(schemaName, table4_ext)
                ddlFile.write('psql -d cogp -f ' + table4_ext+ '.sql;\n')

        ddlFile.close()

        transferFile = open('sql/transfer.sh', 'w',encoding='utf-8')
        for table in rv_tables:
             if self.is_empty_table(table[0], table[1]):
                continue
             transferFile.write("echo 'Tranfering  %s';\n"%table[1])
             transferFile.write("date;\n")
             if self.is_hybrid(table[0],table[1]):
                 transferFile.write(
                     "psql -h 21.136.64.203 -p 5432 -U ridshcz -w huang056 -d gp -c 'copy (select * from %s.%s where cus_type<>'1') to STDOUT'| psql -d cogp -c 'copy %s.%s from STDIN';\n" % (
                     table[0], table[1], table[0], table[1]))
             else:
                transferFile.write("psql -h 21.136.64.203 -p 5432 -U ridshcz -w huang056 -d gp -c 'copy %s.%s to STDOUT'| psql -d cogp -c 'copy %s.%s from STDIN';\n"%(table[0],table[1],table[0],table[1]))
        transferFile.close()

    def generate_subsys_script(self,systemname):
        get_tables = "select schemaname,tablename from pg_tables where schemaname='ods' and tablename like '"+systemname+"_%_f' order by schemaname,tablename "
        print(get_tables)
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "no table exist"

        ddlFile = open('sql/ddl.sh', 'w', encoding='utf-8')
        for table in rv_tables:
            print('--' + table[1])
            schemaName=table[0]
            table_f=table[1]
            self.write_ddl_file(schemaName,table_f)
            ddlFile.write('psql -d cogp -f ' + table_f+ '.sql;\n')
            self.write_function_file(schemaName,'fn_'+table_f)
            ddlFile.write('psql -d cogp -f ' + 'fn_'+table_f+ '.sql;\n')

            table_i=re.sub('_f$','_i',table_f)
            if self.is_table_exist(schemaName,table_i):
                self.write_ddl_file(schemaName, table_i)
                ddlFile.write('psql -d cogp -f ' + table_i+ '.sql;\n')

            table_f_ext=re.sub('_f$','_f_ext',table_f)
            if self.is_table_exist(schemaName,table_f_ext):
                self.write_ddl_file(schemaName, table_f_ext)
                ddlFile.write('psql -d cogp -f ' + table_f_ext+ '.sql;\n')

            table_i_ext=re.sub('_f$','_i_ext',table_f)
            if self.is_table_exist(schemaName,table_i_ext):
                self.write_ddl_file(schemaName, table_i_ext)
                ddlFile.write('psql -d cogp -f ' + table_i_ext+ '.sql;\n')
        ddlFile.close()

        transferFile = open('sql/transfer.sh', 'w',encoding='utf-8')
        for table in rv_tables:
             if self.is_empty_table(table[0], table[1]):
                continue
             transferFile.write("echo 'Tranfering  %s';\n"%table[1])
             transferFile.write("date;\n")
             if self.is_hybrid(table[0],table[1]):
                 transferFile.write(
                     "psql -h 21.136.64.203 -p 5432 -U ridshcz -w huang056 -d gp -c 'copy (select * from %s.%s where cus_type<>'1') to STDOUT'| psql -d cogp -c 'copy %s.%s from STDIN';\n" % (
                     table[0], table[1], table[0], table[1]))
             else:
                transferFile.write("psql -h 21.136.64.203 -p 5432 -U ridshcz -w huang056 -d gp -c 'copy %s.%s to STDOUT'| psql -d cogp -c 'copy %s.%s from STDIN';\n"%(table[0],table[1],table[0],table[1]))
        transferFile.close()

    def is_empty_table(self,schemaname, tablename):
        query = "select * from %s.%s limit 5"%(schemaname,tablename)
        rv_rows=self.queryDB(query)
        if rv_rows and rv_rows[0]:
            return False
        else:
            return True

    def is_table_exist(self,schemaName,tableName):
        get_tables = "select schemaname,tablename from pg_tables where schemaname='%s' and tablename='%s'"%(schemaName,tableName)
        rv_tables = self.queryDB(get_tables)
        if rv_tables and rv_tables[0]:
            return True
        else:
            return False

    def is_hybrid(self,schemaname, tablename):
        ext_table=re.sub('_f$','_i2_ext',tablename)
        return self.is_table_exist(schemaname,ext_table)

    def write_ddl_file(self, schemaname, tablename):
        tabledef = self.get_table_ddl(schemaname + '.' + tablename)
        if tabledef:
            with open('sql/' + tablename + '.sql', 'w', encoding='utf-8') as f:
                f.write('set search_path to %s;\n' % schemaname)
                if tablename.endswith('_ext'):
                    f.write('drop external table if exists %s.%s  ;\n' % (schemaname, tablename))
                else:
                    f.write('drop table if exists %s.%s  ;\n' % (schemaname, tablename))
                f.write(tabledef)

    def write_function_file(self, schemaname, funcname):
        tabledef = self.get_function_ddl(schemaname ,funcname)
        if tabledef:
            with open('sql/' + funcname + '.sql', 'w', encoding='utf-8') as f:
                f.write(tabledef)


tools=GPTransfer("gp", "ridshcz", "huang056", "21.136.64.203", "5432")
#tools=GPTools("gpDB","gpmon","gpmon","192.168.3.5","5432")
#tools.get_schema_ddl('ods')
#tools.get_ddl_script('bancs_%_f_ext')
#tools.get_transfer_script('bancs_%_f')
#tools.get_table_ddl('ods.bancs_csfm_f')
#tools.get_function_ddl('ods','fn_bancs_invm_f')
#tools.generate_bancs_script()
tools.generate_subsys_script('grms')
