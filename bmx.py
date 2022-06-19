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
	
	return data
	#data = pickle.loads(data)
	#print (str(sender) + '  ' + repr(data))	

def send(group, port, ttl, msg):
	addrinfo = socket.getaddrinfo(group, None)[0]

	s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

	# Set Time-to-live (optional)
	ttl_bin = struct.pack('@i', ttl)
	s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
#	data = repr(time.time())
#	msg = pickle.dumps(msg)
	s.sendto(msg + b'\0', (addrinfo[4][0], port))
#	time.sleep(1)



def create_packet(packetheader, frameslist):
	frames_bytes = b''

	for i in frameslist:
		if type(i) == frames.HELLO_ADV:
			#print("I am hello adv")
			frames_bytes += HELLO_ADV_to_bytes(i)

		elif type(i) == frames.RP_ADV:
			frames_bytes+= RP_ADV_to_bytes(i)

		elif type(i) == frames.LINK_REQ:
			frames_bytes += LINK_REQ_to_bytes(i)

		elif type(i) == frames.LINK_ADV:
			frames_bytes += LINK_ADV_to_bytes(i)

	len_of_all_frames = len(frames_bytes)

	packetheader.pkt_len = len_of_all_frames + 17

	packetheader = struct.pack("!BBHHHIIB", packetheader.bmx_version, packetheader.reserved, 
					packetheader.pkt_len, packetheader.transmitterIID, packetheader.link_adv_sqn, 
					packetheader.pkt_sqn, packetheader.local_id, packetheader.dev_idx)

	created_packet = packetheader + frames_bytes

	return created_packet

def dissect_packet(recvd_packet):
	curr_pos = 17 #current position of the bytes
	packetheader = recvd_packet[:x]
	packetheader_raw = struct.unpack("!BBHHHIIB", packetheader)
	packetheader = packet_header(packetheader_raw[0], packetheader_raw[1], packetheader_raw[2], 
								packetheader_raw[3], packetheader_raw[4], packetheader_raw[5], 
								packetheader_raw[6], packetheader_raw[7])

	frameslist = [] #initializes the list of frames recvd
	
	# this while loop iterate through the frames part of the receivd packet
	# curr_pos is the current position of the bytes. while curr_pos is not equal to the packet length(meaning end of the packet)
	# continuosly iterate through the remaing part of the packet
	while x != packetheader.pkt_len:
		# extract first the frame header and check the frame type of the frame under that frame header
		# if frametype is 1 = hello_adv, 2 = rp_adv, 3 = link_req, 4 = link_adv
		frameheader_unkown = recvd_packet[x:x+2]# +2 since frame header length is 2 bytes
		frameheader_unkown = dissect_frame_header(frameheader_unkown)
		
		if frameheader_unkown.frm_type == 1: #if frame type is 1, then it is a hello_adv
			hello_adv_frame = recvd_packet[x:x + frameheader_unkown.frm_len] # extract the part of the packet from the curr_pos up to the length of the frame 
			hello_adv_frame = dissect_HELLO_ADV(hello_adv_frame) # dissects the HELLO_frame
			frameslist.append(hello_adv_frame) # append the dissected HELLO_frame to the frames list
			x += hello_adv_frame.frm_header.frm_len #x now becomes the start of the next byte length/seq

		elif frameheader_unkown.frm_type == 2:
			rp_adv_frame = recvd_packet[x: x + frameheader_unkown.frm_len]
			rp_adv_frame = dissect_RP_ADV(rp_adv_frame)
			frameslist.append(rp_adv_frame)
			x += rp_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == 3: #if frame type is 3, then it is LINK_REQ frame
			link_req_frame = recvd_packet[x: x + frameheader_unkown.frm_len]
			link_req_frame = dissect_LINK_REQ(link_req_frame)
			frameslist.append(link_req_frame)
			x += link_req_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == 4: #if frame type is 4, then it is a LINK_ADV frame
			link_adv_frame = recvd_packet[x: x + frameheader_unkown.frm_len]
			link_adv_frame = dissect_LINK_ADV(link_adv_frame)
			frameslist.append(link_adv_frame)
			x += link_adv_frame.frm_header.frm_len

	packetrecvd = (packetheader, frameslist) 

	return packetrecvd


def frame_header_to_bytes(header):
	#the two if statement here merges short_frame, relevant_Frame and frame_type into 1 byte of data

	
	#short_frm is in the 8th bit position that's why +128, sample: 1 0 0 0 1 1 0 0
	#                                                              ^ 
	if header.short_frm == 1:
		short_and_frmtype = header.frm_type + 128
	else:
		short_and_frmtype = header.frm_type
	
	#relevant _frm is in the 7th bit position that's why +64, sample 1 1 0 0 1 1 0 1
	#                                                                  ^
	if header.relevant_frm == 1:
		short_and_relevant_and_frmtype = short_and_frmtype + 64
	else:
		short_and_relevant_and_frmtype = short_and_frmtype

	#print(short_and_relevant_and_frmtype)
	frame_header = struct.pack("!BB", short_and_relevant_and_frmtype, header.frm_len)

	return frame_header

def dissect_frame_header(recvd_header):
	data = struct.unpack("!BB", recvd_header)

	#since short_frame, relevant_frame and frametype is merged into 1 byte, 
	#we will extract first the short_frame which is in the 8th bit position
	#and next will be the relevant_frame which is in the 7th bit position

	short_and_relevant_and_frametype = data[0]
	frame_len = data[1]

	#check if short_Frame(8th bit) is 1 or 0 then extract it
	if short_and_relevant_and_frametype >= 128:
		short_frame = 1
		relevant_and_frametype = short_and_relevant_and_frametype - 128
	
	else:
		short_frame = 0
		relevant_and_frametype = short_and_relevant_and_frametype

	#check if the relevant_frame(7th bit) is 1 or 0 then extract it
	if relevant_and_frametype >=64:
		relevant_frame = 1
		frametype = relevant_and_frametype - 64

	else:
		relevant_frame = 0
		frametype = relevant_and_frametype

	frame_header = frames.header(short_frame, relevant_frame, frametype, frame_len)

	return frame_header
	

def HELLO_ADV_to_bytes(HELLO_ADV):
	HELLO_ADV.frm_header.frm_len = 2 + 2 #frame header + len(hello sqn no which is 2 bytes)
	frame_header = frame_header_to_bytes(HELLO_ADV.frm_header)

	hello_sqn_no = struct.pack("!H", HELLO_ADV.HELLO_sqn_no)

	return frame_header + hello_sqn_no

def dissect_HELLO_ADV(recvd_HELLO_ADV):
	frame_header = dissect_frame_header(recvd_HELLO_ADV[:2])

	hello_sqn_no = recvd_HELLO_ADV[2:]

	hello_sqn_no = struct.unpack("!H", hello_sqn_no)

	hello_adv = frames.HELLO_ADV(frame_header, hello_sqn_no)

	return hello_adv


def RP_ADV_to_bytes(RP_ADV):
	RP_ADV.frm_header.frm_len = 2 + 1*(len(RP_ADV.rp_msgs)) #setting the frame length of RP_ADV
	frame_header = frame_header_to_bytes(RP_ADV.frm_header)

	rp_adv_msg_list = b'' #initialize empty byte to store rp_adv_msg
	for i in RP_ADV.rp_msgs:
		rp_adv_msg_list = rp_adv_msg_list + RP_ADV_msg_to_bytes(i)
	
	#print(rp_adv_msg_list)
	rp_adv = frame_header + rp_adv_msg_list

	return rp_adv

def dissect_RP_ADV(recvd_RP_ADV):
	frame_header = dissect_frame_header(recvd_RP_ADV[:2])
	rp_adv_msg_list_raw = recvd_RP_ADV[2:]

	rp_adv_msg_list = []

	for i in rp_adv_msg_list_raw:
		#iterate through the raw rp_adv_msg_list to properly parse each rp_adv_msgs
		rp_adv_msg_list.append(dissect_RP_ADV_msg(i))
		

	rp_adv = frames.RP_ADV(frame_header, rp_adv_msg_list)

	return rp_adv


def RP_ADV_msg_to_bytes(RP_ADV_msg):
	#since rp_ADV_msg is 1 byte, the first 7 bits is the rp_127range, and the last bit is the ogm_req
	#rp_127range's maximum value is 127 that's why if ogm_req is 1, add 128(2^7, since ogm_req is in
	# the 8th position of 8 bits)
	if RP_ADV_msg.ogm_req == 1: 
		ogm_req_and_rp_127range = RP_ADV_msg.rp_127range + 128
	else:
		ogm_req_and_rp_127range = RP_ADV_msg.rp_127range

	#print(ogm_req_and_rp_127range)
	rp_adv_msg = struct.pack("!B", ogm_req_and_rp_127range)
	
	return rp_adv_msg

def dissect_RP_ADV_msg(recvd_RP_msg):
	#combined ogm_req(1 bit) to rp_127range(7 bits)
	#ogmreq_rp127range = struct.unpack("!B", recvd_RP_msg)
	ogmreq_rp127range = recvd_RP_msg

	#checking if the 8th bit is 1 or 0. 
	if ogmreq_rp127range >= 128:
		RP_ADV_msg = frames.RP_ADV_msg(ogmreq_rp127range - 128, 1)

	else:
		RP_ADV_msg = frames.RP_ADV_msg(ogmreq_rp127range, 0)

	return RP_ADV_msg
	

def LINK_REQ_to_bytes(LINK_REQ):
	LINK_REQ.frm_header.frm_len = 2 + 4
	frame_header = frame_header_to_bytes(LINK_REQ.frm_header)

	destination_local_id = struct.pack("!I", LINK_REQ.dest_local_id)

	return frame_header + destination_local_id

def dissect_LINK_REQ(recvd_LINK_REQ):
	frame_header = dissect_frame_header(recvd_LINK_REQ[:2])
	destination_local_id = recvd_LINK_REQ[2:]

	destination_local_id = struct.unpack("!I", destination_local_id)

	link_req = frames.LINK_REQ(frame_header, destination_local_id)

	return link_req


def LINK_ADV_msg_to_bytes(LINK_ADV_msg):
	transmitter_device_index = LINK_ADV_msg.trans_dev_index
	peer_device_index = LINK_ADV_msg.peer_dev_index
	peer_local_id = LINK_ADV_msg.peer_local_id

	link_adv_msg = struct.pack("!BBI", transmitter_device_index, peer_device_index, peer_local_id)

	return link_adv_msg

def dissect_LINK_ADV_msg(recvd_LINK_ADV_msg):
	recvd_link_adv_msg = struct.unpack("!BBI", recvd_LINK_ADV_msg)

	transmitter_device_index = recvd_link_adv_msg[0]
	peer_device_index = recvd_link_adv_msg[1]
	peer_local_id = recvd_link_adv_msg[2]

	link_adv_msg = frames.LINK_ADV_msg(transmitter_device_index, peer_device_index, peer_local_id)

	return link_adv_msg


def LINK_ADV_to_bytes(LINK_ADV):
	LINK_ADV.frm_header.frm_len = 2 + 2 + 6*(len(LINK_ADV.link_msgs))
	frame_header = frame_header_to_bytes(LINK_ADV.frm_header)
	device_sequence_no_reference = struct.pack("!H", LINK_ADV.dev_sqn_no_ref)

	link_adv_msg_list = b''
	for i in LINK_ADV.link_msgs:
		link_adv_msg_list += LINK_ADV_msg_to_bytes(i)

	link_adv = frame_header + device_sequence_no_reference + link_adv_msg_list

	return link_adv

def dissect_LINK_ADV(recvd_LINK_ADV):
	frame_header = dissect_frame_header(recvd_LINK_ADV[:2]) #since header size is 2 bytes
	
	#the next 2 bytes is the device sequence number reference
	#then unpack the device sequence number reference
	device_sequence_no_reference = recvd_LINK_ADV[2:4] 
	device_sequence_no_reference = struct.unpack("!H", device_sequence_no_reference)
	link_adv_msg_list_raw = recvd_LINK_ADV[4:]

	link_adv_msg_list_raw_size = len(link_adv_msg_list_raw)
	link_adv_msg_list = []

	#iterate through every 6 bytes since the length of a link_adv_msg is 6 bytes
	# 1 byte = transmitter device index, 1 byte = peer device index and 4 bytes = peer local id
	for i in range(0, link_adv_msg_list_raw_size, 6):
		x = dissect_LINK_ADV_msg(link_adv_msg_list_raw[i:(i + 6)])
		#print(x)
		link_adv_msg_list.append(x)

	link_adv = frames.LINK_ADV(frame_header, device_sequence_no_reference, link_adv_msg_list)

	return link_adv






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

