#!/usr/bin/python


from socket import *
from select import select
from sys import stdin,argv
import re


def sendMsg(msg,nwNicknames,nwSocks,banList):
    m=re.match("^(QUIT|PM \w+ \w+|BM \w+|BAN \w+|UNBAN \w+|BANLIST)",msg,re.IGNORECASE)
    if m :
        #the message is correct, proceeding.
        mType=msg[:2].lower()
        if mType=="pm":
            msgVals=msg.split(" ")
            pmName=msgVals[1]
            if pmName in banList:
                print pmName+" is banned!"
                return True
            pmMsg=" ".join(msgVals[2:])
            pmIp=nwNicknames[pmName]
            for c in nwSocks:
                if c.getpeername()[0]==pmIp:
                    msgToSend="4"+ID+"\001"+"PM#"+nickname+"#"+pmMsg
                    msgU=msgToSend.encode("utf-8")
                    c.send(msgU)
        elif mType=="bm":
            msgToSend="5"+ID+"\001"+"BM#"+nickname+"#"+msg[3:]
            msgToSend=msgToSend.encode("utf-8")
            for name in nwNicknames:
                if not name in banList:
                    for c in nwSocks:
                        if c.getpeername()[0]==nwNicknames[name]:
                            c.send(msgToSend)
        elif mType=="ba":
            if not msg[4:] in nwNicknames.keys():
                return True
            banToSend=msg.encode("utf-8")
            banList.append(msg[4:])
            for c in nwSocks: #indicating the ban to the network
                c.send(banToSend)
        elif mType=="un":
            if not msg[6:] in banList:
                return True
            unbanToSend=msg.encode("utf-8")
            for c in nwSocks: #indicating the unban to the network
                c.send(unbanToSend.encode("utf-8"))
            banList.remove(msg[6:])
        elif mType=="qu": #quitting
            print("Quitting... ")
            for c in nwSocks:
                c.close()
            s.close()
            quit(0)

        return True
    else:
        return False

if len(argv)>2:
    print("Usage: ./chatptp.py [ip]")
    exit(1)


ID="115"
print("Introduce yourself: ")
nickname=stdin.readline().strip("\n")

#server side
s=socket()
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
s.bind(('0.0.0.0', 1664))
s.listen(150)
#print "Listening on port 1664"


nwSocks=[]
nwNicknames={}
banList=[]


#trying to connect to the ip that was passed in agrument
if len(argv)==2:
    #verifying ip fomat
    addr=argv[1]
    ipMatch=re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",addr,re.IGNORECASE)
    if not ipMatch:
        print "Wrong ip format!"
        exit(1)
    c=socket()
    c.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    c.connect((addr,1664))
    nwSocks.append(c)
    #starting the communication with newly created socked
    c.send(("1"+ID+"\001"+"START#"+nickname).encode("utf-8"))
    hResp=c.recv(1024).decode("utf-8")
    hRespFormated=hResp.split("\001")
    print(hRespFormated[0]+" "+hRespFormated[1])

    nwNicknames[hResp.split("#")[1]]=addr
    #exploring existing network sent by the adress that we are connecting to
    ips_list=c.recv(1024).decode('utf-8')
    addrs_ip=ips_list.split("#")[1].strip("()").strip().split(",")
    if len(addrs_ip[0]) >1:
        for ipaddr in addrs_ip: #connecting to each existing host
            ec=socket()
            ec.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
            ec.connect((ipaddr,1664))
            nwSocks.append(ec)
            ec.send(("2"+ID+"\001"+"HELLO#"+nickname).encode("utf-8"))
            respEc=ec.recv(1024).decode("utf-8")
            nwNicknames[respEc.split("#")[1]]=ipaddr
            respFormated=respEc.split("\001")
            print(respFormated[0]+" "+respFormated[1])

socks=[s,stdin]+nwSocks

data=""
while True:
    #print "current network :" + "("+",".join(x.getpeername()[0] for x in nwSocks)+")"
    #print "current nicknames base:"+str(nwNicknames)
    if data == "exit":
        break
    lin, lout, lex=select(socks, [], []) 
    #print "select got %d read events" % (len(lin))
    for t in lin:
        if t==stdin:
            if nickname in banList:
                print "You're banned dude"
                buff=stdin.readline().strip("\n")
                break
            msg=stdin.readline().strip("\n")
            if not sendMsg(msg,nwNicknames,nwSocks,banList):
                print("Give correct msg ")
        elif t==s: #someone is connecting
            (c, addr)=s.accept()
            data=c.recv(1024).decode("utf-8")
            firstData=data.split("\001")
            nwNicknames[firstData[1].split("#")[1]]=addr[0]
            dataFormated=data.split("\001")

            print(dataFormated[0]+" "+dataFormated[1])
            if firstData[0]=="1"+ID:
                c.send(("2"+ID+"\001"+"HELLO#"+nickname).encode("utf-8"))
                #sending the list of current ips in the network
                ipsList="3"+ID+"\001"+"IPS#("+",".join(x.getpeername()[0] for x in nwSocks)+")"
                #print "sending Ips: " +ipsList
                c.send(ipsList.encode('utf-8'))
            else:
                #newly connected host already got the network ips, just greeting back.
                c.send(("2"+ID+"\001"+"HELLO#"+nickname).encode("utf-8"))

            #updating current network list if not already present
            if not any(c.getpeername()[0] in x.getpeername()[0] for x in nwSocks):#if address in not already in the network
                nwSocks.append(c)
                #updating list of socks to which the host is connected
                socks.append(c)
            

        else:
            #Someone is talking

            who=t.getpeername()[0]
            data=t.recv(1024)
            msgDecoded=data.decode("utf-8")
            if data:
                #unbanning someone
                if msgDecoded[:5]=="unban":
                    if not msgDecoded[6:] in banList:
                        break
                    if msgDecoded[6:]==nickname:
                        print "You have been unbanned."
                    else:
                        print msgDecoded[6:]+" has been unbanned."
                    banList.remove(msgDecoded[6:])
                    break
                #banning someone
                if msgDecoded[:3]=="ban":
                    if not msgDecoded[4:] in banList:
                        banList.append(msgDecoded[4:])
                        if msgDecoded[4:]==nickname:
                            print "You have been banned."
                        else:
                            print msgDecoded[4:]+" has been banned."
                        break
                if nickname in banList: #we are banned, passing on incoming message.
                    break

                #printing the message
                msgFormated=msgDecoded.split("\001")
                print(msgFormated[0]+" "+msgFormated[1])
            else:
                #he disconnected
                socks.remove(t)
                nwSocks.remove(t)
                nameToRemove=""
                for names in nwNicknames:
                    if nwNicknames[names]==who:
                        nameToRemove=names
                del nwNicknames[nameToRemove]
                print "Goodbye %s!\n" % (nameToRemove,) 
       
      
        
