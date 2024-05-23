#!/usr/bin/python

import cx_Oracle
import re
import csv
import sys
import os
import getopt
import decimal
import yaml

class OracelExport:
    def __init__(self,user,password,host,service):
        with open('table_config.yaml', 'r') as file:
            config=yaml.safe_load(file)
        self.lob_tables = config['config']['lob_tables']
        #cx_Oracle.init_oracle_client("D:\Program Files\instantclient_64")
        self.conn=cx_Oracle.connect(user+'/'+password+'@'+host+'/'+service)
        self.user=user
        if not os.path.exists('ddl'):
            os.makedirs('ddl')
        if not os.path.exists('data'):
            os.makedirs('data')

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

    def exportTables(self):
        print('---------Generate TABLE DDL file---------\n')
        sql_tables = "select table_name from user_tables order by table_name"
        tables = self.queryDB(sql_tables)
        if not tables or not tables[0]:
            return "No table defined"

        ddlfile = open('./ddl/tables.sql', 'w', encoding='utf-8')
        constrainfile = open('./ddl/constrains.sql', 'w', encoding='utf-8')

        pri_pattern = r'([\w\s\'\.-]+\([\w\s\'\,\.\*-]+\))?[\w\s\'\,\.\*-]*'
        col_pattern = r'([\w\s\'\.-]+\(' + pri_pattern + r'\)){0,2}[\w\s\'\.-]*'
        table_pattern = r'(CREATE\s+TABLE\s+[\w-]+\.[\w-]+\s*\((' + col_pattern + r'[\,\)])*)'
        table_reg = re.compile(r'^\s*'+table_pattern+r'([\s\S]*)',flags=re.MULTILINE)

        pk_constrain_pattern = r'(CONSTRAINT [\w]+ )?(PRIMARY KEY \([\w\s\,-]+\))[\w\s\'\.-]*(\([\w\s\,\.\*-]+\))?[\w\s\'\.-]*'
        pk_constrain_reg = re.compile(r'^\s*'+pk_constrain_pattern + r'[\,\)]', flags=re.MULTILINE)
        unique_index_pattern= r'(CONSTRAINT [\w]+ )?(UNIQUE \([\w\s\,-]+\))[\w\s\'\.-]*(\([\w\s\,\.\*-]+\))?[\w\s\'\.-]*'
        unique_index_reg=re.compile(r'\s*' + unique_index_pattern , flags=re.MULTILINE)
        fk_constrain_pattern = r'CONSTRAINT[\w\s\]+FOREIGN KEY \([\w\s\,-]+\)[\w\s\.]+\([\w\s\,]+\)'
        fk_constrain_reg = re.compile(r'\s*' + fk_constrain_pattern , flags=re.MULTILINE)

        for table in tables:
            tablename=table[0]
            sql_table_ddl = "select dbms_metadata.get_ddl('TABLE','%s','%s') from dual"%(tablename,self.user.upper())
            table_ddls=self.queryDB(sql_table_ddl)
            for table_ddl in table_ddls:
                #print(tablename+"\n")
                ddlfile.write("DROP TABLE IF EXISTS " + self.user.upper() + "." + tablename + " CASCADE;\n")
                ddl_lob=table_ddl[0]
                ddl_gauss=ddl_lob.read()
                #ddlfile.write(ddl_gauss)
                ddl_gauss=re.sub(r"\"","",ddl_gauss,count=0)
                match = re.match(table_reg,ddl_gauss)
                if match:
                    ddl_gauss=match.group(1)
                    ddl_remain=match.group(5)
                    if ddl_remain:
                        constrain_exist=re.search(r'[^\s]CONSTRAINT\s',ddl_remain,flags=re.MULTILINE)
                        if constrain_exist:
                            print('Somethin wrong with %s DDL:%s\n' % (ddl_remain, ddl_gauss))
                            continue
                else:
                    if re.match(r'^\s*CREATE GLOBAL TEMPORARY TABLE',ddl_gauss,flags=re.MULTILINE):
                        ddlfile.write(ddl_gauss + ";\n")
                    else:
                        print('Somethin wrong with %s DDL:%s\n'%(tablename,ddl_gauss))
                    continue

                ddl_gauss=re.sub(r"NOT\sNULL\sENABLE","NOT NULL",ddl_gauss,count=0)
                ddl_gauss=re.sub(r"\)\s+ENABLE",")",ddl_gauss,count=0)
                ddl_gauss=re.sub(r"NUMBER\(\*","NUMBER(16",ddl_gauss,count=0)

                match_list = re.findall(r'[^\s\(]\s*([\w-]+\s+)(LONG\s*[\,\)])', ddl_gauss, flags=re.MULTILINE)
                for match in match_list:
                    criteria = match[0]+'LONG'
                    repl = match[0] + "TEXT"
                    ddl_gauss = re.sub(criteria, repl, ddl_gauss, flags=re.MULTILINE)
                    print("%s: %s LONG->TEXT" % (tablename, match[0]))

                match_list = re.findall(r'[^\s\(]\s*([\w-]+\s+VARCHAR2)(\()(\d+)(\s+CHAR\))', ddl_gauss, flags=re.MULTILINE)
                for match in match_list:
                    criteria = match[0] + r"\(\d+\s+CHAR\)"
                    repl = match[0] + "(" + match[2] + ")"
                    ddl_gauss = re.sub(criteria, repl, ddl_gauss, flags=re.MULTILINE)
                    print("%s: %s(%s CHAR)->%s" % (tablename, match[0],match[2], repl))

                match_list = re.findall(r'[^\s\(]\s*([\w-]+\s+FLOAT)(\()(\d+)(\))', ddl_gauss, flags=re.MULTILINE)
                for match in match_list:
                    precise=int(match[2])
                    if precise>53:
                        criteria = match[0] + "\(\d+\)"
                        repl = match[0] + "(53)"
                        ddl_gauss = re.sub(criteria, repl, ddl_gauss, flags=re.MULTILINE)
                        print("%s: Float(%d)->Float(53)"%(tablename,precise))

                pk_constrain = re.search(pk_constrain_reg,ddl_gauss)
                if pk_constrain:
                    new_pk_str = pk_constrain.group(2)
                    ddl_gauss = re.sub(pk_constrain_pattern, new_pk_str, ddl_gauss, flags=re.MULTILINE)

                unique_index_list = re.findall(unique_index_reg,ddl_gauss)
                if unique_index_list:
                    for constrain in unique_index_list:
                        constrain_ddl = 'ALTER TABLE %s.%s ADD %s' % (self.user.upper(), tablename.upper(), constrain[1])
                        constrainfile.write(constrain_ddl + ';\n');
                    ddl_gauss = re.sub(r'\,\s*'+unique_index_pattern,"",ddl_gauss,count=0,flags=re.MULTILINE)


                fk_list = re.findall(fk_constrain_reg,ddl_gauss)
                if fk_list:
                    for constrain in fk_list:
                        constrain_ddl = 'ALTER TABLE %s.%s ADD %s' % (self.user.upper(), tablename.upper(), constrain)
                        constrainfile.write(constrain_ddl + ';\n');
                    ddl_gauss = re.sub(r'\,\s*'+fk_constrain_pattern,"",ddl_gauss,count=0,flags=re.MULTILINE)

                ddlfile.write(ddl_gauss+";\n")
        ddlfile.close()
        constrainfile.close()

    def exportViews(self):
        print('---------Generate VIEW DDL file---------\n')
        sql_views = "select view_name,text from user_views order by view_name"
        views = self.queryDB(sql_views)
        if not views or not views[0]:
            return "No view defined"

        ddlfile = open('./ddl/views.sql', 'w', encoding='utf-8')
        for view in views:
            viewname = view[0]
            ddl_text = view[1]
            ddl_gauss = 'CREATE OR REPLACE VIEW %s.%s AS '%(self.user.upper(),viewname)+ddl_text
            ddlfile.write(ddl_gauss+";\n")
        ddlfile.close()


    def exportSequences(self):
        print('---------Generate SEQUENCE DDL file---------\n')
        sql_Sequences = '''select sequence_name,min_value,max_value,increment_by,cycle_flag,order_flag,cache_size,last_number 
                        from user_sequences order by sequence_name'''
        sequences = self.queryDB(sql_Sequences)
        if not sequences or not sequences[0]:
            return "No sequence defined"

        ddlfile = open('./ddl/sequences.sql', 'w', encoding='utf-8')
        for sequence in sequences:
            name=sequence[0]
            min_val=sequence[1]
            max_val=sequence[2]
            increment_by=sequence[3]
            cycle_flag=sequence[4]
            order_flag=sequence[5]
            cache_size=sequence[6]
            last_number=sequence[7]
            if max_val>999999999999999999:
                max_val=999999999999999999

            ddlfile.write("DROP SEQUENCE IF EXISTS "+self.user.upper()+"."+name+";\n")
            seq_ddl='CREATE SEQUENCE  %s.%s  MINVALUE %d MAXVALUE %d INCREMENT BY %d START WITH %d '%\
                    (self.user.upper(),name,min_val,max_val,increment_by,last_number)

            if cache_size>0:
                seq_ddl = seq_ddl+" CACHE %d"%cache_size
            else:
                seq_ddl = seq_ddl+" NOCACHE"
            if cycle_flag=='N':
                seq_ddl=seq_ddl+" NOCYCLE"
            else:
                seq_ddl = seq_ddl + " CYCLE"

            ddlfile.write(seq_ddl+";\n")

        ddlfile.close()

    def exportProcedures(self):
        print('---------Generate PROCEDURE DDL file---------\n')
        #sql_proc = "select owner,name,line,text from all_source where type='PROCEDURE' and OWNER<>'SYS' order by owner,name,line"
        sql_proc = "select owner,name,line,text from all_source where type='PROCEDURE' and OWNER='%s' order by owner,name,line"%self.user.upper()
        proc_lines = self.queryDB(sql_proc)
        if not proc_lines or not proc_lines[0]:
            return "No procedure defined"

        ddlfile = open('./ddl/procedures.sql', 'w', encoding='utf-8')
        first_table = True
        header_processed=True
        for proc_line in proc_lines:
            owner=proc_line[0]
            name=proc_line[1]
            line=proc_line[2]
            text = proc_line[3]
            if re.match(r"\s*$",text):
                continue
            if line==1:
                header=''
                if first_table:
                    first_table = False;
                else:
                    if header_processed==True:
                        ddlfile.write("$function$ LANGUAGE plpgsql;\n\n")
                header_processed=False

            if  not header_processed:
                header=header+text
                if re.search("(\s|^)(is|as)\s+",text,re.IGNORECASE)==None:
                    continue;

                pattern = r"\s*procedure\s+\"?" + name + r"\"?\s*\([A-Za-z0-9_,\s]*\)\s+(is|as)\s*"
                if re.match(pattern, header, flags=re.IGNORECASE):
                    pattern = r"\s*procedure\s+\"?" + name + r"\"?\s*"
                    repl = owner + '.' + name
                    modified_text = re.sub(pattern, repl, header, flags=re.IGNORECASE)
                    pattern = r"\s+(is|as)\s+"
                    repl = "\nRETURNS VOID \nAS $function$\nDECLARE\n"
                    modified_text = re.sub(pattern, repl, modified_text, flags=re.IGNORECASE)
                else:
                    pattern = r"\s*procedure\s+\"?" + name + r"\"?\s+(is|as)\s+"
                    if re.match(pattern, header, flags=re.IGNORECASE):
                        repl = owner + '.' + name + "()\nRETURNS VOID \nAS $function$\nDECLARE\n"
                    else:
                        print(header)
                        pattern = r"\s*procedure\s+" + name
                        repl = owner + '.' + name + "()"
                    modified_text = re.sub(pattern, repl, header, flags=re.IGNORECASE)
                header_processed=True
                ddlfile.write('CREATE OR REPLACE FUNCTION '+modified_text)
            else:
                modified_text = re.sub(r"\s*end\s+" + name, "end", text, flags=re.IGNORECASE)

                match = re.match(r"^(\s*DBMS_OUTPUT.PUT_LINE\s*\()([\w\s\|\']*)(\))", modified_text, flags=re.IGNORECASE)
                if match:
                    output_str = match.group(2)
                    repl = "RAISE NOTICE '%'," + output_str
                    modified_text = re.sub(r"DBMS_OUTPUT.PUT_LINE\s*\([\w\s\|\']*\)", repl, modified_text, count=0, flags=re.MULTILINE)

                match = re.match(r"^(\s*INSERT\s+INTO\s+[\w\-\_]*\.[\w\-\_]*)(\s+NOLOGGING)", modified_text, flags=re.IGNORECASE)
                if match:
                    repl = match.group(1)
                    modified_text = re.sub(r"^\s*INSERT\s+INTO\s+[\w\-\_]*\.[\w\-\_]*\s+NOLOGGING", repl, modified_text, count=0,flags=re.MULTILINE)

                modified_text = re.sub(r"^\s*DBMS_STATS" , "--DBMS_STATS", modified_text, flags=re.IGNORECASE)

                ddlfile.write(modified_text);

        ddlfile.write("$function$ LANGUAGE plpgsql;\n\n")
        ddlfile.close()

    def exportData(self):
        print('---------Export DATA----------\n')
        sql_tables = "select table_name from user_tables order by table_name"
        tables = self.queryDB(sql_tables)
        if not tables or not tables[0]:
            return "No table defined"

        with open('./data/copy2Gauss.sh', 'w', encoding='utf-8') as cmdfile:
            cmdfile.write('export current_dir=$(cd $(dirname $0);pwd);\n')
            for table in tables:
                tablename=table[0]
                if tablename in self.lob_tables:
                    continue
                print('-----'+tablename+'--------')
                sql="select * from %s.%s"%(self.user,tablename)
                result=self.queryDB(sql)
                if not result:
                    continue;

                cmdfile.write('gsql -d $destDB -c "truncate table %s.%s";\n'% (self.user.upper(),tablename));
                cmdfile.write('''gsql -d $destDB -c "copy %s.%s from '$current_dir/%s.csv' csv";\n'''
                              %(self.user.upper(),tablename,tablename));
                with open('./data/%s.csv'%tablename, 'w', encoding='utf-8', newline='') as datafile:
                    writer=csv.writer(datafile)
                    for row in result:
                        writer.writerow([str(item) if item!=None else '' for item in row]);

    def generateGaussInitScript(self):
        with open('./ddl/gaussInit.sh', 'w', encoding='utf-8') as cmdfile:
            for sqlfile in ["tables.sql","constrains.sql","views.sql","sequences.sql"]:
                if os.path.exists('ddl/'+sqlfile):
                    cmdfile.write('gsql -d $destDB -f %s;\n'%sqlfile)

            if os.path.exists('ddl/procedures.sql'):
                cmdfile.write('gsql -d $destDB -f procedures.sql 1>/dev/null 2>/dev/null;\n')
                cmdfile.write('gsql -d $destDB -f procedures.sql;\n')#redefine to avoid dependce between procedures

            cmdfile.write('gsql -d $destDB -c "grant all privileges on all tables in schema %s to %s";\n'%(self.user,self.user))
            cmdfile.write('gsql -d $destDB -c "grant all privileges on all sequences in schema %s to %s";\n' % (self.user, self.user))
            cmdfile.write('gsql -d $destDB -c "grant all privileges on all functions in schema %s to %s";\n' % (self.user, self.user))


def main(argv):
    dbuser=''
    dbpass=''
    dbhost=''
    dbservice=''
    if len(argv)!=8:
        print('Usage: Oracle2Gauss.py -h <host> -s <service> -u <user> -p <password>')
        sys.exit(1)
    try:
        opts,args=getopt.getopt(argv,"h:u:s:p:")
    except getopt.GetoptError:
        print('Usage: Oracle2Gauss.py -h <host> -s <service> -u <user> -p <password>')
        sys.exit(1)
    for opt,arg in opts:
        if opt=='-h':
            dbhost = arg
        elif opt == '-s':
            dbservice = arg
        elif opt == '-u':
            dbuser = arg
        elif opt == '-p':
            dbpass = arg
        else:
            print('Usage: Oracle2Gauss.py -h <host> -s <service> -u <user> -p <password>')
            sys.exit(1)

    #设置oracle client的路径，如有设置Oracle环境变量可不用显式设置
    cx_Oracle.init_oracle_client("D:\Program Files\instantclient_64")
    #Oracle数据库的用户/密码/ip/service
    #tools=OracelExport('gdic', 'gdic2011', '22.136.67.141', 'gdic')
    #tools=OracelExport('OPSP', 'OPSP', '22.136.66.192', 'dztd')
    #tools=OracelExport('wxss', 'password', '22.136.66.196', 'wxss')
    #tools=OracelExport('ntax_cs', 'ntax2011', '22.136.66.194', 'cbps')
    #tools = OracelExport('csas', 'zjyw20151224', '22.136.66.112', 'csas')
    #tools = OracelExport('jkgl', 'jkgl_2019', '22.136.66.191', 'bstk')
    tools = OracelExport(dbuser, dbpass, dbhost, dbservice)
    tools.exportTables()
    tools.exportViews()
    tools.exportSequences()
    tools.exportProcedures()
    tools.generateGaussInitScript()
    tools.exportData()

if __name__=="__main__":
    main(sys.argv[1:])
