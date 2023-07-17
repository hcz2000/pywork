#!/usr/bin/python

import psycopg2
import re

class GPTools:
    def __init__(self,database,user,password,host,port):
        self.conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)

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

    def get_segments(self):
        get_segment_sql="select hostname,port from gp_segment_configuration where role='p' and content>=0 order by  port,content"
        segments=self.queryDB(get_segment_sql)
        return segments

    def get_db_version(self):
        get_version_sql="select current_setting('server_version_num')"
        result=self.queryDB(get_version_sql)
        db_version=''
        if result and result[0]:
            db_version=result[0][0]
        return db_version

    def get_table_ddl(self, schema_name, table_name):
        fulltablename = schema_name + '.' + table_name
        db_version = self.get_db_version()
        get_table_status = "select oid, reloptions,relhasoids,relstorage from pg_class where relkind='r' and oid='%s'::regclass"%(fulltablename)
        rv_table=self.queryDB(get_table_status)
        if not rv_table or not rv_table[0]:
            return "Table " + fulltablename + " does not exist"
        table_oid = rv_table[0][0]
        reloptions = rv_table[0][1]
        relhasoids = rv_table[0][2]
        relstorage = rv_table[0][3]
        if relstorage == 'x':
            if db_version.startswith('90'):
                get_extinfo = "select urilocation,fmttype,fmtopts,encoding,writable,command,rejectlimit from pg_exttable where reloid=%s" % (
                    table_oid)
            else:
                get_extinfo = "select location,fmttype,fmtopts,encoding,writable,command,rejectlimit from pg_exttable where reloid=%s" % (
                    table_oid)
            rv_extinfo = self.queryDB(get_extinfo)
            if rv_extinfo:
                is_writable=rv_extinfo[0][4]
                file_locations=rv_extinfo[0][0]
      
        get_columns ='''SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod),a.attnotnull as isnull,
                (SELECT substring(pg_catalog.pg_get_expr(d.adbin,d.adrelid) for 128) 
                    FROM pg_catalog.pg_attrdef d 
                    WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) as default 
                FROM pg_catalog.pg_attribute a 
                WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum;''' %(table_oid); 
        rv_columns = self.queryDB(get_columns)
        if db_version.startswith('90'):
            get_table_distribution1 = "SELECT distkey FROM pg_catalog.gp_distribution_policy t WHERE localoid = %s" % table_oid
        else:
            get_table_distribution1 = "SELECT attrnums FROM pg_catalog.gp_distribution_policy t WHERE localoid = %s" % table_oid
        rv_distribution1 = self.queryDB(get_table_distribution1)
        rv_distribution2 = None
        if rv_distribution1 and rv_distribution1[0][0]:
            if db_version.startswith('90'):
                distribution_key_string = str(rv_distribution1[0][0]).replace(' ', ',')
            else:
                distribution_key_string = str(rv_distribution1[0][0]).lstrip('{').rstrip('}').lstrip('[').rstrip(']')
            get_table_distribution2 = "SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum in (%s) order by position(attnum::text in '%s')" % (
            table_oid, distribution_key_string, distribution_key_string)
            rv_distribution2 = self.queryDB(get_table_distribution2)

        if  relstorage == 'x':
            if is_writable:
                create_sql = 'create writable external table %s(\n' % (fulltablename)
            else:
                if file_locations:
                    create_sql = 'create external table %s(\n' % (fulltablename)
                else:
                    create_sql = 'create external web table %s(\n' % (fulltablename)
        else:
            create_sql = 'create table %s(\n'%(fulltablename)
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
            if rv_extinfo:
                if file_locations:
                    create_sql += 'location ('
                    loc_str=''
                    for loc in file_locations:
                        loc_str +="'"+loc+"',"
                    create_sql +=loc_str.rstrip(',')
                    create_sql +=')\n'
                else:
                    command_str=rv_extinfo[0][5]
                    create_sql += "execute '"+command_str +"'\n"

                format_str=''
                target_encoding = ''
                if rv_extinfo[0][1] == 'b':
                    format_str += "format 'CUSTOM' ("
                    words = re.split(r"(\s+'(?:\w|\||\s|\$|-)*'\s+)", rv_extinfo[0][2])[0:-1]
                    keys=words[::2]
                    values=words[1::2]
                    for i in range(0,len(keys)):
                        if keys[i]=='encoding':
                            format_str += "encoding 'UTF8',"
                            target_encoding = values[i].lstrip(' ').rstrip(' ').lstrip("'").rstrip("'")
                            if target_encoding == 'UTF-8':
                                target_encoding = 'UTF8'
                        else:
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

                encoding_str = ''
                if rv_extinfo[0][3] == 6:
                    encoding_str = 'UTF8'
                if rv_extinfo[0][3] == 39:
                    encoding_str = 'GB18030'
                # switch target and source encoding,fix gp4 mis-define
                if target_encoding != '' and encoding_str == 'UTF8':
                    encoding_str = target_encoding
                create_sql += "encoding  '" + encoding_str + "'\n"

                if rv_extinfo[0][6]:
                    create_sql += "segment reject limit " + str(rv_extinfo[0][6]) + " rows\n"

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
        get_table_comment="select 'comment on table %s is '''|| COALESCE (description,'')||'''' as comment from pg_description where objoid=%s and objsubid=0;"%(fulltablename, table_oid)
        get_column_comment="select 'comment on column %s.'|| b.attname ||' is ''' || COALESCE( a.description,'') ||''' ' as comment from pg_catalog.pg_description a, pg_catalog.pg_attribute b where objoid=% s and a.objoid= b.attrelid and a.objsubid= b.attnum;"%(fulltablename, table_oid)
        rv_table_comment= self.queryDB(get_table_comment)
        rv_column_comment= self.queryDB(get_column_comment)
        for i in rv_table_comment:
            create_sql += i[0]+';\n'
        for i in rv_column_comment:
            create_sql += i[0]+';\n' 
               
        #print(create_sql)
        return create_sql

    def get_view_ddl(self, schema_name, view_name):
        fullviewname= schema_name + '.' + view_name
        get_view_oid = "select oid from pg_class where relkind='v' and oid='%s'::regclass"%(fullviewname)
        rv_oid=self.queryDB(get_view_oid)
        if not rv_oid or not rv_oid[0]:
            return "View " + fullviewname + " does not exist"

        view_oid = rv_oid[0][0]
        get_view_def="select pg_get_viewdef(%s) as viewdef;"%(view_oid)
        rv_viewdef= self.queryDB(get_view_def)
        create_sql = 'create view %s as \n'%(fullviewname)
        #create_sql += rv_viewdef[0]['viewdef']+'\n'
        create_sql += rv_viewdef[0][0] + '\n'
        #print(create_sql)
        return create_sql

    def get_type(self,type_oid):
        get_type = "select typname from pg_type where oid=%s" % (type_oid)
        rv_type = self.queryDB(get_type)
        if rv_type and rv_type[0]:
            return rv_type[0][0]
        return None


    def get_function_ddl(self, schema_name, func_name):
        get_function = "select proname,pronargs,proargtypes,proargnames,prorettype,prosrc from pg_proc t1,pg_namespace t2 where t1.pronamespace = t2.oid and t2.nspname='%s' and  proname='%s'" % (
            schema_name, func_name)
        rv_func = self.queryDB(get_function)
        if not rv_func or not rv_func[0]:
            return "Funcion " + schema_name + '.' + func_name + " does not exist"
        procname = rv_func[0][0]
        nargs = rv_func[0][1]
        arg_types = rv_func[0][2].split(' ')
        arg_names = rv_func[0][3]
        arg_str = ''
        for i in range(0, nargs):
            # arg_str +=arg_names[i]+' '+self.get_type(int(arg_types[i]))+',\n'
            if arg_names == None:
                arg_str += self.get_type(arg_types[i]) + ',\n'
            else:
                arg_str += arg_names[i] + ' ' + self.get_type(arg_types[i]) + ',\n'
        arg_str = arg_str.rstrip(',\n')
        ret_type = rv_func[0][4]
        procsrc = rv_func[0][5]
        create_sql = 'CREATE OR REPLACE FUNCTION  %s.%s (\n' % (schema_name, procname)
        create_sql += arg_str + ')\n'
        create_sql += 'RETURNS ' + self.get_type(ret_type) + ' AS\n'
        create_sql += '$BODY$' + procsrc
        create_sql += '$BODY$ \n LANGUAGE plpgsql VOLATILE ;'
        print(create_sql)
        return create_sql

    def generate_dblink_ddl(self, schema_name,table_name):
        fulltablename = schema_name + table_name
        get_table_status = "select oid, reloptions,relhasoids from pg_class where relkind='r' and oid='%s'::regclass" % (
            fulltablename)
        rv_table = self.queryDB(get_table_status)
        if not rv_table or not rv_table[0]:
            return "Table " + fulltablename + " does not exist"
        table_oid = rv_table[0][0]

        get_columns = '''SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod),a.attnotnull as isnull,
                        (SELECT substring(pg_catalog.pg_get_expr(d.adbin,d.adrelid) for 128) 
                            FROM pg_catalog.pg_attrdef d 
                            WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) as default 
                        FROM pg_catalog.pg_attribute a 
                        WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum;''' % (
            table_oid);
        rv_columns = self.queryDB(get_columns)

        dblink_sql = '''select * from dblink('%s','select * from %s') as t(\n''' % (self.dblink, fulltablename)

        for i in rv_columns:
            # att_name
            if i[0]:
                max_column_len = 10
                if max_column_len < i[0].__len__():
                    max_column_len = i[0].__len__()
                dblink_sql += ' ' + i[0].ljust(max_column_len + 6)
            # format_type
            if i[1]:
                max_type_len = 4
                if max_type_len < i[1].__len__():
                    max_type_len = i[1].__len__()
                dblink_sql += ' ' + i[1].ljust(max_type_len + 2)
            dblink_sql += ",\n"
        dblink_sql = dblink_sql.rstrip(',\n') + '\n)\n'
        dblink_sql += ";\n"

        #print(dblink_sql)
        return dblink_sql

    def is_partition_child(self, schema_name, table_name):
        fulltablename = schema_name + '.' + table_name
        get_table="select  parchildrelid, parname from  pg_partition_rule  where parchildrelid='%s'::regclass"%(fulltablename)
        rv_tables = self.queryDB(get_table)
        if rv_tables:
            return True
        else:
            return False

    def is_partition_parent(self, schema_name, table_name):
        fulltablename = schema_name + '.' + table_name
        get_table="select  parkind, parlevel from  pg_partition  where parrelid='%s'::regclass"%(fulltablename)
        rv_tables = self.queryDB(get_table)
        if rv_tables:
            return True
        else:
            return False

    def get_partition_table_size(self, schema_name, table_name):
        fulltablename = schema_name + '.' + table_name
        get_table = "select sum(pg_relation_size(t2.parchildrelid)) from pg_partition t1,pg_partition_rule t2,pg_class t3 where t2.paroid=t1.oid and t3.oid=t1.parrelid and t1.parrelid='%s'::regclass" % (fulltablename)
        rv_tables = self.queryDB(get_table)
        if rv_tables and rv_tables[0]:
            return rv_tables[0][0]
        else:
            return 0
