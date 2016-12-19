from time import ctime


def thread_handler(client_sock, addr):
    print "...connected from ", addr
    while True:
        recv_data = client_sock.recv(BUFSIZE)
        cmd =recv_data.split(":")[0]

        if not recv_data:
            break

        if cmd == "/REQCLOSE":
            print "%s is gone" % addr[0]
            client_sock.close()

        if cmd == "/SENDFILE":
            file_transfer_handler(client_sock, )

        print "[%s][%s] %s" % (ctime(), addr[0], recv_data)

        client_sock.send("[%s] I got message that \'%s\'" % (ctime(), recv_data))
    client_sock.close()


def file_transfer_handler(client_sock, addr):
    pass
