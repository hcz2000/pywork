#!/usr/bin/python

import re
import os
import sys
import getopt

class FileChecker:
    def __init__(self,source_dir):
        self.source_dir=source_dir

    def processing_folder(self, relative_folder_path):
        folder_path=os.path.join(self.source_dir,relative_folder_path)
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path,file_name)
            if os.path.isfile(file_path):
                #print('...Processing: ', file_path)
                relative_file_path=os.path.join(relative_folder_path,file_name)
                self.processing_file(relative_file_path)
            elif os.path.isdir(file_path):
                dir_name=os.path.split(file_path)[-1]
                relative_path=os.path.join(relative_folder_path,dir_name)
                self.processing_folder(relative_path)


    def processing_file(self, relative_file_path):
        source_file=os.path.join(self.source_dir,relative_file_path)
        if source_file.endswith('.pc') or source_file.endswith('.c'):
            with open(source_file, 'r',encoding='gbk') as srcfile:
                content=srcfile.read()
                self.check(relative_file_path,content)

    def check(self,relative_file_path,content):
        block_list = re.findall(r'#if\s+([01]|[\w]+)([\S\s]*?)#endif', content, flags=re.MULTILINE)
        for block in  block_list:
            if re.search(r'#if',block[1],flags=re.MULTILINE):
                print(relative_file_path, ":存在嵌套#if/#end")

        remark_block_list = re.findall( r'/\*([\S\s]*?)\*/', content, flags=re.MULTILINE)
        for remark_block in remark_block_list:
            remark_text=remark_block
            #print(remark_text)
            if remark_text.find('/*')>0:
                print(relative_file_path, ":存在嵌套/* */注释块")

        sql_list= re.findall(r'EXEC\s+SQL([\s\S]+?);', content)
        for sql in sql_list:
            remark_st=re.search(r'//([\s\S]*?)\n',sql,flags=re.MULTILINE)
            if remark_st:
                print(relative_file_path, ":ESQL语句使用了//注释---",remark_st[0])

        neat_content = re.sub(r'/\*[\S\s]*?\*/', '', content , count=0)
        neat_content = re.sub(r'\n\s*\n', '\n', neat_content, count=0)
        sql_list= re.findall(r'EXEC\s+SQL([\s\S]+?);', neat_content)
        for sql in sql_list:
            dblink_tab=re.search(r'(\w+@\w+)[;\s\)]',sql, flags=re.MULTILINE)
            if dblink_tab:
                print(relative_file_path, ":ESQL语句使用了dblink表---",dblink_tab[0])

def main(argv):
    if len(argv)!=2:
        print('Usage: FileChecker.py -d <directory> ')
        sys.exit(1)
    try:
        opts,args=getopt.getopt(argv,"d:")
    except getopt.GetoptError:
        print('Usage: FileChecker.py -d <directory>')
        sys.exit(1)
    for opt,arg in opts:
        if opt=='-d':
            dir = arg
        else:
            print('Usage: FileChecker.py -d <directory>')
            sys.exit(1)
    checker = FileChecker(dir)
    #checker.processing_file("finReach\\libntax_DZ_Gdco.pc")
    #checker.processing_file("cspHandle\\libntax_migrate_sj.c")
    checker.processing_folder(".")

if __name__ == "__main__":
     main(sys.argv[1:])