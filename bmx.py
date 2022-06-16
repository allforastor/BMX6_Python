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

#receive packet
def listen(group, port):
	# Look up multicast group address in name server 
	addrinfo = socket.getaddrinfo(group, None)[0]
    
	# Create a socket
	s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

	# Allow multiple copies of this program on one machine
	# (not strictly needed)
	#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# Bind it to the port
	s.bind(('', port))

	group_bin = socket.inet_pton(socket.AF_INET6, addrinfo[4][0])
	mreq = group_bin + struct.pack('@I', 0)
	s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

	data, sender = s.recvfrom(1500)
	while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
	data = pickle.loads(data)
	print (str(sender) + '  ' + repr(data))	

#send packet
def send(group, port, ttl, msg):
	addrinfo = socket.getaddrinfo(group, None)[0]

	s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

	# Set Time-to-live (optional)
	ttl_bin = struct.pack('@i', ttl)
	s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
#	data = repr(time.time())
	msg = pickle.dumps(msg)
	s.sendto(msg + b'\0', (addrinfo[4][0], port))
#	time.sleep(1)

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
group = 'ff02::2'
ttl = 1




transient_state = True
knowsAllNodes = False
pktSqn = random.randint(0,4294967295//2) #since packet sequence start at random 

while True:
    frames2send = [frames.HELLO_ADV, frames.RP_ADV] #periodic messages to be  
                                                    #sent together with the packets
    
    threading.Thread(target = listen(group, port)).start() #receiving packets

    #if in transient state
    while transient_state:
        recvd = listen(group, port) #stores the received packet to recvd variable

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

    send(group, port, ttl, msg) #sending packets

