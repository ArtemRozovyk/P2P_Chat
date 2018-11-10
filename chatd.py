#!/usr/bin/python


from socket import *
from select import select
from sys import stdin,argv




if len(argv)>2:
    print("Usage: ./chatptp.py [ip]")
    exit(1)

print("Introduce yourself: ")
nickname=stdin.readline().strip("\n")

#server side
s=socket()
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
s.bind(('0.0.0.0', 1664))
s.listen(150)
print "Listening on port 1664"

#trying to connect to the ip that was passed in agrument
nwSocks=[]
if len(argv)==2:
    addr=argv[1]
    c=socket()
    c.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    c.connect((addr,1664))
    nwSocks.append(c)
    #starting the communication with newly created socked
    c.send("START#"+nickname)
    hResp=c.recv(1024)
    print(hResp)

    #exploring existing network sent by 'c'
    ips_list=c.recv(1024).decode('utf-8')
    addrs_ip=ips_list.split("#")[1].strip("()").strip().split(",")
    if len(addrs_ip[0]) >1:
        for ipaddr in addrs_ip: #connecting to each existing host
            ec=socket()
            ec.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
            ec.connect((ipaddr,1664))
            nwSocks.append(ec)
            ec.send("HELLO#"+nickname)
            respEc=ec.recv(1024)
            print(respEc)

socks=[s,stdin]+nwSocks

data=""
while True:
    print "current network :" + "("+",".join(x.getpeername()[0] for x in nwSocks)+")"

    if data == "exit":
        break
    lin, lout, lex=select(socks, [], []) 
    print "select got %d read events" % (len(lin))
    for t in lin:
        if t==stdin:
            print "Speak:"
            msg=stdin.readline().strip("\n")
            print ("entree clavier : %s" % msg )
        elif t==s: #someone is connecting
            print "Someone is connecting" 
            (c, addr)=s.accept()
            data=c.recv(1024)
            print(data)
            if data[:5]=="START":
                c.send("HELLO#"+nickname)
                #sending the list of current ips in the network
                ipsList="3000"+"\001"+"IPS#("+",".join(x.getpeername()[0] for x in nwSocks)+")"
                print "sending Ips: " +ipsList
                c.send(ipsList.encode('utf-8'))
            else:
                #newly connected host already got the network ips, just greeting back.
                c.send("HELLO#"+nickname)

            #updating current network list if not already present
            if not any(c.getpeername()[0] in x.getpeername()[0] for x in nwSocks):#if address in not already in the network
                nwSocks.append(c)
                #updating list of socks to which the host is connected
                socks.append(c)
            

        else: 
        #Someone is talking
            who=t.getpeername()[0]
            print ("%s is gona do smth...") % (who,)
            data=t.recv(1024)
            if data:
                #he's saying something
                print(data)
            else:
                #he disconnected
                socks.remove(t)
                nwSocks.remove(t)
                print "Goodbye %s!\n" % (who,) 
       
      
        
