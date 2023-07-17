import socket

def main():
    obj = socket.socket()

    obj.connect(("192.168.202.133",1024))

    while True:
        inp = input("请输入 \n >>>")
        if inp == "q":
            obj.sendall(bytes(inp,encoding="utf-8"))
            break
        else:
            obj.sendall(bytes(inp, encoding="utf-8"))
            ret_bytes = obj.recv(1024)
            ret_str = str(ret_bytes,encoding="utf-8")
            print(ret_str)

if __name__=='__main__':
    main()
    
