import string
import sys
import random
import socket
import pickle
import frames as frames
import time
from datetime import datetime
from dataclasses import dataclass
import threading

start_time = time.perf_counter()
# print(start_time)

@dataclass
class packet_header:
    bmx_version: int
    reserved: int
    pkt_len: int
    transmittedIID: int
    link_adv_sqn: int
    pkt_sqn: int
    local_id: int
    dev_idx: int

@dataclass
class packet:
    header: packet_header
    frames: list

#sending packets
def sendpacket(ip, port, msg):
    #creates socket
    s = socket.socket(socket.AF_INET, #itnernet
                                socket.SOCK_DGRAM) #udp
    bmsg = pickle.dumps(msg) #converts the data into bytes
    s.sendto(bmsg, (ip, port)) #sends the message
    print(bmsg)


#receiving packets
def recvpacket(ip, port):
    #creates socket
    s = socket.socket(socket.AF_INET, #itnernet
                                socket.SOCK_DGRAM) #udp
    
    s.bind((ip,port))

    #while True:
    bdata, addr = s.recvfrom(1024) #receives the data 

    data = pickle.loads(bdata) #converts the data from bytes

    print(f"Received {data} from {addr}") #print(data)

    return data

#adding request frames to frames 2 send list alongside with the unsolicited adv frames
def send_REQ_frame(REQ_frame, frames2send):
    #if we wish to send LINK_REQ, it will append LINK_REQ and LINK_ADV to frames2send list 
    #same with other REQ frames
    if REQ_frame == frames.LINK_REQ: 
        frames2send.extend([REQ_frame, frames.LINK_ADV])

    if REQ_frame == frames.HASH_REQ:
        frames2send.extend([REQ_frame, frames.HASH_ADV])

    if REQ_frame == frames.DESC_REQ:
        frames2send.extend([REQ_frame, frames.DESC_ADV])

    if REQ_frame == frames.DEV_REQ:
        frames2send.extend([REQ_frame, frames.DEV_ADV])

#checks if the received packet has req frames, then add appropriate adv frames
#to the frames to send list
def send_ADV_frames(recvd_frames, frames2send):
    for i in recvd_frames: ##iterate through the list of frames received to 
                            # check if there is any REQ frame. add appropriate ADV frame to frames list 
                            # if there is any REQ frame
        #if there is DESC_REQ in received frame list, it will append DESC_ADV to frames2send list
        #same with others
        if i == frames.DESC_REQ:
            frames2send.append(frames.DESC_ADV)

        if i == frames.LINK_REQ:
            frames2send.append(frames.LINK_ADV)

        if i == frames.HASH_REQ:
            frames2send.append(frames.HASH_ADV)

        if i == frames.DEV_REQ:
            frames2send.append(frames.DEV_ADV)
        

        
        
#just test port values
port = 8080
ip = socket.gethostbyname(socket.gethostname())





transient_state = True
knowsAllNodes = False
pktSqn = random.randint(0,4294967295//2) #since packet sequence start at random 

while True:
    frames2send = [frames.HELLO_ADV, frames.RP_ADV] #periodic messages to be  
                                                    #sent together with the packets
    
    threading.Thread(target = recvpacket(ip, port)).start() #receiving packets

    #if in transient state
    while transient_state:
        recvd = recvpacket(ip, port) #stores the received packet to recvd variable

        #if it knows every nodes, enter steady state
        if knowsAllNodes:
            transient_state = False

        #else append non periodic frames
        else:
            recvd_frames = recvd.frames #store packet frames list to recevd_frames
            
            send_ADV_frames(recvd_frames, frames2send) 

            knowsAllNodes = True #then knows every node

    pktSqn += 1 #increment sqn number every sending of packets

    #creating packets
    msg = packet(packet_header(3,4,5,6,7,pktSqn, 9, 0), frames2send) #some of the integers are test values
    print(msg)
    time.sleep(0.5) #Hello and Rp sent every 0.5s
    print(datetime.now().time()) #show current time

    sendpacket(ip, port, msg) #sending packets

