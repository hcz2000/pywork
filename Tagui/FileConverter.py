
#!/usr/bin/python

import re
import os
import sys
import getopt
import yaml
import logging

class FileConverter:
    def __init__(self):
        with open('config_gwks.yaml', 'r') as file:
            self.config=yaml.safe_load(file)

        self.source_dir = self.config['converter']['sourcedir']
        self.target_dir = self.config['converter']['targetdir']
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        self.logger = logging.getLogger('logger')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        file_handler = logging.FileHandler(filename='convert.log', mode='w')
        file_handler.setLevel(logging.DEBUG)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        param_pattern = r'\s*(const\s+)?(struct\s+)?[a-zA-Z_]\w*\s+\**\s*([a-zA-Z_][\w\[\]]*)\s*'
        param_list_pattern = r'((' + param_pattern + r',)*' + param_pattern + '|\s*)'
        func_pattern = r'^\s*(static\s+)?((unsigned\s+)?([a-zA-Z_\*]\w*\s+)?\w+)\s*\(' + param_list_pattern + r'\)\s*{([\s\S]*)}'
        self.fun_reg = re.compile(func_pattern, flags=re.MULTILINE)

        var_pattern = r'\s*\*?\s*([a-zA-Z_]\w*)\s*(\[[\w\+\-\*\s]+\]\s*)*(\=[^\,\;]+)?'
        varlist_pattern = r'((' + var_pattern + r',)*' + var_pattern + r')(?=;)'
        vardef_pattern = r'[;\{]\s*((static\s+)?(struct\s+)?[a-zA-Z_]\w*)(\s)' + varlist_pattern
        self.vardef_reg=re.compile(vardef_pattern, flags=re.MULTILINE)

        esql_pattern = r'\s*EXEC\s+SQL\s+[^;]+;'
        self.esql_reg = re.compile(esql_pattern, flags=re.MULTILINE)

        esql_var_pattern = r'[\s\=\(\,]\:\s*([a-zA-Z_]\w*)'
        self.esql_var_reg = re.compile(esql_var_pattern, flags=re.MULTILINE)

        self.param_reg = re.compile(param_pattern, flags=re.MULTILINE)
        formatted_var_pattern = r'^(static\s+)?(struct\s+)?[a-zA-Z_]\w*\s' + var_pattern
        self.formatted_var_reg = re.compile(formatted_var_pattern, flags=re.MULTILINE)

        embeded_vardef_pattern=r'^\s*EXEC\s+SQL\s+BEGIN\s+DECLARE\s+SECTION\s*;\s*'\
                            +'([\s\S]*?)'+ r'EXEC\s+SQL\s+END\s+DECLARE\s+SECTION\s*;'
        self.embeded_vardef_reg= re.compile(embeded_vardef_pattern, flags=re.MULTILINE)


    def processing_folder(self, relative_folder_path):
        if not os.path.exists(os.path.join(self.target_dir, relative_folder_path)):
            os.makedirs(os.path.join(self.target_dir, relative_folder_path))
        folder_path=os.path.join(self.source_dir,relative_folder_path)
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path,file_name)
            if os.path.isfile(file_path):
                self.info('...Processing: '+file_path)
                relative_file_path=os.path.join(relative_folder_path,file_name)
                self.processing_file(relative_file_path)
            elif os.path.isdir(file_path):
                dir_name=os.path.split(file_path)[-1]
                relative_path=os.path.join(relative_folder_path,dir_name)
                self.processing_folder(relative_path)


    def processing_file(self, relative_file_path):
        source_file=os.path.join(self.source_dir,relative_file_path)
        if source_file.endswith('.pc') or source_file.endswith('.c') or source_file.endswith('.h'):
            with open(source_file, 'r',encoding='gbk') as srcfile:
                content=srcfile.read()
                if source_file.endswith('.pc'):
                    content=self.pre_processing_file(content)
                    content=self.esql_rewrite(content)
                    content=content+'\n{//DUMB BLOCK}'
                    content,func_defs=self.rewrite_pcfile_function(content,relative_file_path)
                    content=self.rewrite_file_header(content, func_defs)
                    content=self.replace_last(content,'\n{//DUMB BLOCK}','')
                elif source_file.endswith('.c'):
                    content=self.pre_processing_file(content)
                    func_defs=self.get_function_def(content)
                    content = self.rewrite_file_header(content, func_defs)
                    content = self.modify_cfile_include(content,relative_file_path)
                else:
                    content = self.pre_processing_file(content)
                    content = self.modify_hfile_include(content,relative_file_path)

            target_file=os.path.join(self.target_dir,relative_file_path)
            with open(target_file, 'w',encoding='gbk') as newfile:
                newfile.write(content)


    def rewrite_pcfile_function(self, content, relative_file_path):
        neat_content = re.sub(r'//.*\n', '', content, count=0)
        neat_content = re.sub(r'/\*[\S\s]*?\*/', '', neat_content, count=0)
        all_esql_var_list = self.parse_esql_var_refs(neat_content)
        func_defs=[]
        func_list = re.findall(self.fun_reg, content)
        for func in func_list:
            func_status = func[0] if func[0] else ''
            func_name = func[1]
            param_section = func[4]
            func_params = self.parse_func_params(param_section);

            self.debug("----------%s begin-------------" % func_name)
            self.debug("--Func Param:" )
            for param in func_params:
                self.debug('  '+param)

            result = re.search(r'([\s\S]*?)' + func_status + func_name.replace('*','\*') + r'\s*\([\s\w\*\,\-\[\]]*\)\s*\{', content,
                                   flags=re.MULTILINE)

            prefix_part=result.group(1)
            prefix_part=self.modify_pcfile_include(prefix_part , relative_file_path, all_esql_var_list)
            func_body,remain_part = self.parse_func_body('{' + func[-1] + '}')

            #self.debug('-------prefix:-------')
            #self.debug(prefix_part)
            #self.debug('-------remain:-------')
            #self.debug(remain_part)
            #self.debug('--------end----------')

            neat_func_body = re.sub(r'//.*\n', '', func_body, count=0)
            neat_func_body = re.sub(r'/\*[\S\s]*?\*/', '', neat_func_body, count=0)
            raw_vardef_list,vardef_list = self.parse_local_var_defs(neat_func_body)
            self.debug("--Local variable:" )
            for vardef in vardef_list:
                self.debug('  '+vardef)

            esql_var_list = self.parse_esql_var_refs(neat_func_body)
            self.debug("--ESQL variable:" )
            for execvar in esql_var_list:
                self.debug('  '+execvar)

            declared_embed_var_names=self.parse_declared_embed_var_names(func_body)
            self.debug("--Declared ESQL variable:")
            for var_name in declared_embed_var_names:
                self.debug('  '+var_name)

            new_func_header,exec_declare_section=self.generate_header_and_declare_section(\
                        func_name,func_params,vardef_list,esql_var_list,declared_embed_var_names)

            func_defs.append(func_status+new_func_header)

            if len(esql_var_list) > 0:
                func_body=self.modify_function_body(func_body,esql_var_list,raw_vardef_list,declared_embed_var_names)
                new_func_dec = func_status + new_func_header + '{\n' + exec_declare_section + func_body[1:]
            else:
                new_func_dec = func_status + new_func_header + func_body

            self.debug("----------%s end-------------" % func_name)

            if remain_part:
                remain_funcs,remain_defs=self.rewrite_pcfile_function(remain_part, relative_file_path)
                content = prefix_part + new_func_dec + remain_funcs
                for remain_def in remain_defs:
                    func_defs.append(remain_def)
            else:
                content= prefix_part + new_func_dec

        return content,func_defs

    def rewrite_file_header(self, content, func_defs):
        if len(func_defs)<2:
            return content

        neat_content = re.sub(r'//.*\n', '', content, count=0)
        neat_content = re.sub(r'/\*[\S\s]*?\*/', '', neat_content, count=0)
        neat_content = re.sub(r'\n\s*\n', '\n', neat_content, count=0)

        first_func_def=func_defs[0]
        header_part=content.split(first_func_def)[0]
        neat_header_part=re.sub(r'/\*[\S\s]*?\*/', '', header_part, count=0)
        neat_header_part = re.sub(r'\n\s*\n', '\n' , neat_header_part, count=0)
        neat_header_part = re.sub(r'\n\s*//.*\n', '\n' , neat_header_part, count=0)

        pre_declare=''

        for func_def in func_defs[1:]:
            type_and_name=func_def.split('(')[0]
            func_name = type_and_name.split(' ')[-1]
            if neat_header_part.find(' '+func_name.lstrip('*')+'(')>0:
                continue
            else:
                prev_part=neat_content.split(func_def)[0]
                if re.search(r'[\^\s\*\(\=]'+func_name.lstrip('*')+'\s*\(',prev_part,flags=re.MULTILINE):
                    pre_declare=pre_declare+'/*ESQL*/'+func_def+';\n'

        if pre_declare!='':
            self.debug("--Function must declare first:")
            self.debug(pre_declare)
            result = re.search(r'(.*\n)*(.*)', neat_header_part, flags=re.MULTILINE)
            if result:
                last_line=result.group(1)
                if header_part.find(last_line)>0:
                    new_header_part=self.replace_last(header_part,last_line,last_line+'\n'+pre_declare)
                else:
                    re_last_line=last_line.rstrip('\n').replace('*','\*').replace('.','.').replace('(','\(').replace(')','\)')
                    result=re.search(re_last_line+r'//[^\n]*\n',header_part,flags=re.MULTILINE)
                    if result:
                        last_line=result.group(0)
                        new_header_part = self.replace_last(header_part, last_line, last_line + '\n' + pre_declare)
                    else:
                        result = re.search(re_last_line + r'/\*[\S\s]*?\*/', header_part, flags=re.MULTILINE)
                        if result:
                            last_line = result.group(0)
                            new_header_part = self.replace_last(header_part, last_line, last_line + '\n' + pre_declare)
                        else:
                            last_line=last_line.rstrip('\n')
                            new_header_part = self.replace_last(header_part, last_line, last_line + '\n' + pre_declare)

                content=content.replace(header_part,new_header_part,1)
            else:
                content=content.replace(header_part,header_part+pre_declare+'\n\n',1)

        return content

    def replace_last(self,text,to_replace,replacement):
        start=text.rfind(to_replace)
        if start>-1:
            before_text=text[:start]
            after_text=text[start+len(to_replace):]
            return before_text+replacement+after_text
        else:
            return text


    def get_function_def(self, content):
        func_defs=[]
        func_list = re.findall(self.fun_reg, content)
        for func in func_list:
            func_status = func[0] if func[0] else ''
            func_name = func[1]
            param_section = func[4]

            func_def = func_status + func_name + '(' + param_section + ')'
            func_defs.append(func_def)

            func_body,remain_part = self.parse_func_body('{' + func[-1] + '}')

            if remain_part:
                remain_defs=self.get_function_def(remain_part)
                for remain_def in remain_defs:
                    func_defs.append(remain_def)

        return func_defs

    def parse_func_params(self,param_str):
        func_params = param_str.split(',')
        formatted_params = [];
        for param in func_params:
            formatted_param = param.strip();
            formatted_params.append(formatted_param)
        return formatted_params

    def parse_local_var_defs(self,neat_func_body):
        reserved_words = ['return', 'goto','else']
        raw_vardef_list=[]
        formatted_vardef_list = []
        vardef_list = re.findall(self.vardef_reg, neat_func_body)
        for vardef in vardef_list:
            type = vardef[0]
            if type.lower() not in reserved_words:
                raw_vardef=(vardef[0],vardef[3],vardef[4])
                raw_vardef_list.append(raw_vardef)
                var_list = vardef[4].split(',')
                for var in var_list:
                    formatted_vardef_list.append(type + '\t' + var)
        return raw_vardef_list,formatted_vardef_list

    def parse_esql_var_refs(self, neat_func_body):
        exec_var_list = []
        execsql_list = re.findall(self.esql_reg, neat_func_body)
        for execsql in execsql_list:
            varstr_list = re.findall(self.esql_var_reg, execsql)
            for varstr in varstr_list:
                exec_var_list.append(varstr)

        return list(set(exec_var_list))

    def parse_declared_embed_var_names(self, neat_func_body):
        declared_blocks=re.findall(self.embeded_vardef_reg,neat_func_body)
        declared_var_names=set()
        for def_block in declared_blocks:
            vardef_list=re.findall(self.vardef_reg,'{'+def_block+'}')
            for vardef in vardef_list:
                varname=self.get_variable_name(vardef[3])
                declared_var_names.add(varname)
        return declared_var_names

    def parse_func_body(self, text):
        bracket_stack=[]
        status = 0
        i=0
        for char in text:
            i = i + 1
            if char == '/':
                if status == 0:
                    status = 1
                elif status == 1:
                    status = 2
                elif status == 2:
                    status = 2
                elif status == 3:
                    status = 3
                elif status == 4:
                    status = 0
            elif char == '*':
                if status == 0:
                    status = 0
                elif status == 1:
                    status = 3
                elif status == 2:
                    status = 2
                elif status == 3:
                    status = 4
                elif status == 4:
                    status = 4
            elif char == '\n':
                if status == 0:
                    status = 0
                elif status == 1:
                    status = 0
                elif status == 2:
                    status = 0
                elif status == 3:
                    status = 3
                elif status == 4:
                     status = 3
            else:
                if status == 0:
                     status = 0
                elif status == 1:
                     status = 0
                elif status == 2:
                     status = 2
                elif status == 3:
                     status = 3
                elif status == 4:
                     status = 3

            if status in [2, 3, 4]:
                continue

            if char == '{':
                bracket_stack.append('{')
            else:
                if char == '}':
                    bracket_stack.pop()
                    if len(bracket_stack) == 0:
                        break;

        func_body=text[0:i+1]
        remain_part=text[i+1:]
        return func_body,remain_part

    def generate_header_and_declare_section(self,func_name,func_params,vardef_list,esql_var_list,declared_embed_var_names):
        exec_declare_section = 'EXEC SQL BEGIN DECLARE SECTION;\n'
        exec_param_names = []

        for param in func_params:
            #param_name = re.search(self.param_reg, param).group(2)
            param_name = re.split(r'\s+|\*', param)[-1]
            if param_name in esql_var_list:
                exec_param_names.append(param_name)
                exec_declare_section = exec_declare_section + '\t' + param + "=" + param_name + '_in;\n'

        for vardef in vardef_list:
            var_name = re.search(self.formatted_var_reg, vardef).group(3)
            if var_name in esql_var_list and var_name not in declared_embed_var_names:
                exec_declare_section = exec_declare_section + '\t' + vardef + ";\n"
        exec_declare_section = exec_declare_section + 'EXEC SQL END DECLARE SECTION;\n'

        new_func_header = func_name + '('
        for param in func_params:
            param_name = re.split(r'\s+|\*', param)[-1]
            if param_name in exec_param_names:
                new_func_header = new_func_header + param + '_in,'
            else:
                new_func_header = new_func_header + param + ','

        new_func_header = new_func_header.rstrip(',') + ')'
        return new_func_header,exec_declare_section;

    def modify_function_body(self,func_body,esql_var_list,raw_vardef_list,embeded_var_names):
        extra_ws = re.search(r'^\s*EXEC\s+SQL\s+[\w\s\*\'\-\>\.\,\(\)\=\/]+\:\s+\w',
                             func_body, flags=re.MULTILINE)
        if extra_ws:
            func_body = re.sub(r'\:\s+', ':', func_body, count=0);

        if  len(esql_var_list) > 0:
            to_change_jobs={}
            for raw_vardef in raw_vardef_list:
                var_type=raw_vardef[0]
                var_literal_list=raw_vardef[2].split(',')
                varname_list=[]
                to_change_item=[]
                for count in range(len(var_literal_list)):
                    var_literal=var_literal_list[count]
                    var_name=self.get_variable_name(var_literal)
                    varname_list.append(var_name)
                    if var_name in esql_var_list and var_name not in embeded_var_names:
                        to_change_item.append(count)

                if len(to_change_item)==0:
                    continue

                original_text=raw_vardef[0]+raw_vardef[1]+raw_vardef[2]+';'
                if len(varname_list)==len(to_change_item):
                    to_change_jobs[original_text]='/*ESQL* '+original_text+'*/'
                else:
                    dest_literial='/*ESQL* '+original_text+'*/'+var_type+'\t';
                    for i in range(len(var_literal_list)):
                        if i not in to_change_item:
                            dest_literial=dest_literial+var_literal_list[i]+','
                    dest_literial = dest_literial.rstrip(',')+';'
                    to_change_jobs[original_text]=dest_literial
            self.debug('--Def Changed:')
            for key,value in to_change_jobs.items():
                func_body=func_body.replace(key,value,1)
                self.debug('  '+key+'--->'+value)

        return func_body

    def get_variable_name(self,var_literal):
        name=re.split(r'\[|=', var_literal)[0].strip().lstrip('*')
        return name


    def modify_pcfile_include(self, header, relative_file_path , all_esql_var_list):
        rewrite_include=self.config['sql_include']['rewrite']
        if not rewrite_include or not header or len(header)<10:
            return header

        header = re.sub(r'EXEC\s+SQL\s+INCLUDE\s+SQLCA', 'EXEC SQL INCLUDE sqlca', header, count=1);
        header = re.sub(r'#include\s+<sqlca\.h>', 'EXEC SQL INCLUDE sqlca;', header, count=1);
        header = re.sub(r'EXEC\s+SQL\s+INCLUDE\s+oraca\s*\;\s*\n', '', header, count=1);
        header = re.sub(r'#include\s+<sys/ldr\.h>\s*\n', '', header, count=1);
        header = re.sub(r'#include\s+<sys/access\.h>\s*\n', '', header, count=1);
        header = re.sub(r'#include\s+<oraca\.h>\s*\n', '', header, count=1);
        header = re.sub(r'#include\s+<oci\.h>\s*\n', '', header, count=1);

        pc_dirs=re.split(r'/|\\',relative_file_path.lstrip('./').lstrip('.\\'))[:-1]
        h_files=self.config['sql_include']['header_files']

        for h_file in h_files:
            h_dirs=h_file.split('/')[:-1]
            level=0
            rel_h_path = ''
            for pc_dir in pc_dirs:
                if level >= len(h_dirs):
                    break
                if  pc_dir==h_dirs[level]:
                    level = level + 1
                    continue;
                else:
                    for i in range(level,len(pc_dirs)):
                        rel_h_path=rel_h_path+'../'
                    break
                level=level+1

            for i in range(level, len(h_dirs)):
                rel_h_path = rel_h_path + h_dirs[i] + '/'
            rel_h_path = rel_h_path + h_file.split('/')[-1]

            re_file=r'#include\s+"'+rel_h_path.replace('.','\.')+'"'
            header = re.sub(re_file,'EXEC SQL INCLUDE "'+rel_h_path+'";',header,count=1)

            rel_h_path = './' + rel_h_path
            re_file=r'#include\s+"'+rel_h_path.replace('.','\.')+'"'
            header = re.sub(re_file,'EXEC SQL INCLUDE "'+rel_h_path+'";',header,count=1)

        multi_line_pattern = r'^\s*(#define\s+)(\w+\s(.*?\\\n)+.+)'
        multi_line_list = re.findall(multi_line_pattern, header, flags=re.MULTILINE)
        for multi_line_define in multi_line_list:
            old_define = multi_line_define[0] + multi_line_define[1]
            new_define = 'EXEC SQL DEFINE ' + multi_line_define[1] + ';'
            header = header.replace(old_define, new_define)

        neat_header = header;
        declared_pattern = r'^(\s*EXEC\s+SQL\s+BEGIN\s+DECLARE\s+SECTION;[\s\S]*?EXEC\s+SQL\s+END\s+DECLARE\s+SECTION;)'
        declared_area_list = re.findall(declared_pattern, header, flags=re.MULTILINE)
        for declare_area in declared_area_list:
            neat_header = neat_header.replace(declare_area, '')

        typedef_pattern = r'^\s*(typedef\s+struct\s*\{[\s\S]*?\}.*?;)'
        typedef_list = re.findall(typedef_pattern, neat_header, flags=re.MULTILINE)
        for typedef_define in typedef_list:
            old_define = typedef_define
            new_define = 'EXEC SQL BEGIN DECLARE SECTION;\n' + typedef_define + '\nEXEC SQL END DECLARE SECTION;'
            header = header.replace(old_define, new_define)

        struct_pattern = r'^\s*(struct\s*\w*\s*{[\s\S]*?\}.*?;)'
        struct_list = re.findall(struct_pattern, neat_header, flags=re.MULTILINE)
        self.debug('--Struct need to be SQL DECLARED:')
        for struct_def in struct_list:
            old_define = struct_def
            self.debug(old_define)
            new_define = 'EXEC SQL BEGIN DECLARE SECTION;\n' + struct_def + '\nEXEC SQL END DECLARE SECTION;'
            header = header.replace(old_define, new_define)

        neat_header = header
        neat_header=re.sub(declared_pattern,'',neat_header, flags=re.MULTILINE)
        neat_header=re.sub(r'#.+','',neat_header, flags=re.MULTILINE)

        global_vardef_list = re.findall(self.vardef_reg, '{'+neat_header+'}')
        for vardef in global_vardef_list:
            original_text = vardef[0] + vardef[3] + vardef[4]
            var_list = vardef[4].split(',')
            for var_literal in var_list:
                var_name = self.get_variable_name(var_literal)
                if var_name in all_esql_var_list:
                    new_text = 'EXEC SQL BEGIN DECLARE SECTION;\n' + original_text + ';\nEXEC SQL END DECLARE SECTION'
                    header = header.replace(original_text, new_text)
                    break

        combinable_stmts_pattern = r'^(\s*EXEC\s+SQL\s+END\s+DECLARE\s+SECTION;\s*EXEC\s+SQL\s+BEGIN\s+DECLARE\s+SECTION;)'
        combinable_stmts_list = re.findall(combinable_stmts_pattern, header, flags=re.MULTILINE)
        for combinable_stmts in combinable_stmts_list:
            header = header.replace(combinable_stmts, '\n')

        return header;


    def modify_cfile_include(self, content , relative_file_path):
        if not self.config['sql_include']['rewrite']:
            return content
        content = re.sub(r'#include\s+<sys/ldr\.h>\s*\n', '', content,count=1);
        content = re.sub(r'#include\s+<sys/access\.h>\s*\n', '', content,count=1);
        content = re.sub(r'#include\s+<oraca\.h>\s*\n', '', content,count=1);
        if not re.search(r'#define\s+__INCLUDE_IN_C__',content,flags=re.MULTILINE):

            pc_dirs = re.split(r'/|\\', relative_file_path.lstrip('./').lstrip('.\\'))[:-1]
            h_files = self.config['sql_include']['header_files']

            for h_file in h_files:
                h_dirs = h_file.split('/')[:-1]
                level = 0
                rel_h_path = ''
                for pc_dir in pc_dirs:
                    if level >= len(h_dirs):
                        break
                    if pc_dir == h_dirs[level]:
                        level = level + 1
                        continue;
                    else:
                        for i in range(level, len(pc_dirs)):
                            rel_h_path = rel_h_path + '../'
                        break
                    level = level + 1

                for i in range(level, len(h_dirs)):
                    rel_h_path = rel_h_path + h_dirs[i]+'/'
                rel_h_path = rel_h_path + h_file.split('/')[-1]
                re_file = r'#include\s+"' + rel_h_path.replace('.', '\.') + '"'
                content = re.sub(re_file, '#define __INCLUDE_IN_C__ TRUE\n#include "' + rel_h_path + '"', content, count=1)

        return content

    def modify_hfile_include(self, content, relative_file_path):
        if self.config['sql_include']['rewrite']:
            content = re.sub(r'#include\s+<sys/ldr\.h>\s*\n', '', content);
            content = re.sub(r'#include\s+<sys/access\.h>\s*\n', '', content);
            content = re.sub(r'#include\s+<oraca\.h>\s*\n', '', content);
            content = re.sub(r'#include\s+<oci\.h>\s*\n', '', content);

            pc_dirs = re.split(r'/|\\', relative_file_path.lstrip('./').lstrip('.\\'))[:-1]
            h_files = self.config['sql_include']['header_files']

            for h_file in h_files:
                h_dirs = h_file.split('/')[:-1]
                level = 0
                rel_h_path = ''
                for pc_dir in pc_dirs:
                    if level >= len(h_dirs):
                        break
                    if pc_dir == h_dirs[level]:
                        level = level + 1
                        continue;
                    else:
                        for i in range(level, len(pc_dirs)):
                            rel_h_path = rel_h_path + '../'
                        break
                    level = level + 1

                for i in range(level, len(h_dirs)):
                    rel_h_path = rel_h_path + h_dirs[i] + '/'
                rel_h_path = rel_h_path + h_file.split('/')[-1]

                re_file = r'#include\s+"' + rel_h_path.replace('.', '\.') + '"'
                replace_text= '#ifndef __INCLUDE_IN_C__\nEXEC SQL INCLUDE "%s";\n#else\n#include "%s"\n#endif\n' % (rel_h_path, rel_h_path)
                content = re.sub(re_file, replace_text, content, count=1)

                rel_h_path = './' + rel_h_path
                re_file = r'#include\s+"' + rel_h_path.replace('.', '\.') + '"'
                replace_text = '#ifndef __INCLUDE_IN_C__\nEXEC SQL INCLUDE "%s";\n#else\n#include "%s"\n#endif\n' % (rel_h_path, rel_h_path)
                content = re.sub(re_file, replace_text, content, count=1)

            to_convert_hfiles=self.config['sql_include']['header_files']
            formatted_path =  relative_file_path.lstrip('./').lstrip('.\\').replace('\\','/')
            if formatted_path in to_convert_hfiles:
                typedef_pattern = r'^\s*(typedef\s+struct\s*\w*\s*\{[\s\S]*?\}.*?;)'
                typedef_list = re.findall(typedef_pattern, content, flags=re.MULTILINE)
                for typedef_define in typedef_list:
                    old_define = typedef_define
                    new_define = '#ifndef __INCLUDE_IN_C__\nEXEC SQL BEGIN DECLARE SECTION;\n#endif\n' + typedef_define + '\n#ifndef __INCLUDE_IN_C__\nEXEC SQL END DECLARE SECTION;\n#endif'
                    content = content.replace(old_define, new_define)

                checking_pattern = r'^(#ifndef __INCLUDE_IN_C__\nEXEC SQL END DECLARE SECTION;\n#endif)([\S\s]*?)(#ifndef __INCLUDE_IN_C__\nEXEC SQL BEGIN DECLARE SECTION;\n#endif)'
                area_list = re.findall(checking_pattern, content, flags=re.MULTILINE)
                for area in area_list:
                    orginal_text=area[0]+area[1]+area[2]
                    keep_text=area[1]
                    content = content.replace(orginal_text, keep_text)

        return content

    def pre_processing_file(self, content):
        block_list = re.findall(r'#if(\s+)([01]|[\w]+)([\S\s]*?)#endif', content)
        for block in block_list:
            if re.search(r'#if', block[2], flags=re.MULTILINE):
                self.info("#if/#endif 嵌套，需要手工处理")
                return content

        for block in block_list:
            space=block[0]
            condition=block[1]
            block_text=block[2]
            else_case = re.search(r'([\S\s]*?)#else([\S\s]*?)',block_text,flags=re.MULTILINE)
            if not else_case:
                if condition=='1':
                    content = content.replace('#if' +space+condition+block_text + '#endif', block_text)
                else:
                    content = content.replace('#if' + space + condition + block_text + '#endif','')
            else:
                if_part=else_case[0]
                else_part=else_case[1]
                if condition == '1':
                    content = content.replace('#if' + space + condition + block_text + '#endif', if_part)
                else:
                    content = content.replace('#if' + space + condition + block_text + '#endif', else_part)

        remark_list = re.findall(r'(/\*[\s\S]*?\*/)', content, flags=re.MULTILINE);
        pre_remark=None
        for current_remark in remark_list:
            if pre_remark:
                orginal_text=pre_remark+current_remark
                if content.find(orginal_text)>=0:
                    new_text=pre_remark[:-2]+current_remark[2:]
                    content=content.replace(orginal_text,new_text)
            pre_remark = current_remark

        content = re.sub(r'\=\s*\'\'', '= 0 /*ESQL*/', content, count=0);
        stat_ref=re.search(r'struct\s+stat',content,flags=re.MULTILINE)
        if stat_ref:
            if not re.search(r'#include\s+<sys/stat\.h>',content,flags=re.MULTILINE):
                content = re.sub(r'#include\s+<stdio\.h>',
                                 '#include <stdio.h>\n#include <sys/stat.h>', content, count=1)

        if content.find('strerror(')>=0:
            if not re.search(r'#include\s+<string\.h>',content,flags=re.MULTILINE):
                content = re.sub(r'#include\s+<errno\.h>',
                                 '#include <errno.h>\n#include <string.h>', content, count=1)

        formatable_inc_list=re.findall(r'(#include\s+"\./)([\w\-\/]+\.h)"', content, flags=re.MULTILINE)
        for formatable_inc in formatable_inc_list:
            orginal_text=formatable_inc[0]+formatable_inc[1]+'"'
            new_text='#include "'+formatable_inc[1]+'"'
            content = content.replace(orginal_text, new_text)

        unusual_pattern = r'(\([\w\s\*\,]*(const\s+)?(struct\s+)?[a-zA-Z_]\w*\*+)(\s+[a-zA-Z_][\w\[\]]*[\w\s\*\,]*\))'
        unusual_param_list = re.findall(unusual_pattern, content, flags=re.MULTILINE)
        for unusual_param in unusual_param_list:
            orginal_text = unusual_param[0] + unusual_param[3]
            if orginal_text.find('** ')>-1:
                new_text = re.sub(r'\*\*\s+', ' **', orginal_text, count=0)
                new_text = re.sub(r'\*\s+', ' *', new_text, count=0)
            else:
                new_text = re.sub(r'\*\s+', ' *', orginal_text, count=0)
            content = content.replace(orginal_text, new_text)

        param_pattern = r'\s*(const\s+)?(struct\s+)?[a-zA-Z_]\w*\s+\*?\s*([a-zA-Z_][\w\[\]]*)\s*'
        old_style_func_list = re.findall(r'([a-zA-Z_]\w+\s*)\(((\s*\w+\s*,)*.\s*\w+\s*)\)(('
                                         + param_pattern + r';)+\s*)\{', content, flags=re.MULTILINE)
        for func in old_style_func_list:
            orginal_text = func[0] + '(' + func[1] + ')' + func[3] + '{'
            new_text = func[0] + '('
            arg_list = func[1].split(',')
            arg_def_list = func[3].split(';')[:-1]
            if len(arg_list) == len(arg_def_list):
                for arg in arg_list:
                    arg1 = arg.strip(' ')
                    for arg_def in arg_def_list:
                        arg2 = re.split(r'[\s|\*]',arg_def.strip().strip('[]').strip())[-1]
                        if arg1 == arg2:
                            new_text = new_text + arg_def.strip() + ','
                            break;
                new_text = new_text.rstrip(',') + '){'
                content = content.replace(orginal_text, new_text)

        abnormal_esql_list = re.findall(r'(exec\s+sql[\s\S]+?;)', content, flags=re.MULTILINE)
        for abnormal_esql in abnormal_esql_list:
            normal_esql=re.sub(r'exec\s+sql','EXEC SQL',abnormal_esql,count=1)
            content=content.replace(abnormal_esql,normal_esql)

        return content

    def esql_rewrite(self, content):
        esql_list = re.findall(r'(EXEC\s+SQL[\s\S]+?;)', content, flags=re.MULTILINE)
        for esql in esql_list:
            remark_stmts = re.findall(r'//(.*?)$', esql, flags=re.MULTILINE | re.DOTALL)
            new_esql = esql
            for remark_text in remark_stmts:
                if re.search(r'/\*(.*?)\*/', remark_text) or remark_text.find('*/') < 0:
                    new_esql = new_esql.replace('//' + remark_text, '')
            new_esql = re.sub(r'\n\s*\n', '\n', new_esql, count=0)
            new_esql = re.sub(r'\n\s*$', '', new_esql, count=0)
            content = content.replace(esql, new_esql)

        esql_list = re.findall(r'(EXEC\s+SQL[\s\S]+?;)', content, flags=re.MULTILINE)
        for esql in esql_list:
            new_esql = re.sub(r'\s*from\s*dual', ' ', esql, re.MULTILINE)
            new_esql = re.sub(r'\s*FROM\s*DUAL', ' ', esql, re.MULTILINE)
            new_esql = re.sub(r'into:', 'into :', new_esql, re.MULTILINE)
            new_esql = re.sub(r'INTO:', 'INTO :', new_esql, re.MULTILINE)
            content = content.replace(esql, new_esql)

        del_esql_list = re.findall(r'(EXEC\s+SQL\s+(delete|DELETE)\s+(\w+)([\s\S]+?);)', content, flags=re.MULTILINE)
        for del_esql in del_esql_list:
            key_word = del_esql[2]
            if key_word not in ['from', 'FROM']:
                orginal_esql = del_esql[0]
                new_esql = 'EXEC SQL DELETE FROM '+del_esql[2]+del_esql[3]+';'
                content = content.replace(orginal_esql, new_esql)

        return content

    def debug(self, info):
        self.logger.debug(info)

    def info(self, info):
        self.logger.info(info)

def main(argv):
    converter = FileConverter()
    #converter.processing_file("incl\\tran_gdpy_mq.h")
    converter.processing_folder(".")

if __name__ == "__main__":
     main(sys.argv[1:])