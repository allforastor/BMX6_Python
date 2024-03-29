import socket
import struct
import string
import sys
import random
import socket
import pickle
from xml.etree.ElementTree import canonicalize
import frames as frames
import time
from datetime import datetime
from dataclasses import dataclass
import threading
import binascii
#from runtime import *

group = 'ff02::2'
MYPORT = 6240
MYTTL = 1

# frame types(int) of each frames

frame_type_HELLO_ADV = 4

frame_type_DEV_REQ = 6
frame_type_DEV_ADV = 7
frame_type_LINK_REQ = 8
frame_type_LINK_ADV = 9

frame_type_RP_ADV = 11


frame_type_DESC_REQ = 14
frame_type_DESC_ADV = 15


frame_type_HASH_REQ = 18
frame_type_HASH_ADV = 19


frame_type_OGM_ADV = 22
frame_type_OGM_ACK = 23



@dataclass
class packet_header:
    bmx_version: int
    reserved: int
    pkt_len: int
    transmitterIID: int
    link_adv_sqn: int
    pkt_sqn: int
    local_id: int
    dev_idx: int

@dataclass
class packet:
    header: packet_header
    frames: list

#receiving packet
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
	
	return data, sender
	#data = pickle.loads(data)
	#print (str(sender) + '  ' + repr(data))	

#sending of packets
def send(group, port, ttl, msg):
	addrinfo = socket.getaddrinfo(group, None)[0]

	s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

	# Set Time-to-live (optional)
	ttl_bin = struct.pack('@i', ttl)
	s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
#	data = repr(time.time())
#	msg = pickle.dumps(msg)
	s.sendto(msg, (addrinfo[4][0], port))
#	time.sleep(1)

# checks if the sequence number is max, if already max, current sequence number becomes 0
def is_max(sqn_no, sqn_max):
	if sqn_no == sqn_max:
		sqn_no = 0

#creating packet together with the packetheader
def create_packet(packetheader, frameslist):
	frames_bytes = b'' #initialization of list of frames as bitwise data 

	# iterates through the list of frames to send, convert each frames
	# into bitwise data and add that converted frames into frame_bytes
	for i in frameslist:
		if type(i) == frames.HELLO_ADV:
			frames_bytes += HELLO_ADV_to_bytes(i)

		elif type(i) == frames.RP_ADV:
			frames_bytes += RP_ADV_to_bytes(i)

		elif type(i) == frames.LINK_REQ:
			frames_bytes += LINK_REQ_to_bytes(i)

		elif type(i) == frames.LINK_ADV:
			frames_bytes += LINK_ADV_to_bytes(i)

		elif type(i) == frames.DEV_REQ:
			frames_bytes += DEV_REQ_to_bytes(i)

		elif type(i) == frames.DEV_ADV:
			frames_bytes += DEV_ADV_to_bytes(i)

		elif type(i) == frames.DESC_REQ:
			frames_bytes += DESC_REQ_to_bytes(i)

		elif type(i) == frames.DESC_ADV:
			frames_bytes += DESC_ADV_to_bytes(i)

		elif type(i) == frames.HASH_REQ:
			frames_bytes += HASH_REQ_to_bytes(i)

		elif type(i) == frames.HASH_ADV:
			frames_bytes += HASH_ADV_to_bytes(i)

		elif type(i) == frames.OGM_ACK:
			frames_bytes += OGM_ACK_to_bytes(i)

		elif type(i) == frames.OGM_ADV:
			frames_bytes += OGM_ADV_to_bytes(i)

	
	len_of_all_frames = len(frames_bytes)		# computes the total length(in bytes) of the frames to send

	packetheader.pkt_len = len_of_all_frames + 17	# set the packet length of the created packet. it is the length 
							# of the frames to send plus 17(which is the length of the packet header)

	# converts the packet header data into bitwise data 
	packetheader = struct.pack("!BBHHHIIB", packetheader.bmx_version, packetheader.reserved, 
					packetheader.pkt_len, packetheader.transmitterIID, packetheader.link_adv_sqn, 
					packetheader.pkt_sqn, packetheader.local_id, packetheader.dev_idx)

	created_packet = packetheader + frames_bytes	# created packet consists of packet header(in bytes) + frames to send(in bytes)

	return created_packet

# dissect and parse the received packet which is in a bitwise data format 
def dissect_packet(recvd_packet):
	curr_pos = 17
	packetheader = recvd_packet[:curr_pos]				# since packet header is in the first 17 bytes of the received packet
	packetheader_raw = struct.unpack("!BBHHHIIB", packetheader)	# unpack the packet header
	
	# since struct.unpack() returns tuple, extract each data and parse that into packet header data class
	packetheader = packet_header(packetheader_raw[0], packetheader_raw[1], packetheader_raw[2], 
								packetheader_raw[3], packetheader_raw[4], packetheader_raw[5], 
								packetheader_raw[6], packetheader_raw[7])

	frameslist = []			# initialize and empty frames list and append every frames parsed into it

	while curr_pos != packetheader.pkt_len:				#when not end of the recvd bytes
		
		first_byte = recvd_packet[curr_pos:curr_pos + 1]	# checks the first bit(short_frame) of the recvd packet if
									# the current frame has a short frame header or a long frame header 
		# get the first byte of a frame and 
		# extract the short_frame
		first_byte = first_byte[0]				
		short_frame = (first_byte >> 7) & 1			
		
		# if short_frame is 1, meaning its frame is a short frame
		# and dissect and parse that frame header as short_frame
		if short_frame == 1:
			frameheader_unkown = recvd_packet[curr_pos:curr_pos + 2]	# plus two since the length of the short frame header is 2 bytes
			frameheader_unkown = dissect_short_frame_header(frameheader_unkown)
		# else, dissect and parse frame header as long_frame
		else:
			frameheader_unkown = recvd_packet[curr_pos:curr_pos + 4]	# plus four since the length of the long frame header is 4 bytes
			frameheader_unkown = dissect_long_frame_header(frameheader_unkown)			
		
		
		# checks the frame type(that is found in frame header) of the dissected 
		# frame, parse that into corresponding frame type data class and 
		# appends it to the frames list
		if frameheader_unkown.frm_type == frame_type_HELLO_ADV: 
			hello_adv_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			hello_adv_frame = dissect_HELLO_ADV(hello_adv_frame)
			frameslist.append(hello_adv_frame)
			curr_pos += hello_adv_frame.frm_header.frm_len 			#curr_pos now becomes the start of the next byte length/seq

		elif frameheader_unkown.frm_type == frame_type_RP_ADV:
			rp_adv_frame = recvd_packet[curr_pos: curr_pos + frameheader_unkown.frm_len]
			rp_adv_frame = dissect_RP_ADV(rp_adv_frame)
			frameslist.append(rp_adv_frame)
			curr_pos += rp_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_LINK_REQ: 
			link_req_frame = recvd_packet[curr_pos: curr_pos + frameheader_unkown.frm_len]
			link_req_frame = dissect_LINK_REQ(link_req_frame)
			frameslist.append(link_req_frame)
			curr_pos += link_req_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_LINK_ADV: 
			link_adv_frame = recvd_packet[curr_pos: curr_pos + frameheader_unkown.frm_len]
			link_adv_frame = dissect_LINK_ADV(link_adv_frame)
			frameslist.append(link_adv_frame)
			curr_pos += link_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_DEV_REQ:
			dev_req_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			dev_req_frame = dissect_DEV_REQ(dev_req_frame)
			frameslist.append(dev_req_frame)
			curr_pos += dev_req_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_DEV_ADV:
			dev_adv_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			dev_adv_frame = dissect_DEV_ADV(dev_adv_frame)
			frameslist.append(dev_adv_frame)
			curr_pos += dev_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_DESC_REQ:
			desc_req_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			desc_req_frame = dissect_DESC_REQ(desc_req_frame)
			frameslist.append(desc_req_frame)
			curr_pos += desc_req_frame.frm_header.frm_len
		
		elif frameheader_unkown.frm_type == frame_type_DESC_ADV:
			desc_adv_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			desc_adv_frame = dissect_DESC_ADV(desc_adv_frame)
			frameslist.append(desc_adv_frame)
			curr_pos += desc_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_HASH_REQ:
			hash_req_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			hash_req_frame = dissect_HASH_REQ(hash_req_frame)
			frameslist.append(hash_req_frame)
			curr_pos += hash_req_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_HASH_ADV:
			hash_adv_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			hash_adv_frame = dissect_HASH_ADV(hash_adv_frame)
			frameslist.append(hash_adv_frame)
			curr_pos += hash_adv_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_OGM_ACK:
			ogm_ack_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			ogm_ack_frame = dissect_OGM_ACK(ogm_ack_frame)
			frameslist.append(ogm_ack_frame)
			curr_pos += ogm_ack_frame.frm_header.frm_len

		elif frameheader_unkown.frm_type == frame_type_OGM_ADV:
			ogm_adv_frame = recvd_packet[curr_pos:curr_pos + frameheader_unkown.frm_len]
			ogm_adv_frame = dissect_OGM_ADV(ogm_adv_frame)
			frameslist.append(ogm_adv_frame)
			curr_pos += ogm_adv_frame.frm_header.frm_len

	packetrecvd = packet(packetheader, frameslist)					# create a packet data class using the parsed packet header 
											# and frames list

	return packetrecvd


def short_frame_header_to_bytes(header):
	header.short_frm = 1

	short_frame = header.short_frm
	relevant_frame = header.relevant_frm
	frame_type = header.frm_type

	#used bitshifting to store short frame(1 bit), relevant frame(1 bit) and frame type(6 bits) into 1 byte(8 bits)
	shortFrm_relevantFrm_frmType = short_frame << 7 | relevant_frame << 6 | frame_type

	frame_header = struct.pack("!BB", shortFrm_relevantFrm_frmType, header.frm_len)

	return frame_header


def dissect_short_frame_header(recvd_header):
	data = struct.unpack("!BB", recvd_header)

	shortFrm_relevantFrm_frmType = data[0]
	frame_len = data[1]

	# unpacking short frame, relevant frame and frame type
	short_frame = (shortFrm_relevantFrm_frmType >> 7) & 1 			# & 1 since max value for short frame is 1(1 bit)
	relevant_frame = (shortFrm_relevantFrm_frmType >> 6) & 1 		# & 1 since max value for relevant frame is 1(1 bit)
	frame_type = shortFrm_relevantFrm_frmType & 63 				# & 63 since max value for frame type is 63(6 bits)

	frame_header = frames.short_header(short_frame, relevant_frame, frame_type, frame_len)

	return frame_header

def long_frame_header_to_bytes(header):
	header.short_frm = 0

	short_frame = header.short_frm
	relevant_frame = header.relevant_frm
	frame_type = header.frm_type

	#using bitshifting to store short frame(1 bit), relevant frame(1 bit) and frame type(6 bits) into 1 byte(8 bits)
	shortFrm_relevantFrm_frmType = short_frame << 7 | relevant_frame << 6 | frame_type

	frame_header = struct.pack("!BBH", shortFrm_relevantFrm_frmType, header.reserved, header.frm_len)

	return frame_header

def dissect_long_frame_header(recvd_header):
	# this returns a tuple of (shortFrm_relevantFrm_frmType, reserved, frame_length)
	data = struct.unpack("!BBH", recvd_header)
	
	# extract each element 
	shortFrm_relevantFrm_frmType  = data[0]
	reserved = data[1]
	frame_length = data[2]

	# unpacking short frame, relevant frame and frame type
	short_frame = (shortFrm_relevantFrm_frmType >> 7) & 1 			# & 1 since max value for short frame is 1(1 bit)
	relevant_frame = (shortFrm_relevantFrm_frmType >> 6) & 1 		# & 1 since max value for relevant frame is 1(1 bit)
	frame_type = shortFrm_relevantFrm_frmType & 63 				# & 63 since max value for frame type is 63(6 bits)

	frame_header = frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length)

	return frame_header


def set_frame_header(frame):
	short_frame_header_length = 2
	long_frame_header_length = 4
	relevant_frame = frame.frm_header.relevant_frm


	if type(frame) == frames.HELLO_ADV: # if frame type is HELLO_ADV, set frm_type to 1
		frame_type = frame_type_HELLO_ADV
		short_frame = 1
		hello_sqn_no = frame.HELLO_sqn_no
		frame_length = short_frame_header_length + 2 #size of the hello sequence number
		created_frame = frames.HELLO_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), hello_sqn_no)

	elif type(frame) == frames.RP_ADV:
		frame_type = frame_type_RP_ADV
		reserved = 0
		if len(frame.rp_msgs)*1 + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + 1*(len(frame.rp_msgs))
			created_frame = frames.RP_ADV(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.rp_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + 1*(len(frame.rp_msgs))
			created_frame = frames.RP_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.rp_msgs)

	elif type(frame) == frames.LINK_REQ:
		frame_type = frame_type_LINK_REQ
		short_frame = 1
		destination_local_id = frame.dest_local_id
		frame_length = short_frame_header_length + 4 #size of the destination local id
		created_frame = frames.LINK_REQ(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), destination_local_id)

	elif type(frame) == frames.LINK_ADV:
		frame_type = frame_type_LINK_ADV
		reserved = 0
		device_sequence_no_reference_length = 2
		if len(frame.link_msgs)*6 + device_sequence_no_reference_length + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + device_sequence_no_reference_length + 6*(len(frame.link_msgs)) #since every link msg is 6 bytes in length
			created_frame = frames.LINK_ADV(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.dev_sqn_no_ref, frame.link_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + device_sequence_no_reference_length + 6*(len(frame.link_msgs)) #since every link msg is 6 bytes in length
			created_frame = frames.LINK_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.dev_sqn_no_ref, frame.link_msgs)
	
	elif type(frame) == frames.DEV_REQ:
		frame_type = frame_type_DEV_REQ
		short_frame = 1
		destination_local_id = frame.dest_local_id
		frame_length = short_frame_header_length + 4 # size of tHe destination local id
		created_frame = frames.DEV_REQ(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), destination_local_id)

	elif type(frame) == frames.DEV_ADV:
		frame_type = frame_type_DEV_ADV
		reserved = 0
		device_sequence_no_length = 2
		if len(frame.dev_msgs)*26 + device_sequence_no_length + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + device_sequence_no_length + 26*(len(frame.dev_msgs))
			created_frame = frames.DEV_ADV(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.dev_sqn_no, frame.dev_msgs)
	
		else:
			short_frame = 1
			frame_length = short_frame_header_length + device_sequence_no_length + 26*(len(frame.dev_msgs))
			created_frame = frames.DEV_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.dev_sqn_no, frame.dev_msgs)
	
	elif type(frame) == frames.DESC_REQ:
		frame_type = frame_type_DESC_REQ
		reserved = 0
		if len(frame.desc_msgs)*6 + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + 6*(len(frame.desc_msgs))
			created_frame = frames.DESC_REQ(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.desc_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + 6*(len(frame.desc_msgs))
			created_frame = frames.DESC_REQ(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.desc_msgs)

	elif type(frame) == frames.DESC_ADV:
		frame_type = frame_type_DESC_ADV
		reserved = 0
		extension_frame_length_counter = 0
		for i in frame.desc_msgs:
			extension_frame_length_counter += i.ext_len

		if len(frame.desc_msgs)*70 + extension_frame_length_counter + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + len(frame.desc_msgs)*70 + extension_frame_length_counter
			created_frame = frames.DESC_ADV(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.desc_msgs)

		else:
			short_frame = 1
			frame_length = short_frame_header_length + len(frame.desc_msgs)*70 + extension_frame_length_counter
			created_frame = frames.DESC_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.desc_msgs)

	elif type(frame) == frames.HASH_REQ:
		frame_type = frame_type_HASH_REQ
		reserved = 0
		if len(frame.hash_msgs)*6 + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + 6*(len(frame.hash_msgs))
			created_frame = frames.HASH_REQ(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.hash_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + 6*(len(frame.hash_msgs))
			created_frame = frames.HASH_REQ(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.hash_msgs)

	elif type(frame) == frames.HASH_ADV:
		frame_type = frame_type_HASH_ADV
		short_frame = 1
		transmitterIID4x = frame.trans_iid4x
		description_hash = frame.desc_hash
		frame_length = short_frame_header_length + 2 + 20 # size of the transmitterIID4x = 2 bytes and size of description hash is 20 bytes
		created_frame = frames.HASH_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), transmitterIID4x, description_hash)

	elif type(frame) == frames.OGM_ACK:
		frame_type = frame_type_OGM_ACK
		reserved = 0
		if len(frame.ogm_ack_msgs)*2 + short_frame_header_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + 2*(len(frame.ogm_ack_msgs)) #since every ogm_ack msg is 2 bytes in length
			created_frame = frames.OGM_ACK(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.ogm_ack_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + 2*(len(frame.ogm_ack_msgs)) #since every ogm_ack msg is 2 bytes in length
			created_frame = frames.OGM_ACK(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.ogm_ack_msgs)

	elif type(frame) == frames.OGM_ADV:
		frame_type = frame_type_OGM_ADV
		reserved = 0
		aggregation_sequence_number_length = 1
		ogm_destination_array_size_length = 1
		ogm_destination_array_length = len(frame.ogm_dest_arr)
		if len(frame.ogm_adv_msgs)*4 + short_frame_header_length + aggregation_sequence_number_length + ogm_destination_array_size_length + ogm_destination_array_length > 255:
			short_frame = 0
			frame_length = long_frame_header_length + aggregation_sequence_number_length + ogm_destination_array_size_length + ogm_destination_array_length + 4*(len(frame.ogm_adv_msgs))
			created_frame = frames.OGM_ADV(frames.long_header(short_frame, relevant_frame, frame_type, reserved, frame_length), frame.agg_sqn_no, 
											frame.ogm_dest_arr_size, frame.ogm_dest_arr, frame.ogm_adv_msgs)
		else:
			short_frame = 1
			frame_length = short_frame_header_length + aggregation_sequence_number_length + ogm_destination_array_size_length + ogm_destination_array_length + 4*(len(frame.ogm_adv_msgs))
			created_frame = frames.OGM_ADV(frames.short_header(short_frame, relevant_frame, frame_type, frame_length), frame.agg_sqn_no, 
											frame.ogm_dest_arr_size, frame.ogm_dest_arr, frame.ogm_adv_msgs)

	return created_frame
	
def is_short_header(frame_header):
	if frame_header.short_frm == 1:
		frame_header = short_frame_header_to_bytes(frame_header)
	else:
		frame_header = long_frame_header_to_bytes(frame_header)

	return frame_header

def HELLO_ADV_to_bytes(HELLO_ADV):
	HELLO_ADV = set_frame_header(HELLO_ADV)
	frame_header = short_frame_header_to_bytes(HELLO_ADV.frm_header)
	hello_sqn_no = struct.pack("!H", HELLO_ADV.HELLO_sqn_no)

	hello_adv_bytes = frame_header + hello_sqn_no

	return hello_adv_bytes

def dissect_HELLO_ADV(recvd_HELLO_ADV):
	frame_header = dissect_short_frame_header(recvd_HELLO_ADV[:2])
	hello_sqn_no = recvd_HELLO_ADV[2:]

	hello_sqn_no = struct.unpack("!H", hello_sqn_no)

	hello_adv = frames.HELLO_ADV(frame_header, hello_sqn_no[0])

	return hello_adv


def RP_ADV_to_bytes(RP_ADV):
	RP_ADV = set_frame_header(RP_ADV)
	
	frame_header = is_short_header(RP_ADV.frm_header)

	rp_adv_msg_list = b'' #initialize empty byte to store rp_adv_msg
	for i in RP_ADV.rp_msgs:
		rp_adv_msg_list = rp_adv_msg_list + RP_ADV_msg_to_bytes(i)
	
	#print(rp_adv_msg_list)
	rp_adv_bytes = frame_header + rp_adv_msg_list

	return rp_adv_bytes

def dissect_RP_ADV(recvd_RP_ADV):
	#checks the first bit(short_frame) of the recvd RP_ADV  
	first_byte = recvd_RP_ADV[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_RP_ADV[:2])
		rp_adv_msg_list_raw = recvd_RP_ADV[2:]
	else:
		frame_header = dissect_long_frame_header(recvd_RP_ADV[:4])
		rp_adv_msg_list_raw = recvd_RP_ADV[4:]

	rp_adv_msg_list_raw_size = len(rp_adv_msg_list_raw)
	rp_adv_msg_list = []

	for i in range(0, rp_adv_msg_list_raw_size):
		#iterate through the raw rp_adv_msg_list to properly parse each rp_adv_msgs
		x = dissect_RP_ADV_msg(rp_adv_msg_list_raw[i:(i + 1)])
		rp_adv_msg_list.append(x)
		

	rp_adv = frames.RP_ADV(frame_header, rp_adv_msg_list)

	return rp_adv


def RP_ADV_msg_to_bytes(RP_ADV_msg):

	# using bitshifting and OR bitwise operation to store ogm_req(1 bit) and rp_127range(7 bit) into 1 byte(8bits)
	ogmreq_and_rp127range = (RP_ADV_msg.rp_127range << 1) | RP_ADV_msg.ogm_req

	rp_adv_msg_bytes = struct.pack("!B", ogmreq_and_rp127range)

	return rp_adv_msg_bytes

def dissect_RP_ADV_msg(recvd_RP_msg):
	
	recvd_RP_msg = struct.unpack("!B", recvd_RP_msg)
	ogmreq_and_rp127range = recvd_RP_msg[0]

	rp_127range = (ogmreq_and_rp127range >> 1) & 127
	ogm_req = ogmreq_and_rp127range & 1

	rp_msg = frames.RP_ADV_msg(rp_127range, ogm_req)

	return rp_msg

def LINK_REQ_to_bytes(LINK_REQ):
	LINK_REQ = set_frame_header(LINK_REQ)
	frame_header = short_frame_header_to_bytes(LINK_REQ.frm_header)

	destination_local_id = struct.pack("!I", LINK_REQ.dest_local_id)

	link_req_bytes = frame_header + destination_local_id

	return link_req_bytes

def dissect_LINK_REQ(recvd_LINK_REQ):
	frame_header = dissect_short_frame_header(recvd_LINK_REQ[:2])
	destination_local_id = recvd_LINK_REQ[2:]

	destination_local_id = struct.unpack("!I", destination_local_id)

	link_req = frames.LINK_REQ(frame_header, destination_local_id[0])

	return link_req


def LINK_ADV_msg_to_bytes(LINK_ADV_msg):
	transmitter_device_index = LINK_ADV_msg.trans_dev_index
	peer_device_index = LINK_ADV_msg.peer_dev_index
	peer_local_id = LINK_ADV_msg.peer_local_id

	link_adv_msg_bytes = struct.pack("!BBI", transmitter_device_index, peer_device_index, peer_local_id)

	return link_adv_msg_bytes

def dissect_LINK_ADV_msg(recvd_LINK_ADV_msg):
	recvd_link_adv_msg = struct.unpack("!BBI", recvd_LINK_ADV_msg)

	transmitter_device_index = recvd_link_adv_msg[0]
	peer_device_index = recvd_link_adv_msg[1]
	peer_local_id = recvd_link_adv_msg[2]

	link_adv_msg = frames.LINK_ADV_msg(transmitter_device_index, peer_device_index, peer_local_id)

	return link_adv_msg


def LINK_ADV_to_bytes(LINK_ADV):
	#LINK_ADV.frm_header.frm_len = 2 + 2 + 6*(len(LINK_ADV.link_msgs))
	LINK_ADV = set_frame_header(LINK_ADV)
	frame_header = is_short_header(LINK_ADV.frm_header)
	
	if LINK_ADV.dev_sqn_no_ref < 0:
		device_sequence_no_reference = struct.pack("!h", LINK_ADV.dev_sqn_no_ref)
	else:
		device_sequence_no_reference = struct.pack("!H", LINK_ADV.dev_sqn_no_ref)

	link_adv_msg_list = b''
	for i in LINK_ADV.link_msgs:
		link_adv_msg_list += LINK_ADV_msg_to_bytes(i)

	link_adv_bytes = frame_header + device_sequence_no_reference + link_adv_msg_list

	return link_adv_bytes

def dissect_LINK_ADV(recvd_LINK_ADV):
	#checks the first bit(short_frame) of the recvd LINK_ADV  
	first_byte = recvd_LINK_ADV[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_LINK_ADV[:2]) #since short header size is 2 bytes
		#the next 2 bytes is the device sequence number reference
		#then unpack the device sequence number reference
		device_sequence_no_reference = recvd_LINK_ADV[2:4] 
		device_sequence_no_reference = struct.unpack("!H", device_sequence_no_reference)
		link_adv_msg_list_raw = recvd_LINK_ADV[4:]
	
	else:
		frame_header = dissect_long_frame_header(recvd_LINK_ADV[:4]) #since long header size is 4 bytes
		#the next 2 bytes is the device sequence number reference
		#then unpack the device sequence number reference
		device_sequence_no_reference = recvd_LINK_ADV[4:6] 
		device_sequence_no_reference = struct.unpack("!H", device_sequence_no_reference)
		link_adv_msg_list_raw = recvd_LINK_ADV[6:]

	link_adv_msg_list_raw_size = len(link_adv_msg_list_raw)
	link_adv_msg_list = []

	#iterate through every 6 bytes since the length of a link_adv_msg is 6 bytes
	# 1 byte = transmitter device index, 1 byte = peer device index and 4 bytes = peer local id
	for i in range(0, link_adv_msg_list_raw_size, 6):
		x = dissect_LINK_ADV_msg(link_adv_msg_list_raw[i:(i + 6)]) #dissects the 6 bytes
		link_adv_msg_list.append(x)

	link_adv = frames.LINK_ADV(frame_header, device_sequence_no_reference[0], link_adv_msg_list)

	return link_adv

def DEV_REQ_to_bytes(DEV_REQ):
	DEV_REQ = set_frame_header(DEV_REQ) 
	frame_header = short_frame_header_to_bytes(DEV_REQ.frm_header)
	destination_local_id = struct.pack("!I", DEV_REQ.dest_local_id)

	dev_req_bytes = frame_header + destination_local_id

	return dev_req_bytes

def dissect_DEV_REQ(recvd_DEV_REQ):
	frame_header = dissect_short_frame_header(recvd_DEV_REQ[:2])
	destination_local_id = recvd_DEV_REQ[2:]

	destination_local_id = struct.unpack("!I", destination_local_id)

	dev_req = frames.DEV_REQ(frame_header, destination_local_id[0])

	return dev_req

def DEV_ADV_msg_to_bytes(DEV_ADV_msg):
	device_index = DEV_ADV_msg.dev_index
	channel = DEV_ADV_msg.channel
	transmitter_bitrate_min = DEV_ADV_msg.trans_bitrate_min
	transmitter_bitrate_max = DEV_ADV_msg.trans_bitrate_max
	local_ipv6 = DEV_ADV_msg.local_ipv6.to_bytes(16, 'big')
	mac_address = DEV_ADV_msg.mac_address.to_bytes(6, 'big')

	dev_adv_msg_bytes = struct.pack("!B B B B 16s 6s", device_index, channel, transmitter_bitrate_min, 
												transmitter_bitrate_max, local_ipv6, mac_address)

	return dev_adv_msg_bytes

def dissect_DEV_ADV_msg(recvd_DEV_ADV_msg):
	recvd_dev_adv_msg = struct.unpack("!B B B B 16s 6s", recvd_DEV_ADV_msg)

	device_index = recvd_dev_adv_msg[0]
	channel = recvd_dev_adv_msg[1]		
	transmitter_bitrate_min = recvd_dev_adv_msg[2]
	transmitter_bitrate_max =recvd_dev_adv_msg[3]
	local_ipv6 = int.from_bytes(recvd_dev_adv_msg[4], 'big')
	mac_address = int.from_bytes(recvd_dev_adv_msg[5], 'big')

	dev_adv_msg = frames.DEV_ADV_msg(device_index, channel, transmitter_bitrate_min, transmitter_bitrate_max, local_ipv6, mac_address)

	return dev_adv_msg

def DEV_ADV_to_bytes(DEV_ADV):
	DEV_ADV = set_frame_header(DEV_ADV)
	frame_header = is_short_header(DEV_ADV.frm_header)


	device_sequence_number = struct.pack("!H", DEV_ADV.dev_sqn_no)

	dev_adv_msg_list = b''
	for i in DEV_ADV.dev_msgs:
		dev_adv_msg_list = dev_adv_msg_list + DEV_ADV_msg_to_bytes(i)

	dev_adv_bytes = frame_header + device_sequence_number + dev_adv_msg_list

	return dev_adv_bytes

def dissect_DEV_ADV(recvd_DEV_ADV):
	#checks the first bit(short_frame) of the recvd DEV_ADV  
	first_byte = recvd_DEV_ADV[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_DEV_ADV[:2]) #since short header size is 2 bytes
		#the next 2 bytes is the device sequence number 
		#then unpack the device sequence number 
		device_sequence_no = recvd_DEV_ADV[2:4] 
		device_sequence_no = struct.unpack("!H", device_sequence_no)
		dev_adv_msg_list_raw = recvd_DEV_ADV[4:] #received dev_adv_msgs are from 4 bytes onwards
	else:
		frame_header = dissect_long_frame_header(recvd_DEV_ADV[:4]) #since long header size is 4 bytes
		#the next 2 bytes is the device sequence number 
		#then unpack the device sequence number 
		device_sequence_no = recvd_DEV_ADV[4:6] 
		device_sequence_no = struct.unpack("!H", device_sequence_no)
		dev_adv_msg_list_raw = recvd_DEV_ADV[6:]#received dev_adv_msgs are from 6 bytes onwards

	dev_adv_msg_list_raw_size = len(dev_adv_msg_list_raw)
	dev_adv_msg_list = []

	#iterate through every 26 bytes since the length of a dev_adv_msg is 26 bytes
	# 1 byte = device index, 1 byte = channel, 1 byte = transmitter bitrate min, 1 btye = transmitter bitrate max, 
	# 16 bytes = local ipv6 and 6 bytes = mac address
	for i in range(0, dev_adv_msg_list_raw_size, 26):
		x = dissect_DEV_ADV_msg(dev_adv_msg_list_raw[i:(i + 26)]) #dissects the 26 bytes
		dev_adv_msg_list.append(x)

	dev_adv = frames.DEV_ADV(frame_header, device_sequence_no[0], dev_adv_msg_list)

	return dev_adv

def DESC_REQ_msg_to_bytes(DESC_REQ_msg):
	destination_local_id = DESC_REQ_msg.dest_local_id
	receiver_iid = DESC_REQ_msg.receiver_iid

	desc_req_msg_bytes = struct.pack("!IH", destination_local_id, receiver_iid)

	return desc_req_msg_bytes

def dissect_DESC_REQ_msg(recvd_DESC_REQ_msg):
	recvd_desc_req_msg = struct.unpack("!IH", recvd_DESC_REQ_msg)

	destination_local_id = recvd_desc_req_msg[0]
	receiver_iid = recvd_desc_req_msg[1]

	desc_req_msg = frames.DESC_REQ_msg(destination_local_id, receiver_iid)

	return desc_req_msg

def DESC_REQ_to_bytes(DESC_REQ):
	DESC_REQ = set_frame_header(DESC_REQ)
	frame_header = is_short_header(DESC_REQ.frm_header)


	desc_req_msg_list = b''
	for i in DESC_REQ.desc_msgs:
		desc_req_msg_list = desc_req_msg_list + DESC_REQ_msg_to_bytes(i)

	desc_req_bytes = frame_header + desc_req_msg_list

	return desc_req_bytes

def dissect_DESC_REQ(recvd_DESC_REQ):
	#checks the first bit(short_frame) of the recvd DESC_REQ  
	first_byte = recvd_DESC_REQ[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_DESC_REQ[:2]) #since short header size is 2 bytes
		desc_req_msg_list_raw = recvd_DESC_REQ[2:] #received desc_req_msgs are from 2 bytes onwards

	else:
		frame_header = dissect_long_frame_header(recvd_DESC_REQ[:4]) #since short header size is 4 bytes
		desc_req_msg_list_raw = recvd_DESC_REQ[4:] #received dev_adv_msgs are from 4 bytes onwards
	
	desc_req_msg_list_raw_size = len(desc_req_msg_list_raw)
	desc_req_msg_list = []

	#iterate through every 6 bytes since the length of a desc_req_msg is 6 bytes
	# 4 bytes = destination local id and 2 bytes = receiver iid
	for i in range(0, desc_req_msg_list_raw_size, 6):
		x = dissect_DESC_REQ_msg(desc_req_msg_list_raw[i:(i + 6)]) #dissects the 6 bytes
		desc_req_msg_list.append(x)

	desc_req = frames.DESC_REQ(frame_header, desc_req_msg_list)

	return desc_req

def DESC_ADV_msg_to_bytes(DESC_ADV_msg):
	transmitterIID4x = DESC_ADV_msg.trans_iid4x
	name = DESC_ADV_msg.name
	pkid = DESC_ADV_msg.pkid
	code_version = DESC_ADV_msg.code_version
	capabilities = DESC_ADV_msg.capabilities
	desc_sqn_no = DESC_ADV_msg.desc_sqn_no
	ogm_min_sqn_no = DESC_ADV_msg.ogm_min_sqn_no
	ogm_range = DESC_ADV_msg.ogm_range
	transmission_interval = DESC_ADV_msg.trans_interval
	reserved = DESC_ADV_msg.reserved
	extension_length = DESC_ADV_msg.ext_len
	extension_frames = DESC_ADV_msg.ext_frm #as bytes

	
	desc_adv_msg_bytes = struct.pack("!H 32s 20s H H H H H H H H", transmitterIID4x, name, pkid, code_version, capabilities, desc_sqn_no, 
																	ogm_min_sqn_no, ogm_range, transmission_interval, reserved, extension_length) + extension_frames

	return desc_adv_msg_bytes

def dissect_DESC_ADV_msg(recvd_DESC_ADV_msg):
	recvd_desc_adv_msg = struct.unpack("!H 32s 20s H H H H H H H H", recvd_DESC_ADV_msg[:70]) 
	extension_frames = recvd_DESC_ADV_msg[70:]

	transmitterIID4x = recvd_desc_adv_msg[0]
	name = recvd_desc_adv_msg[1]
	pkid = recvd_desc_adv_msg[2]
	code_version = recvd_desc_adv_msg[3]
	capabilities = recvd_desc_adv_msg[4]
	desc_sqn_no = recvd_desc_adv_msg[5]
	ogm_min_sqn_no = recvd_desc_adv_msg[6]
	ogm_range = recvd_desc_adv_msg[7]
	transmission_interval = recvd_desc_adv_msg[8]
	reserved = recvd_desc_adv_msg[9]
	extension_length = recvd_desc_adv_msg[10]

	desc_adv_msg = frames.DESC_ADV_msg(transmitterIID4x, name, pkid, code_version, capabilities, desc_sqn_no, 
										ogm_min_sqn_no, ogm_range, transmission_interval, reserved, extension_length, extension_frames)

	return desc_adv_msg

def DESC_ADV_to_bytes(DESC_ADV):
	DESC_ADV = set_frame_header(DESC_ADV)
	frame_header = is_short_header(DESC_ADV.frm_header)

	desc_adv_msg_list = b''
	for i in DESC_ADV.desc_msgs:
		desc_adv_msg_list = desc_adv_msg_list + DESC_ADV_msg_to_bytes(i)

	desc_adv_bytes = frame_header + desc_adv_msg_list

	return desc_adv_bytes

def dissect_DESC_ADV(recvd_DESC_ADV):
	#checks the first bit(short_frame) of the recvd DESC_ADV  
	first_byte = recvd_DESC_ADV[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_DESC_ADV[:2]) #since short header size is 2 bytes
		desc_adv_msg_list_raw = recvd_DESC_ADV[2:] #received desc_adv_msgs are from 2 bytes onwards

	else:
		frame_header = dissect_long_frame_header(recvd_DESC_ADV[:4]) #since short header size is 4 bytes
		desc_adv_msg_list_raw = recvd_DESC_ADV[4:] #received desc_adv_msgs are from 4 bytes onwards

	desc_adv_msg_list = []

	ctr = 0
	while ctr != frame_header.frm_len:
		extension_length = desc_adv_msg_list_raw[(ctr + 68):(ctr + 70)]
		if len(extension_length) == 0:
			break
		
		extension_length = struct.unpack("!H", extension_length)
		extension_length = extension_length[0]

		x = dissect_DESC_ADV_msg(desc_adv_msg_list_raw[ctr:ctr + 70 + extension_length])
		desc_adv_msg_list.append(x)

		ctr = ctr + 70 + extension_length

	desc_adv = frames.DESC_ADV(frame_header, desc_adv_msg_list)

	return desc_adv
	

def HASH_REQ_msg_to_bytes(HASH_REQ_msg):
	destination_local_id = HASH_REQ_msg.dest_local_id
	receiver_iid = HASH_REQ_msg.receiver_iid

	hash_req_msg_bytes = struct.pack("!IH", destination_local_id, receiver_iid)

	return hash_req_msg_bytes

def dissect_HASH_REQ_msg(recvd_HASH_REQ_msg):
	recvd_hash_req_msg = struct.unpack("!IH", recvd_HASH_REQ_msg)

	destination_local_id = recvd_hash_req_msg[0]
	receiver_iid = recvd_hash_req_msg[1]

	hash_req_msg = frames.HASH_REQ_msg(destination_local_id, receiver_iid)

	return hash_req_msg

def HASH_REQ_to_bytes(HASH_REQ):
	HASH_REQ = set_frame_header(HASH_REQ)
	frame_header = is_short_header(HASH_REQ.frm_header)


	hash_req_msg_list = b''
	for i in HASH_REQ.hash_msgs:
		hash_req_msg_list = hash_req_msg_list + HASH_REQ_msg_to_bytes(i)

	hash_req_bytes = frame_header + hash_req_msg_list

	return hash_req_bytes

def dissect_HASH_REQ(recvd_HASH_REQ):
	#checks the first bit(short_frame) of the recvd HASH_REQ  
	first_byte = recvd_HASH_REQ[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_HASH_REQ[:2]) #since short header size is 2 bytes
		hash_req_msg_list_raw = recvd_HASH_REQ[2:] #received hash_req_msgs are from 2 bytes onwards

	else:
		frame_header = dissect_long_frame_header(recvd_HASH_REQ[:4]) #since long header size is 4 bytes
		hash_req_msg_list_raw = recvd_HASH_REQ[4:] #received hash_req_msgs are from 4 bytes onwards
	
	hash_req_msg_list_raw_size = len(hash_req_msg_list_raw)
	hash_req_msg_list = []

	#iterate through every 6 bytes since the length of a hash_req_msg is 6 bytes
	# 4 bytes = destination local id and 2 bytes = receiver iid
	for i in range(0, hash_req_msg_list_raw_size, 6):
		x = dissect_HASH_REQ_msg(hash_req_msg_list_raw[i:(i + 6)]) #dissects the 6 bytes
		hash_req_msg_list.append(x)

	hash_req = frames.HASH_REQ(frame_header, hash_req_msg_list)

	return hash_req

def HASH_ADV_to_bytes(HASH_ADV):
	HASH_ADV = set_frame_header(HASH_ADV) 
	frame_header = short_frame_header_to_bytes(HASH_ADV.frm_header)
	
	transmitterIID4x_and_descriptionHash = struct.pack("!H20s", HASH_ADV.trans_iid4x, HASH_ADV.desc_hash)

	hash_adv_bytes = frame_header + transmitterIID4x_and_descriptionHash

	return hash_adv_bytes

def dissect_HASH_ADV(recvd_HASH_ADV):
	frame_header = dissect_short_frame_header(recvd_HASH_ADV[:2])
	transmitterIID4x_and_descriptionHash = recvd_HASH_ADV[2:]

	transmitterIID4x_and_descriptionHash = struct.unpack("!H 20s", transmitterIID4x_and_descriptionHash)
	
	transmitterIID4x = transmitterIID4x_and_descriptionHash[0]
	description_hash = transmitterIID4x_and_descriptionHash[1]

	hash_adv = frames.HASH_ADV(frame_header, transmitterIID4x, description_hash)

	return hash_adv

def OGM_ACK_msg_to_bytes(OGM_ACK_msg):
	ogm_destination = OGM_ACK_msg.ogm_dest
	aggregation_sequence_number = OGM_ACK_msg.agg_sqn_no

	ogm_ack_msg_bytes = struct.pack("!BB", ogm_destination, aggregation_sequence_number)

	return ogm_ack_msg_bytes

def dissect_OGM_ACK_msg(recvd_OGM_ACK_msg):
	recvd_ogm_ack_msg = struct.unpack("!BB", recvd_OGM_ACK_msg)

	ogm_destination = recvd_ogm_ack_msg[0]
	aggregation_sequence_number = recvd_ogm_ack_msg[1]

	ogm_ack_msg = frames.OGM_ACK_msg(ogm_destination, aggregation_sequence_number)

	return ogm_ack_msg

def OGM_ACK_to_bytes(OGM_ACK):
	OGM_ACK = set_frame_header(OGM_ACK)
	frame_header = is_short_header(OGM_ACK.frm_header)

	ogm_ack_msg_list = b''
	for i in OGM_ACK.ogm_ack_msgs:
		ogm_ack_msg_list = ogm_ack_msg_list + OGM_ACK_msg_to_bytes(i)

	ogm_ack_bytes = frame_header + ogm_ack_msg_list

	return ogm_ack_bytes


def dissect_OGM_ACK(recvd_OGM_ACK):
	#checks the first bit(short_frame) of the recvd OGM_ACK  
	first_byte = recvd_OGM_ACK[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_OGM_ACK[:2]) #since short header size is 2 bytes
		ogm_ack_msg_list_raw = recvd_OGM_ACK[2:] #received ogm_ack_msgs are from 2 bytes onwards

	else:
		frame_header = dissect_long_frame_header(recvd_OGM_ACK[:4]) #since long header size is 4 bytes
		ogm_ack_msg_list_raw = recvd_OGM_ACK[4:] #received ogm_ack_msgs are from 4 bytes onwards

	ogm_ack_msg_list_raw_size = len(ogm_ack_msg_list_raw)
	ogm_ack_msg_list = []

	#iterate through every 2 bytes since the length of a ogm_ack_msg is 2 bytes
	# 1 byte = ogm sequence number and 1 byte = aggregation sequence number
	for i in range(0, ogm_ack_msg_list_raw_size, 2):
		x = dissect_OGM_ACK_msg(ogm_ack_msg_list_raw[i:(i + 2)]) #dissects the 2 bytes
		ogm_ack_msg_list.append(x)

	ogm_ack = frames.OGM_ACK(frame_header, ogm_ack_msg_list)

	return ogm_ack
	

def OGM_ADV_msg_to_bytes(OGM_ADV_msg):
	# since mantisse is 5 bits, exponent is 5 bits and iid_offset is 6 bits, combine
	# them into 2 bytes of data

	mantisse = OGM_ADV_msg.metric_mantisse
	exponent = OGM_ADV_msg.metric_exponent
	iid_offset = OGM_ADV_msg.iid_offset

	#using bitshifting to store mantisse(5 bits), exponent(5 bits) and iid offset(6 btis) into 2 bytes(16 bits)
	mantisse_exponent_iidOffset = mantisse << 11 | exponent << 6 | iid_offset
	
	ogm_sequence_number = OGM_ADV_msg.ogm_sqn_no

	ogm_adv_msg_bytes = struct.pack("!HH", mantisse_exponent_iidOffset, ogm_sequence_number)
	
	return ogm_adv_msg_bytes

def dissect_OGM_ADV_msg(recvd_OGM_ADV_msg):
	# unpack received data
	data = struct.unpack("!HH", recvd_OGM_ADV_msg)
	
	# extract from tuple
	mantisse_exponent_iidOffset = data[0]
	ogm_sequence_number = data[1]

	mantisse = (mantisse_exponent_iidOffset >> 11) & 31
	exponent = (mantisse_exponent_iidOffset >> 6) & 31
	iid_offset = mantisse_exponent_iidOffset & 63

	ogm_adv_msg = frames.OGM_ADV_msg(mantisse, exponent, iid_offset, ogm_sequence_number)

	return ogm_adv_msg

def OGM_ADV_to_bytes(OGM_ADV):
	OGM_ADV = set_frame_header(OGM_ADV)
	frame_header = is_short_header(OGM_ADV.frm_header)

	aggregation_sequence_number = OGM_ADV.agg_sqn_no
	ogm_destination_array_size = OGM_ADV.ogm_dest_arr_size
	ogm_destination_array = OGM_ADV.ogm_dest_arr

	aggregationSequenceNumber_ogmDestinationArraySize = struct.pack("BB", aggregation_sequence_number, ogm_destination_array_size)
	ogm_destination_array_bytes = bytes(ogm_destination_array)

	ogm_adv_msg_list = b''
	for i in OGM_ADV.ogm_adv_msgs:
		ogm_adv_msg_list = ogm_adv_msg_list + OGM_ADV_msg_to_bytes(i)

	ogm_adv_bytes = frame_header + aggregationSequenceNumber_ogmDestinationArraySize + ogm_destination_array_bytes + ogm_adv_msg_list

	return ogm_adv_bytes

def dissect_OGM_ADV(recvd_OGM_ADV):
	#checks the first bit(short_frame) of the recvd OGM_ADV  
	first_byte = recvd_OGM_ADV[:1]
	first_byte = first_byte[0]
	short_frame = (first_byte >> 7) & 1

	#checks if short frame is 1 or 0
	if short_frame == 1:
		frame_header = dissect_short_frame_header(recvd_OGM_ADV[:2]) #since short header size is 2 bytes

		aggregationSequenceNumber_ogmDestinationArraySize = recvd_OGM_ADV[2:4]
		aggregationSequenceNumber_ogmDestinationArraySize = struct.unpack("!BB", aggregationSequenceNumber_ogmDestinationArraySize)
		
		aggregation_sequence_number = aggregationSequenceNumber_ogmDestinationArraySize[0]
		ogm_destination_array_size = aggregationSequenceNumber_ogmDestinationArraySize[1]

		ogm_destination_array = recvd_OGM_ADV[4:4 + ogm_destination_array_size]
		ogm_destination_array = list(ogm_destination_array)
		
		ogm_adv_msg_list_raw = recvd_OGM_ADV[4 + ogm_destination_array_size:] 


	else:
		frame_header = dissect_long_frame_header(recvd_OGM_ADV[:4]) #since long header size is 4 bytes
		aggregationSequenceNumber_ogmDestinationArraySize = recvd_OGM_ADV[4:6]
		aggregationSequenceNumber_ogmDestinationArraySize = struct.unpack("!BB", aggregationSequenceNumber_ogmDestinationArraySize)
		
		aggregation_sequence_number = aggregationSequenceNumber_ogmDestinationArraySize[0]
		ogm_destination_array_size = aggregationSequenceNumber_ogmDestinationArraySize[1]

		ogm_destination_array = recvd_OGM_ADV[6:6 + ogm_destination_array_size]
		ogm_destination_array = list(ogm_destination_array)
		
		ogm_adv_msg_list_raw = recvd_OGM_ADV[6 + ogm_destination_array_size:] 


	ogm_adv_msg_list_raw_size = len(ogm_adv_msg_list_raw)
	ogm_adv_msg_list = []

	#iterate through every 4 bytes since the length of a dev_adv_msg is 4 bytes
	# 5 bits = mantisse, 5 bits = exponent, 6 bits = iid offset, 2 btyes = ogm sqn number 
	
	for i in range(0, ogm_adv_msg_list_raw_size, 4):
		x = dissect_OGM_ADV_msg(ogm_adv_msg_list_raw[i:(i + 4)]) #dissects the 4 bytes
		ogm_adv_msg_list.append(x)

	ogm_adv = frames.OGM_ADV(frame_header, aggregation_sequence_number, ogm_destination_array_size, ogm_destination_array, ogm_adv_msg_list)

	return ogm_adv




'''
hello = frames.HELLO_ADV(frames.short_header(0,0,0,0), 1000)
frameslist = [hello]
packetheader = packet_header(1, 2, 3, 4, 5, 6, 7, 8)

a = create_packet(packetheader, frameslist)

while True:
	f , senders = listen(group, MYPORT)
	f = dissect_packet(f)
	print(f)
#	frames_list = runtime.packet_received(f, senders[0])
#	print(dissect_packet(a))
	#send(group, MYPORT, MYTTL, a)
#	print_all(local_list)
#	print(frames_list)

	
'''
