import copy
import time
import random
import socket
import psutil
import ipaddress
from os import link
from pickle import TRUE
from sys import getsizeof
from collections import deque
from numpy import append, empty
from dataclasses import dataclass, field
import bmx
import nodes
import frames




### INITIALIZATION

@dataclass
class frame_handler:
    hello_sqn: int = random.randint(0,65535)                    # add 1 every send of HELLO_ADV
    dev_sqn: int = 1                                            # add 1 every send of DEV_ADV
    link_sqn: int = 1                                           # add 1 every send of LINK_ADV
    msg_index: int = 0                                          # serves as the index for LINK_ADV/RP_ADV ordering

    dev_req_ids: list = field(default_factory=lambda:[])        # list of ids to send DEV_REQs to
    link_req_ids: list = field(default_factory=lambda:[])       # list of ids to send LINK_REQs to
    lndevs_possible: list = field(default_factory=lambda:[])    # list of lndevs that might send LINK and RP msgs
    lndevs_expected: list = field(default_factory=lambda:[])    # list of lndevs that will send LINK and RP msgs
    link_msgs2send: list = field(default_factory=lambda:[])     # list of LINK_ADV msgs to send
    dev_msgs2send: list = field(default_factory=lambda:[])      # list of DEV_ADV msgs to send
    rp_msgs2send: list = field(default_factory=lambda:[])       # list of RP_ADV msgs to send

    frames2send: list = field(default_factory=lambda:[])        # list of friends to send

    def reset(self):
        self.dev_req_ids.clear()
        self.link_req_ids.clear()
        self.lndevs_possible.clear()
        self.link_msgs2send.clear()
        self.dev_msgs2send.clear()
        self.rp_msgs2send.clear()
        self.frames2send.clear()
    
    def iterate(self):
        for frame in self.frames2send:    
            if(type(frame) == frames.HELLO_ADV):    # HELLO_ADV
                self.hello_sqn = self.hello_sqn + 1
            elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
                self.dev_sqn = self.dev_sqn + 1
            elif(type(frame) == frames.LINK_ADV):   # LINK_ADV
                self.link_sqn = self.link_sqn + 1

def get_interfaces(iflist):
    dev_id = len(iflist)
    
    if(len(iflist) == 0):
        iflist.append(nodes.dev_node())
        dev_id = dev_id + 1

    def check_interface(name, iflist):
        for itf in iflist:
            if((itf.name == name) and (itf.idx > 0)):
                return itf.idx
        return -1

    def inactive(iflist):
        for itf in iflist:                                                      # assume all interfaces inactive
            itf.active = 0

    inactive(iflist)
    for x, y in psutil.net_if_addrs().items():
        id = check_interface(x, iflist)
        if(id == -1):
            interface = nodes.dev_node(name = x, idx = dev_id, active = 1)  # new interfaces always active
        else:
            interface = iflist[id]                                          # if found, mark as active
            iflist[id].active = 1  
        for z in y:
            if(z.family is socket.AF_INET):
                interface.ipv4 = z.address
            elif(z.family is socket.AF_INET6):
                interface.ipv6 = z.address.split("%")[0]                    # get address only
            else:
                interface.mac = z.address
        if((interface.mac == "00:00:00:00:00:00") and (interface.ipv6 == '::1')):   # linux loopback interface
            interface.mac = None
        if((interface.umetric_min is None) and (interface.umetric_max is None)):
            if((interface.mac is None) and (interface.ipv6 == '::1')):              # loopback interface
                interface.type = 0
                interface.umetric_min = 128849018880    # UMETRIC_MAX
                interface.umetric_max = 128849018880    # UMETRIC_MAX
                interface.fmu8_min = 255                # 0xff (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 255                # 0xff (converted UMETRIC to FMETRIC_U8_T)
            elif((interface.name[0] == 'e') or (interface.name[0] == 'E')):         # ethernet
                interface.type = 1
                interface.channel = 255
                interface.umetric_min = 1000000000      # DEF_DEV_BITRATE_MIN_LAN
                interface.umetric_max = 1000000000      # DEF_DEV_BITRATE_MAX_LAN
                interface.fmu8_min = 199                # 0xc7 (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 199                # 0xc7 (converted UMETRIC to FMETRIC_U8_T)
            else:
                interface.type = 2                                                  # wireless
                interface.umetric_min = 6000000         # DEF_DEV_BITRATE_MIN_WIFI
                interface.umetric_max = 56000000        # DEF_DEV_BITRATE_MAX_WIFI
                interface.fmu8_min = 139                # 0x8b (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 165                # 0xa5 (converted UMETRIC to FMETRIC_U8_T)
        if(interface.type == 0):
            interface.idx = 0
            iflist[0] = interface
        elif(id == -1):
            iflist.append(interface)
            dev_id = dev_id + 1
        else:
            iflist[id] = interface
    
    for interface in iflist:
        if(interface.type == 1):        # treat ethernet as the main connection
            return interface.mac, interface.idx         # use ethernet mac addr for local_id generation
    
    for interface in iflist:            # if no ethernet, use wireless connection
        if(interface.type == 2):
            return interface.mac, interface.idx         # use ethernet mac addr for local_id generation
    
    return -1

def global_id_gen():
    name = socket.gethostname()
    randomm = hex(random.randint(75557863725914323419136, 1208925819614629174706175))[2:]  # 1 w/ 19 0's in decimal
    glid = name + "." + randomm
    return glid

def local_id_gen(mac_addr):
    # | lid[0] | lid[1] | lid[2] | lid[3] |
    # | random | mac[3] | mac[4] | mac[5] |
    lid = random.randint(0,255) << 8
    lid = lid + int(mac_addr[9]+mac_addr[10], 16) << 8
    lid = lid + int(mac_addr[12]+mac_addr[13], 16) << 8
    lid = lid + int(mac_addr[15]+mac_addr[16], 16)

    return lid

def check_if_exists(object, object_list):
    if(type(object_list) == list):
        i = 0
        for x in object_list:
            if(object_list[i] == object):   # if the object is in the list, then it exists
                return i                    # index is returned
            i = i + 1
    else:
        if(object_list == [object]):
            return 0
        else:
            return -1
    return -1                               # object not found 


fhandler = frame_handler()      # holds information used later for sending the packet
local_ids = []                  # list of local_ids
global_ids = []    		        # list of global ids
description_list = []   	    # list of descriptions
local_list = []                 # list of local_nodes
link_keys = []                  # list of link_node_key
link_list = []                  # list of link_nodes
link_dev_list = []              # list of link_dev_nodes
dev_list = []                   # list of devices (includes loopback interface and inactive devices)

lomac, device_idx = get_interfaces(dev_list)    # gets the MAC address
loid = local_id_gen(lomac)                      # generates the local_id of the main node
globalid = global_id_gen()      		        # generates global id of the main node  
main_local = nodes.local_node(local_id = loid)  # main local_node (node of itself)
my_iid_repos = nodes.iid_repos()

main_name = globalid[:-21]			            # slice global id to get name part
main_pkid = globalid[-20:]			            # slide global id to get id part
main_description = nodes.description(name=main_name, pkid=main_pkid)  	# create description of the node 
main_orig = nodes.orig_node(global_id=globalid, desc=main_description)  # create orig node to store global id

local_ids.append(loid)                          # store in global local_id list
global_ids.append(globalid)     		        # store in global global_id list    
description_list.append(main_pkid)  		    # store pkid part of the description in global description list
local_list.append(main_local)                   # store in global local_node list



### DEBUGGING

def print_interfaces(iflist):
    for x in iflist:
        print(x.idx," - '",x.name,"':",sep='')
        if(x.ipv4 is not None):
            print("    IPv4:",'\t', x.ipv4)
        if(x.ipv6 is not None):
            print("    IPv6:",'\t', x.ipv6)
        if(x.mac is not None):
            print("    MAC:",'\t', x.mac)
        print("    type:",'\t', x.type)
        print("    active:",'\t', x.active)
        print("    channel:",'\t', x.channel)
        print("    umetric_min:", x.umetric_min)
        print("    umetric_max:", x.umetric_max)
        print("    fmu8_min:", x.fmu8_min)
        print("    fmu8_max:", x.fmu8_max)
    print()

def print_all(nodes):
    print("ALL NODES")
    i1 = 1
    for local in nodes:
        print("local_node", i1, ":")
        print("    local_id =", local.local_id)
        print("    link_tree:")
        i2 = 1
        for link in local.link_tree:
            print('\t\t', "    link_node", i2, ":")
            print('\t\t\t', "local =", link.local.local_id)
            print('\t\t\t', "key =", link.key)
            print('\t\t\t', "link_ip =", link.link_ip)
            print('\t\t\t', "pkt_time_max =", link.pkt_time_max)
            print('\t\t\t', "hello_time_max =", link.hello_time_max)
            print('\t\t\t', "hello_sqn_max =", link.hello_sqn_max)
            print('\t\t\t', "linkdev_list:")
            i3 = 1
            for lndev in link.lndev_list:
                print('\t\t\t\t\t\t', "link_dev_node", i3, ":")
                # print('\t\t\t\t\t\t', "    list_n = [...]")           # UNUSED
                print('\t\t\t\t\t\t', "    key:")           # dev node will add another level of depth
                print('\t\t\t\t\t\t\t', "link_node =", link.key)
                print('\t\t\t\t\t\t\t', "dev_node: ")
                print('\t\t\t\t\t\t\t', "    name = ", lndev.key.dev.name)
                print('\t\t\t\t\t\t\t', "    dev_idx = ", lndev.key.dev.idx)
                print('\t\t\t\t\t\t\t', "    ipv4 = ", lndev.key.dev.ipv4)
                print('\t\t\t\t\t\t\t', "    ipv6 = ", lndev.key.dev.ipv6)
                print('\t\t\t\t\t\t\t', "    mac = ", lndev.key.dev.mac)
                print('\t\t\t\t\t\t\t', "    type = ", lndev.key.dev.type)
                print('\t\t\t\t\t\t\t', "    active = ", lndev.key.dev.active)
                print('\t\t\t\t\t\t\t', "    channel = ", lndev.key.dev.channel)
                print('\t\t\t\t\t\t\t', "    umetric_min (fmu8_min) = ", lndev.key.dev.umetric_min, " (", hex(lndev.key.dev.fmu8_min),")",sep="")
                print('\t\t\t\t\t\t\t', "    umetric_max (fmu8_max) = ", lndev.key.dev.umetric_max, " (", hex(lndev.key.dev.fmu8_max),")",sep="")
                print('\t\t\t\t\t\t', "    tx_probe_umetric =", lndev.tx_probe_umetric)
                print('\t\t\t\t\t\t', "    timeaware_tx_probe =", lndev.timeaware_tx_probe)
                print('\t\t\t\t\t\t', "    rx_probe_record:")
                print('\t\t\t\t\t\t\t', "hello_sqn_max =", lndev.rx_probe_record.hello_sqn_max)
                print('\t\t\t\t\t\t\t', "hello_array =", lndev.rx_probe_record.hello_array)
                print('\t\t\t\t\t\t\t', "hello_sum =", lndev.rx_probe_record.hello_sum)
                print('\t\t\t\t\t\t\t', "hello_umetric =", lndev.rx_probe_record.hello_umetric)
                print('\t\t\t\t\t\t\t', "hello_time_max =", lndev.rx_probe_record.hello_time_max)
                print('\t\t\t\t\t\t', "    timeaware_rx_probe =", lndev.timeaware_rx_probe)
                # print('\t\t\t\t\t\t', "    tx_task_lists = []")       # UNUSED
                print('\t\t\t\t\t\t', "    link_adv_msg =", lndev.link_adv_msg)
                print('\t\t\t\t\t\t', "    pkt_time_max:", lndev.pkt_time_max)
                i3 = i3 + 1
                print()
            i2 = i2 + 1
        if(i1 >= 1):
            if local.best_rp_linkdev:
                print("    best_rp_linkdev = link_dev_key(link=", local.best_rp_linkdev[0].key.link.key, ", dev=", local.best_rp_linkdev[0].key.dev.idx, ")",sep='')
            else:
                print("    best_rp_linkdev = []")
            if local.best_tp_linkdev:            
                print("    best_tp_linkdev = link_dev_key(link=", local.best_tp_linkdev[0].key.link.key, ", dev=", local.best_tp_linkdev[0].key.dev.idx, ")",sep='')
            else:
                print("    best_tp_linkdev = []")
            if local.best_linkdev: 
                print("    best_linkdev = link_dev_key(link=", local.best_linkdev[0].key.link.key, ", dev=", local.best_linkdev[0].key.dev.idx, ")",sep='')
            else:
                print("    best_tp_linkdev = []")
            print("    neigh =", local.neigh)
            print("    packet_sqn =", local.packet_sqn)
            print("    packet_time =", local.packet_time)
            print("    packet_link_sqn_ref =", local.packet_link_sqn_ref)
            print("    link_adv_sqn =", local.link_adv_sqn)
            print("    link_adv_time =", local.link_adv_time)
            print("    link_adv_msgs =", local.link_adv_msgs)
            print("    link_adv_msg_for_me =", local.link_adv_msg_for_me)
            print("    link_adv_msg_for_him =", local.link_adv_msg_for_him)
            if local.link_adv:
                i4 = 0
                print("    link_adv:")
                for link in local.link_adv:
                    print("\t[", i4, "]    ", link, sep="")
                    i4 = i4 + 1
            else:
                print("    link_adv = []")
            print("    link_adv_dev_sqn_ref =", local.link_adv_dev_sqn_ref)
            print("    dev_adv_sqn =", local.dev_adv_sqn)
            print("    dev_adv_msgs =", local.dev_adv_msgs)
            if local.dev_adv:
                i5 = 0
                print("    dev_adv:")
                for dev in local.dev_adv:
                    print("\t[", i5, "]    ", dev, sep="")
                    i5 = i5 + 1
            else:
                print("    dev_adv = []")
            print("    rp_adv_time =", local.rp_adv_time)
            print("    rp_ogm_request_received =", local.rp_ogm_request_received)
            print("    orig_routes =", local.orig_routes)
        i1 = i1 + 1
        print()

def print_frames(frame_list, send_recv):
    i1 = 0
    if(send_recv == 0):
        print(">>> FRAMES TO SEND:")
    elif(send_recv == 1):
        print("<<< FRAMES RECEIVED:")
    for frame in frame_list:
        i2 = 0
        print("[", i1, "]  ", sep="", end='')
        if(type(frame) == frames.LINK_ADV):     # LINK_ADV
            print("LINK_ADV(frm_header=",frame.frm_header,", dev_sqn_no_ref=", frame.dev_sqn_no_ref, ", link_msgs:",sep="")
            for msg in frame.link_msgs:
                print("\t\t[", i2, "]  ", msg, sep="")
                i2 = i2 + 1
        elif(type(frame) == frames.LINK_REQ):   # LINK_REQ
            print(frame)
        elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
            print("DEV_ADV(frm_header=",frame.frm_header,", dev_sqn_no=", frame.dev_sqn_no, ", dev_msgs:",sep="")
            for msg in frame.dev_msgs:
                print("\t\t[", i2, "]  ", msg, sep="")
                i2 = i2 + 1
        elif(type(frame) == frames.DEV_REQ):    # DEV_REQ
            print(frame)
        elif(type(frame) == frames.RP_ADV):     # RP_ADV
            print("RP_ADV(frm_header=",frame.frm_header, ", rp_msgs:",sep="")
            for msg in frame.rp_msgs:
                print("\t\t[", i2, "]  ", msg, sep="")
                i2 = i2 + 1
        elif(type(frame) == frames.HELLO_ADV):  # HELLO_ADV
            print(frame)
        i1 = i1 + 1
    print()

def print_expected_lndevs(frame_handler):
    i = 0
    print("link_dev_nodes expected:")
    for lndev in frame_handler.lndevs_expected:
        print("[", i, "]  link_index = ", lndev[0], "\tlndev_index = ", lndev[1], sep="")
        i = i + 1
    print()



### PACKET HANDLING

def packet_received(self, ip6):
    ## NODE STRUCTURE INITIALIZATION
    active_known = 0
    active_devices = 0
    get_interfaces(dev_list)                    # get latest device list

    # check if the packet sender already has a local_node for the sender
    if(check_if_exists(self.header.local_id, local_ids) == -1):         # new local_node
        # create new local_node and link_node objects for the new node
        local = nodes.local_node(local_id = self.header.local_id)       # initialize new local_node
        
        # store new info in the global arrays
        local_ids.append(local.local_id)        # store in global local_id list
        local_list.append(local)                # store in global local_node list

    # # check if the local_node knows the link
    # print("knows link?", check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys))
    # print("search for:", nodes.link_node_key(self.header.local_id, self.header.dev_idx))
    # print("link_keys:", link_keys, '\n')

    if(check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys) == -1):
        # add the new link to the main local_node
        ln_key = nodes.link_node_key(self.header.local_id, self.header.dev_idx)
        ln = nodes.link_node(local = local_list[check_if_exists(self.header.local_id, local_ids)], key = ln_key, link_ip = ipaddress.ip_address(ip6))
        main_local.link_tree.append(ln)                                                     # add link to the main node
        local_list[check_if_exists(self.header.local_id, local_ids)].link_tree.append(ln)   # add link to the new node

        # store new info in the global arrays
        link_keys.append(ln_key)                # store in global link_node_key list
        link_list.append(ln)                    # store in global link_node list

        # add link_dev_nodes to the new link
        for dev in dev_list:
            if((dev.type != 0) and (dev.active == 1)):
                lndev = nodes.link_dev_node(key = nodes.link_dev_key(ln, dev), rx_probe_record= nodes.lndev_probe_record(hello_array = deque(127*[0], 127)))
                ln.lndev_list.append(lndev)     # add lndev to the the link's lndev_list
                link_dev_list.append(lndev)     # store in global link_dev_node list

    local_index = check_if_exists(self.header.local_id, local_ids)
    link_index = check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys)

    # check if lndevs are correct
    for lndev in link_list[link_index].lndev_list:
        if(lndev.key.dev.active == 1):
            active_known =  active_known + 1    # known active lndev
    for dev in dev_list:
        if((dev.type != 0) and (dev.active == 1)):
            active_devices = active_devices + 1
    if(active_known < active_devices):          # if there is a mismatch, then there is new active device
        for dev in dev_list:
            if((dev.type != 0) and (dev.active == 1) and (dev.idx > len(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))].lndev_list))):  
                lndev = nodes.link_dev_node(key = nodes.link_dev_key(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))], dev), rx_probe_record= nodes.lndev_probe_record(hello_array = deque(127*[0], 127)))
                link_list[link_index].lndev_list.append(lndev)                             # add lndev to the the link's lndev_list
                link_dev_list.append(lndev)     # store in global link_dev_node list
            
    main_local.pkt_received(self.header, 0)
    local_list[local_index].pkt_received(self.header, 1)


    ## FRAME ITERATION
    # print_frames(self.frames, 1)
    
    link_req = 0    # set to 1 if a REQ must be sent
    dev_req = 0     # set to 1 if a REQ must be sent
    rp = []         # holds rp_adv messages
    for frame in self.frames:
        if(type(frame) == frames.LINK_ADV):     # LINK_ADV
            main_local.link_adv_received(frame)
            local_list[local_index].link_adv_received(frame)
        elif(type(frame) == frames.LINK_REQ):   # LINK_REQ
            link_req = main_local.link_req_received(frame)
        elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
            main_local.dev_adv_received(frame)
            local_list[local_index].dev_adv_received(frame)
        elif(type(frame) == frames.DEV_REQ):    # DEV_REQ
            dev_req = main_local.dev_req_received(frame)
        elif(type(frame) == frames.RP_ADV):     # RP_ADV
            rp = frame.rp_msgs
            main_local.rp_adv_received(frame)
            local_list[local_index].rp_adv_received(frame)
        elif(type(frame) == frames.HELLO_ADV):  # HELLO_ADV
            if(link_index >= 0):
                link_list[link_index].hello_adv_received(frame)

    # match rp_adv msgs with link_adv msgs
    if rp:
        rp_index = 0
        for link_msg in main_local.link_adv:
            if(link_msg.peer_local_id == main_local.local_id):
                for lndev in link_list[link_index].lndev_list:
                    if((link_msg.peer_dev_index == lndev.key.dev.idx) and (lndev.key.dev.active == 1)):
                        lndev.tx_probe_umetric = (rp[rp_index].rp_127range / 127) * 128849018880    # UMETRIC_MAX
            rp_index = rp_index + 1

    # obtain timeaware tx/rx values and update best linkdevs
    for lndev in link_dev_list:                 # ADD: check if update is critical
        lndev.update_tx()
        lndev.update_rx()
        # assign best link_dev_node for transmitting
        if main_local.best_tp_linkdev:
            if(lndev.timeaware_tx_probe < main_local.best_tp_linkdev[0].timeaware_tx_probe):
                main_local.best_tp_linkdev[0] = lndev
        else:
            main_local.best_tp_linkdev = [lndev]
        # assign best link_dev_node for receiving
        if main_local.best_rp_linkdev:
            if(lndev.timeaware_rx_probe < main_local.best_rp_linkdev[0].timeaware_rx_probe):
                main_local.best_rp_linkdev[0] = lndev
        else:
            main_local.best_rp_linkdev = [lndev]
    # assign best link_dev_node
    if(main_local.best_rp_linkdev == main_local.best_tp_linkdev):
        main_local.best_linkdev = main_local.best_rp_linkdev
    else:
        main_local.best_linkdev = []


    ## FRAME SENDING (frame headers are to be set later)

    # check if DEV_REQ IS NEEDED 
    if(main_local.link_adv_dev_sqn_ref > local_list[local_index].dev_adv_sqn):
        outdated_dev = 1                        # set to 1 if dev is outdated
    elif(main_local.link_adv_dev_sqn_ref == local_list[local_index].dev_adv_sqn):
        outdated_dev = 0                        # set to 0 if dev is updated
    else:
        outdated_dev = -1

    # check if LINK_REQ IS NEEDED 
    if(main_local.packet_link_sqn_ref > local_list[local_index].link_adv_sqn):
        outdated_link = 1                       # set to 1 if link is outdated
    elif(main_local.packet_link_sqn_ref == local_list[local_index].link_adv_sqn):
        outdated_link = 0                       # set to 0 if link is updated
    else:
        outdated_link = -1

    # NON-PERIODICAL
    if(main_local.link_tree and (outdated_dev == 1)):
        fhandler.dev_req_ids.append(self.header.local_id)                   #### DEV_REQ 
        for dev in dev_list:                                                #### DEV_ADV
            if((dev.type != 0) and (dev.active == 1)):
                mac_converted = int(dev.mac[0]+dev.mac[1]+dev.mac[3]+dev.mac[4]+dev.mac[6]+dev.mac[7]+dev.mac[9]+dev.mac[10]+dev.mac[12]+dev.mac[13]+dev.mac[15]+dev.mac[16], 16)
                fhandler.dev_msgs2send.append(frames.DEV_ADV_msg(
                                dev_index=dev.idx,                              # uint8_t (0 - 255)
                                channel=dev.channel,                            # uint8_t (0 - 255)
                                trans_bitrate_min=dev.fmu8_min,                 # FMETRIC_U8_T
                                trans_bitrate_max=dev.fmu8_max,                 # FMETRIC_U8_T
                                local_ipv6=int(ipaddress.ip_address(dev.ipv6)), # int (hex)
                                mac_address=mac_converted                       # int (hex)
                                ))
    elif(main_local.link_tree and (dev_req == 1)):      # ADD: or if dev_list changed after calling get_interfaces
        for dev in dev_list:                                                #### DEV_ADV
            if((dev.type != 0) and (dev.active == 1)):
                mac_converted = int(dev.mac[0]+dev.mac[1]+dev.mac[3]+dev.mac[4]+dev.mac[6]+dev.mac[7]+dev.mac[9]+dev.mac[10]+dev.mac[12]+dev.mac[13]+dev.mac[15]+dev.mac[16], 16)
                fhandler.dev_msgs2send.append(frames.DEV_ADV_msg(
                                dev_index=dev.idx,                              # uint8_t (0 - 255)
                                channel=dev.channel,                            # uint8_t (0 - 255)
                                trans_bitrate_min=dev.fmu8_min,                 # FMETRIC_U8_T
                                trans_bitrate_max=dev.fmu8_max,                 # FMETRIC_U8_T
                                local_ipv6=int(dev.ipv6),                       # int (hex)
                                mac_address=mac_converted                       # int (hex)
                                ))

    if(main_local.link_tree and (outdated_link == 1)):
        fhandler.link_req_ids.append(self.header.local_id)                  #### LINK_REQ
        lndev_count = 0                                                     #### LINK_ADV (unsolicited)
        for lndev in link_list[link_index].lndev_list:
            if(lndev.key.dev.active == 1):
                fhandler.link_msgs2send.append(frames.LINK_ADV_msg(
                                trans_dev_index=lndev.key.dev.idx,              # uint8_t (0 - 255)
                                peer_dev_index=self.header.dev_idx,             # uint8_t (0 - 255)
                                peer_local_id=self.header.local_id              # uint32_t (0 - 4294967295)
                                ))
                fhandler.lndevs_possible.append([copy.deepcopy(link_index), copy.deepcopy(lndev_count)])
                main_local.link_adv_msg_for_him = len(fhandler.lndevs_possible) - 1
                local_list[local_index].link_adv_msg_for_him = len(fhandler.lndevs_possible) - 1
            lndev_count = lndev_count + 1
        fhandler.lndevs_expected.clear()
    elif(main_local.link_tree and (outdated_dev == 0) and (link_req == 1)):
        lndev_count = 0                                                     #### LINK_ADV
        for lndev in link_list[link_index].lndev_list:
            if(lndev.key.dev.active == 1):
                fhandler.link_msgs2send.append(frames.LINK_ADV_msg(
                                trans_dev_index=lndev.key.dev.idx,              # uint8_t (0 - 255)
                                peer_dev_index=self.header.dev_idx,             # uint8_t (0 - 255)
                                peer_local_id=self.header.local_id              # uint32_t (0 - 4294967295)
                                ))
                fhandler.lndevs_possible.append([copy.deepcopy(link_index), copy.deepcopy(lndev_count)])
                main_local.link_adv_msg_for_him = len(fhandler.lndevs_possible) - 1
                local_list[local_index].link_adv_msg_for_him = len(fhandler.lndevs_possible) - 1
            lndev_count = lndev_count + 1
        fhandler.lndevs_expected.clear()



### FRAME LIST FORMATION

def form_frames2send_list(frame_handler):	
    # PERIODICAL (every 500ms)
    frame_handler.frames2send.append(bmx.set_frame_header(frames.HELLO_ADV( #### HELLO_ADV
                            frm_header=frames.header(0,0,0,0),  
                            HELLO_sqn_no=frame_handler.hello_sqn                # uint16_t (0 - 65535)
                            )))
    

    # NON-PERIODICAL
    if frame_handler.dev_req_ids:                                           #### DEV_REQ
        for dev_req_id in frame_handler.dev_req_ids:
            frame_handler.frames2send.append(bmx.set_frame_header(frames.DEV_REQ(
                            frm_header=frames.header(0,0,0,0),
                            dest_local_id=dev_req_id                            # uint32_t (0 - 4294967295)
                            )))
    if frame_handler.dev_msgs2send:                                         #### DEV_ADV
        frame_handler.frames2send.append(bmx.set_frame_header(frames.DEV_ADV(
                            frm_header=frames.header(0,0,0,0),
                            dev_sqn_no=frame_handler.dev_sqn,                   # uint16_t (0 - 65535)
                            dev_msgs=frame_handler.dev_msgs2send
                            )))

    if frame_handler.link_msgs2send:                                        #### LINK_REQ
        for link_req_id in frame_handler.link_req_ids:
            frame_handler.frames2send.append(bmx.set_frame_header(frames.LINK_REQ(
                            frm_header=frames.header(0,0,0,0),
                            dest_local_id=link_req_id                           # uint32_t (0 - 4294967295)
                            )))
    if frame_handler.link_msgs2send:                                        #### LINK_ADV
        frame_handler.lndevs_expected = copy.deepcopy(frame_handler.lndevs_possible)
        frame_handler.frames2send.append(bmx.set_frame_header(frames.LINK_ADV(
                            frm_header=frames.header(0,0,0,0),
                            dev_sqn_no_ref=main_local.dev_adv_sqn,              # uint16_t (0 - 65535)
                            link_msgs=frame_handler.link_msgs2send
                            )))


    # PERIODICAL (every 500ms)
    if(frame_handler.lndevs_expected):                                      #### RP_ADV
        for lndev_info in frame_handler.lndevs_expected:
            lndev = link_list[lndev_info[0]].lndev_list[lndev_info[1]]
            lndev.update_tx()
            lndev.update_rx()
            if(lndev.key.dev.active == 1):
                rp_127_converted = round((lndev.timeaware_rx_probe * 127) / 128849018880)   # UMETRIC_MAX
                fhandler.rp_msgs2send.append(frames.RP_ADV_msg(
                                rp_127range=rp_127_converted,                   # 7 bits (0 - 127)
                                ogm_req=0                                       # 1 bit (0 / 1) (HAROLD)
                                ))
        frame_handler.frames2send.append(bmx.set_frame_header(frames.RP_ADV(
                            frm_header=frames.header(0,0,0,0),  
                            rp_msgs=frame_handler.rp_msgs2send
                            )))



################################################################
#########   COMPLETE FRAME HEADERS AND PACKET HEADER   #########
################################################################
# packer_header.bmx_version = 16
# packer_header.reserved = ???
# packer_header.pkt_len = (TRISTAN)
# packer_header.transmitterIID = ???
# packer_header.link_adv_sqn = fhandler.link_sqn
# packer_header.pkt_sqn = (TRISTAN)
# packer_header.local_id = main_local.local_id
# packer_header.dev_idx = device_idx

packet_header = bmx.packet_header(0,0,0,0,fhandler.link_sqn,0,main_local.local_id,device_idx)



################################################################
####################   CALL SEND FUNCTION   ####################
################################################################
packet = bmx.create_packet(packet_header, fhandler.frames2send) 		### created packet here is as bytes
bmx.send('ff02::2', 6240, 1, packet)



################################################################
####################   CALL AFTER SENDING   ####################
################################################################
fhandler.iterate()    # iterates all sqn that were sent
fhandler.reset()      # empties lists to be sent



### TESTING

# check if initialized properly
print_interfaces(dev_list)
print(lomac)
print(hex(loid))
print("local_id =", loid,'\n')

# check if the receive packet fills the data properly
recvdpacket, senderipv6 = bmx.listen('ff02::2', 6240)           #### CALLED RECEIVING FUNCTION HERE ####
packet = bmx.dissect_packet(recvdpacket)
print("this is the sender's ipv6 address: ", senderipv6[0])
print("this is the received packet:")
print(packet)
#print(senderipv6)
packet_received(packet, senderipv6[0])
# packet_received(packet2, '::1')
print_all(local_list)


# ### MANUAL TESTING
# fhead = frames.header(0,0,0,0)                      # default frame header

# # HELLO_ADV
# hello_frame1 = frames.HELLO_ADV(fhead,10)
# head1 = bmx.packet_header(0,0,0,0,0,4,11111,0)
# packet1 = bmx.packet(head1, [hello_frame1])

# # HELLO_ADV
# hello_frame3 = frames.HELLO_ADV(fhead,77)
# head3 = bmx.packet_header(0,0,0,0,0,2,242424,2)
# packet3 = bmx.packet(head3, [hello_frame3])

# packet_received(packet1, '::1')
# packet_received(packet3, '::2')
# # print_all(local_list)
# form_frames2send_list(fhandler)
# print_frames(fhandler.frames2send, 0)
# fhandler.iterate()
# fhandler.reset()

# # HELLO_ADV, LINK_ADV
# hello_frame2 = frames.HELLO_ADV(fhead,12)
# ln_msg2 = frames.LINK_ADV_msg(0,1,loid)
# ln_frame2 = frames.LINK_ADV(fhead, 1, [ln_msg2])
# head2 = bmx.packet_header(0,0,0,0,1,5,11111,0)
# packet2 = bmx.packet(head2, [hello_frame2, ln_frame2])

# # HELLO_ADV, LINK_ADV
# hello_frame4 = frames.HELLO_ADV(fhead,78)
# ln_msg4 = frames.LINK_ADV_msg(2,1,loid)
# ln_frame4 = frames.LINK_ADV(fhead, 1, [ln_msg4])
# head4 = bmx.packet_header(0,0,0,0,1,3,242424,2)
# packet4 = bmx.packet(head4, [hello_frame4, ln_frame4])

# packet_received(packet2, '::1')
# packet_received(packet4, '::2')
# print_all(local_list)
# print_expected_lndevs(fhandler)
# form_frames2send_list(fhandler)
# print_frames(fhandler.frames2send, 0)
# fhandler.iterate()
# fhandler.reset()

# # HELLO_ADV, RP_ADV
# hello_frame5 = frames.HELLO_ADV(fhead,13)
# rp_msg5 = frames.RP_ADV_msg(120,1)
# rp_frame5 = frames.RP_ADV(fhead, [rp_msg5])
# head5 = bmx.packet_header(0,0,0,0,1,6,11111,0)
# packet5 = bmx.packet(head5, [hello_frame5, rp_frame5])

# packet_received(packet5, '::1')
# # print_all(local_list)
# print_expected_lndevs(fhandler)
# form_frames2send_list(fhandler)
# print_frames(fhandler.frames2send, 0)
# fhandler.iterate()
# fhandler.reset()

# # NO FRAMES RECEIVED (TESTS PERIODICAL FRAMES)
# time.sleep(5)
# form_frames2send_list(fhandler)
# print_frames(fhandler.frames2send, 0)
