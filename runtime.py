import ipaddress
from os import link
from pickle import TRUE
import time
from sys import getsizeof
from collections import deque
from dataclasses import dataclass, field
import socket
import random

from numpy import append, empty

import psutil
# import subprocess
import bmx
import nodes
import frames
# import miscellaneous

# my_iid_repos = nodes.iid_repos()



## TEST VALUES
fhead = frames.header(0,0,0,0)
ln_msg = frames.LINK_ADV_msg(1,1,1)
ln_frame = frames.LINK_ADV(fhead, 0, [ln_msg])
rp_msg = frames.RP_ADV_msg(127,1)
rp_msg2 = frames.RP_ADV_msg(7,1)
rp_frame = frames.RP_ADV(fhead, [rp_msg])
rp_frame2 = frames.RP_ADV(fhead, [rp_msg2])
hello_frame = frames.HELLO_ADV(fhead,10)
head = bmx.packet_header(0,0,0,0,1,0,11111,0)
head2 = bmx.packet_header(0,0,0,0,1,1,11112,1)
# packet = bmx.packet(head, [ln_frame, hello_frame, rp_frame])
packet = bmx.packet(head, [hello_frame])
packet2 = bmx.packet(head2, [hello_frame, rp_frame2])



## INITIALIZATION

hello_sqn = random.randint(0,65535)     # add 1 every send of HELLO_ADV
link_sqn = 1                            # add 1 every send of LINK_ADV
dev_sqn = 1                             # add 1 every send of DEV_ADV

frames2send = []                        # list of friends to be sent
rp_msgs2send = []
rp_msgs_index = 0
# link_msgs2send = []
# dev_msgs2send = []

local_ids = []                  # list of local_ids
local_list = []                 # list of local_nodes
link_keys = []                  # list of link_node_key
link_list = []                  # list of link_nodes
# link_dev_keys = []              # list of link_dev_keys
link_dev_list = []              # list of link_dev_nodes
dev_list = []                   # list of devices (includes loopback interface and inactive devices)
# node_IIDs = []                # list of local_IIDs (can be substituted by however Geom does)

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
            # print('\t', z, type(z))
            # print('\t\t', z.family)
            # print('\t\t', z.address)
            if(z.family is socket.AF_INET):
                interface.ipv4 = z.address
            elif(z.family is socket.AF_INET6):
                interface.ipv6 = z.address
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
        # print(interface, '\n')
    
    for interface in iflist:
        if(interface.type == 1):
            return interface.mac                                        # use ethernet mac addr for local_id generation
    return -1

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
    return -1                           # object not found 

lomac = get_interfaces(dev_list)                # gets the MAC address
loid = local_id_gen(lomac)                      # generates the local_id of the main node
# main_local = nodes.local_node(local_id = loid)  # main local_node (node of itself)
main_local = nodes.local_node(local_id = 1)     # main local_node (node of itself)

local_ids.append(loid)                          # store in global local_id list
local_list.append(main_local)                   # store in global local_node list

print_interfaces(dev_list)
print(lomac)
print(hex(loid))
print("local_id =", loid,'\n')



## PACKET HANDLING

def packet_received(self, ip6):
    ## NODE STRUCTURE INITIALIZATION
    active_known = 0
    active_devices = 0
    get_interfaces(dev_list)                    # get latest device list

    # check if the packet sender already has a local_node for the sender
    if(check_if_exists(self.header.local_id, local_ids) == -1):         # new local_node
        # create new local_node and link_node objects for the new node
        local = nodes.local_node(local_id = self.header.local_id)       # initialize new local_node
        # local.link_tree.append(nodes.link_node(local = main_local))   # add link from new node to the main
        
        # store new info in the global arrays
        local_ids.append(local.local_id)        # store in global local_id list
        local_list.append(local)                # store in global local_node list

    # check if the local_node knows the link
    print("knows link?", check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys))
    print("comparison:", nodes.link_node_key(self.header.local_id, self.header.dev_idx))
    print("link_keys:", link_keys)

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
                lndev = nodes.link_dev_node(key = nodes.link_dev_key(ln, dev))
                ln.lndev_list.append(lndev)     # add lndev to the the link's lndev_list
                link_dev_list.append(lndev)     # store in global link_dev_node list

    link_index = check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys)

    # check if lndevs are correct
    for lndev in link_list[link_index].lndev_list:
        if(lndev.key.dev.active == 1):
            active_known =  active_known + 1    # known lndev_active
    for dev in dev_list:
        if((dev.type != 0) and (dev.active == 1)):
            active_devices = active_devices + 1
    if(active_known < active_devices):          # if there is a mismatch, then there is new active device
        for dev in dev_list:
            if((dev.type != 0) and (dev.active == 1) and (dev.idx > len(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))].lndev_list))):  
                lndev = nodes.link_dev_node(key = nodes.link_dev_key(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))], dev))
                link_list[link_index].lndev_list.append(lndev)                             # add lndev to the the link's lndev_list
                link_dev_list.append(lndev)     # store in global link_dev_node list
            
    main_local.pkt_received(self.header)


    ## FRAME ITERATION
    link_req = 0    # set to 1 if a REQ must be sent
    dev_req = 0     # set to 1 if a REQ must be sent
    rp = []         # holds rp_adv messages
    for frame in self.frames:
        if(type(frame) == frames.LINK_ADV):     # LINK_ADV
            main_local.link_adv_received(frame)
        elif(type(frame) == frames.LINK_REQ):   # LINK_REQ
            link_req = main_local.link_req_received(frame)
        elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
            main_local.dev_adv_received(frame)
        elif(type(frame) == frames.DEV_REQ):    # DEV_REQ
            dev_req = main_local.dev_req_received(frame)
        elif(type(frame) == frames.RP_ADV):     # RP_ADV
            rp = frame.rp_msgs
            main_local.rp_adv_received(frame)

        elif(type(frame) == frames.HELLO_ADV):  # HELLO_ADV
            if(link_index >= 0):
                link_list[link_index].hello_adv_received(frame)
                for lndev in link_list[link_index].lndev_list:
                    if(lndev.key.dev.active == 1):
                        lndev.hello_adv_received(frame)

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
    for lndev in link_dev_list:                 # TO DO: check if update is critical
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


    ## FRAME SENDING
    # frame headers are to be set later

    # check if DEV_REQ IS NEEDED 
    if(main_local.link_adv_dev_sqn_ref > main_local.dev_adv_sqn):
        outdated_dev = 1                       # set to 1 if dev is outdated
    elif(main_local.link_adv_dev_sqn_ref == main_local.dev_adv_sqn):
        outdated_dev = 0                       # set to 0 if dev is updated
    else:
        outdated_dev = -1

    # check if LINK_REQ IS NEEDED 
    if(main_local.packet_link_sqn_ref > main_local.link_adv_sqn):
        outdated_link = 1                       # set to 1 if link is outdated
    elif(main_local.packet_link_sqn_ref == main_local.link_adv_sqn):
        outdated_link = 0                       # set to 0 if link is updated
    else:
        outdated_link = -1




    # NON-PERIODICAL

    if(main_local.link_tree and (outdated_dev == 1)):
        frames2send.append(frames.DEV_REQ(                      #### DEV_REQ
                            frm_header=frames.header(0,0,0,0),
                            dest_local_id=self.header.local_id))    # uint32_t (0 - 4294967295)
        # ADD: unsolicited DEV_ADV after done with format below
    elif(main_local.link_tree and (dev_req == 1)): # ADD: or ifdev_list changed after calling get_interfaces
        global dev_sqn
        devs = []                                               #### DEV_ADV
        for dev in dev_list:
            if((dev.type != 0) and (dev.active == 1)):
                mac_converted = int(dev.mac[0]+dev.mac[1]+dev.mac[3]+dev.mac[4]+dev.mac[6]+dev.mac[7]+dev.mac[9]+dev.mac[10]+dev.mac[12]+dev.mac[13]+dev.mac[15]+dev.mac[16], 16)
                devs.append(frames.DEV_ADV_msg(
                                dev_index=dev.idx,                  # uint8_t (0 - 255)
                                channel=dev.channel,                # uint8_t (0 - 255)
                                trans_bitrate_min=dev.fmu8_min,     # FMETRIC_U8_T  # TO-DO
                                trans_bitrate_max=dev.fmu8_max,     # FMETRIC_U8_T  # TO-DO
                                local_ipv6=int(dev.ipv6),           # int (hex)
                                mac_address=mac_converted           # int (hex)
                                ))
        frames2send.append(frames.DEV_ADV(
                            frm_header=frames.header(0,0,0,0),
                            dev_sqn_no=dev_sqn,                     # uint16_t (0 - 65535)
                            dev_msgs=devs
                            ))
        dev_sqn = dev_sqn + 1


    if(main_local.link_tree and (outdated_link == 1)):
        global link_sqn
        frames2send.append(frames.LINK_REQ(                     #### LINK_REQ
                            frm_header=frames.header(0,0,0,0),
                            dest_local_id=self.header.local_id))
        links = []                                              #### LINK_ADV (unsolicited)
        for lndev in link_dev_list:
            links.append(frames.LINK_ADV_msg(
                                trans_dev_index=lndev.key.dev.idx,  # uint8_t (0 - 255)
                                peer_dev_index=self.header.dev_idx, # uint8_t (0 - 255)
                                peer_local_id=self.header.local_id  # uint32_t (0 - 4294967295)
                                ))
        frames2send.append(frames.LINK_ADV(
                            frm_header=frames.header(0,0,0,0),
                            dev_sqn_no_ref=main_local.dev_adv_sqn,  # uint16_t (0 - 65535)
                            link_msgs=links
                            ))
        link_sqn = link_sqn + 1
    elif(main_local.link_tree and (outdated_dev == 0) and (link_req == 1)):
        links = []                                              #### LINK_ADV
        for lndev in link_dev_list:
            links.append(frames.LINK_ADV_msg(
                                trans_dev_index=lndev.key.dev.idx,  # uint8_t (0 - 255)
                                peer_dev_index=self.header.dev_idx, # uint8_t (0 - 255)
                                peer_local_id=self.header.local_id  # uint32_t (0 - 4294967295)
                                ))
        frames2send.append(frames.LINK_ADV(
                            frm_header=frames.header(0,0,0,0),
                            dev_sqn_no_ref=main_local.dev_adv_sqn,  # uint16_t (0 - 65535)
                            link_msgs=links
                            ))
        link_sqn = link_sqn + 1


    # PERIODICAL
    if(main_local.link_tree and (outdated_dev == 0) and (outdated_link == 0)):
        for lndev in link_dev_list:                             #### RP_ADV
            rp_127_converted = round((lndev.timeaware_tx_probe * 127) / 128849018880)    # UMETRIC_MAX
            rp_msgs2send.append(frames.RP_ADV_msg(
                                rp_127range=rp_127_converted,       # 7 bits (0 - 127)
                                ogm_req=0                           # 1 bit (0 / 1) (HAROLD)
                                ))


# PERIODICAL (every 500ms)
frames2send.append(frames.HELLO_ADV(                            #### HELLO_ADV
                            frm_header=frames.header(0,0,0,0),  
                            HELLO_sqn_no=hello_sqn))                # uint16_t (0 - 65535)
hello_sqn = hello_sqn + 1

if main_local.link_tree:    # send only if the node has links
    frames2send.append(frames.RP_ADV(                           #### RP_ADV
                            frm_header=frames.header(0,0,0,0),  
                            rp_msgs=rp_msgs2send))

## AFTER SENDING
# rp_msgs2send.clear()
# link_msgs2send.clear()
# dev_msgs2send.clear()


    
## DEBUGGING

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
                # print('\t\t\t\t\t\t', "    list_n = [...]")             # not needed
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
                print('\t\t\t\t\t\t\t', "hello_array = [...]")
                print('\t\t\t\t\t\t\t', "hello_sum =", lndev.rx_probe_record.hello_sum)
                print('\t\t\t\t\t\t\t', "hello_umetric =", lndev.rx_probe_record.hello_umetric)
                print('\t\t\t\t\t\t\t', "hello_time_max =", lndev.rx_probe_record.hello_time_max)
                print('\t\t\t\t\t\t', "    timeaware_rx_probe =", lndev.timeaware_rx_probe)
                print('\t\t\t\t\t\t', "    tx_task_lists = []")
                print('\t\t\t\t\t\t', "    link_adv_msg =", lndev.link_adv_msg)
                print('\t\t\t\t\t\t', "    pkt_time_max:", lndev.pkt_time_max)
                i3 = i3 + 1
                print()
            i2 = i2 + 1
        if(i1 == 1):
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
            print("    link_adv =", local.link_adv)
            print("    link_adv_dev_sqn_ref =", local.link_adv_dev_sqn_ref)
            print("    dev_adv_sqn =", local.dev_adv_sqn)
            print("    dev_adv_msgs =", local.dev_adv_msgs)
            print("    dev_adv =", local.dev_adv)
            print("    rp_adv_time =", local.rp_adv_time)
            print("    rp_ogm_request_received =", local.rp_ogm_request_received)
            print("    orig_routes =", local.orig_routes)
        i1 = i1 + 1
        print()

def print_frames(frame_list):
    i1 = 1
    print("FRAMES TO SEND:")
    for frame in frame_list:
        i2 = 1
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


## TESTING

packet_received(packet, '::1')
print_all(local_list)
print_frames(frames2send)
# packet_received(packet2, '::1')
# print_all(local_list)
# print(local_ids)
# print(link_keys)
# print(link_list)