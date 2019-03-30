#!/usr/bin/python

import psycopg2

class GPTools:
    __conn=None
    def __init__(self,database,user,password,host,port):
        self.__conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
      
    def __del__(self):
        self.__conn.close()

    def queryDB(self,sql):
        try:
            cur=self.__conn.cursor()
            cur.execute(sql)
            #result=[r for r in cur]
            result=cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            print(e)

    def get_table_ddl(self,tablename):
        
        get_table_status = "select oid, reloptions,relhasoids from pg_class where relkind='r' and oid='%s'::regclass"%(tablename)
        rv_table=self.queryDB(get_table_status)
        if not rv_table or not rv_table[0]:
            return "Table "+tablename+" does not exist"
        table_oid = rv_table[0][0]
        reloptions = rv_table[0][1]
        relhasoids = rv_table[0][2]     
      
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
            get_table_distribution2 = "SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum in ("%table_oid + str(rv_distribution1[0][0]).strip('{').strip('}').strip('[').strip(']') + ")"
            rv_distribution2 = self.queryDB(get_table_distribution2)
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
        create_sql=create_sql.strip(',\n')+'\n)\n'
        create_sql+="with(\n"
        if reloptions:
            create_sql+=str(reloptions).strip('{'). strip('}').strip('[').strip(']')+",\n"
        if relhasoids==True:
            create_sql+="OIDS=TRUE"
        else:
            create_sql+="OIDS=FALSE"
        create_sql+="\n)\n" 
        if rv_distribution2:
            create_sql += 'Distributed by ('
            for i in rv_distribution2:
                create_sql += i[0] + ','
            create_sql = create_sql.strip(',') + ')'
        elif rv_distribution1:
            create_sql += 'Distributed randomly\n'
            
        if v_par_parent:
            partitiontype = v_par_info[0][2]
            create_sql+='\nPARTITION BY ' + partitiontype + "("+v_par_parent[0][0]+")\n(\n";
            for i in v_par_info:
                create_sql+=" "+i[3]+',\n'
            create_sql = create_sql.strip(',\n')+ "\n)"
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


    def get_schema_ddl(self,schema):

        #get_tables = "select a.relname from pg_class a,pg_namespace b where a.relnamespace=b.oid and a.relkind='r' and b.nspname='%s'"%(schema)
        get_tables = "select tablename from pg_tables where schemaname='%s'"%(schema)
        rv_tables=self.queryDB(get_tables)
        if not rv_tables or not rv_tables[0]:
            return "Schema "+schema+" not exist or does not contain tables"

        for table in rv_tables:
            print('--'+table[0])
            self.get_table_ddl(table[0])

    def get_big_table(self):

        get_tables = '''select * from
            (select relname,relfilenode,pg_size_pretty(pg_relation_size(oid)) as size 
                from pg_class where relkind='r' 
                order by pg_relation_size(oid) desc
            ) tab1
            fetch first 10 rows only'''

        rv_tables=self.queryDB(get_tables)
     
        for table in rv_tables:
            print(table[0],table[1],table[2])

    def get_table_dist(self,tablename):

        get_tables = "select gp_segment_id,pg_relation_size(oid)  from gp_dist_random('pg_class') where relname='%s'"%(tablename)

        rv_tables=self.queryDB(get_tables)
     
        for table in rv_tables:
            print(table[0],table[1])

    def get_dist_ratio(self):
        get_tables = '''select tabname, max(size)/(avg(size)+ 0.001) as max_div_avg,sum(size) total_size from 
            (select gp_segment_id, oid::regclass tabname, pg_relation_size(oid) size 
                from gp_dist_random('pg_class') where relkind='r' ) t 
            group by tabname 
            order by 2 desc'''

        rv_tables=self.queryDB(get_tables)
     
        for table in rv_tables:
            print(table[0],table[1])

    

tools=GPTools("gpDB","gpmon","gpmon","192.168.3.5","5432")
#table=tools.get_table_ddl('public.test')
tools.get_schema_ddl('public')
tools.get_big_table()
tools.get_dist_ratio()