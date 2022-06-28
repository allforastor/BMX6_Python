import ipaddress
from pickle import TRUE
import time
from sys import getsizeof
from collections import deque
from dataclasses import dataclass, field
import socket
import random

from numpy import append

import psutil
# import subprocess
import bmx
import nodes
import frames
# import miscellaneous

my_iid_repos = nodes.iid_repos()

# TESTING
ln_head = frames.header(0,0,0,0)
ln_msg = frames.LINK_ADV_msg(1,1,1)
ln_frame = frames.LINK_ADV(ln_head, 1, [ln_msg])
head = bmx.packet_header(0,0,0,0,0,0,11111,0)
packet = bmx.packet(head, [ln_frame])


# INITIALIZATION

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
            elif((interface.name[0] == 'e') or (interface.name[0] == 'E')):         # ethernet
                interface.type = 1
                interface.channel = 255
                interface.umetric_min = 1000000000      # DEF_DEV_BITRATE_MIN_LAN
                interface.umetric_max = 1000000000      # DEF_DEV_BITRATE_MAX_LAN
            else:
                interface.type = 2                                                  # wireless
                interface.umetric_min = 6000000         # DEF_DEV_BITRATE_MIN_WIFI
                interface.umetric_max = 56000000        # DEF_DEV_BITRATE_MAX_WIFI
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
    print()

def local_id_gen(mac_addr):
    # | lid[3] | lid[2] | lid[1] | lid[0] |
    # | mac[5] | mac[4] | mac[3] | random |
    lid = int(mac_addr[15]+mac_addr[16], 16) << 8
    lid = lid + int(mac_addr[12]+mac_addr[13], 16) << 8
    lid = lid + int(mac_addr[9]+mac_addr[10], 16) << 8
    lid = lid + random.randint(0,255)

    return lid

def check_if_exists(object, object_list):
    i = 0
    for x in object_list:
        if(object_list[i] == object):   # if the object is in the list, then it exists
            return i                    # index is returned
        i = i + 1
    return -1                           # object not found 


lomac = get_interfaces(dev_list)                # gets the MAC address
loid = local_id_gen(lomac)                      # generates the local_id of the main node
main_local = nodes.local_node(local_id = loid)  # main local_node (node of itself)

local_ids.append(loid)                          # store in global local_id list
local_list.append(main_local)                    # store in global local_node list

print_interfaces(dev_list)
print(lomac)
print(hex(loid))
print("local_id =", loid,'\n')


# PACKET HANDLING

def packet_received(self, ip6):
    # INITIALIZATION
    active_known = 0
    active_devices = 0
    get_interfaces(dev_list)                        # get latest device list

    # check if the packet sender already has a local_node for the sender
    if(check_if_exists(self.header.local_id, local_ids) == -1):         # new local_node
        # create new local_node and link_node objects for the new node
        local = nodes.local_node(local_id = self.header.local_id)       # initialize new local_node
        # local.link_tree.append(nodes.link_node(local = main_local))   # add link from new node to the main
        
        # store new info in the global arrays
        local_ids.append(local.local_id)        # store in global local_id list
        local_list.append(local)                 # store in global local_node list

    # check if the local_node knows the link
    if(check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), main_local.link_tree) == -1):
        # check if the link exists in the global link_node list
        if(check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys) >= 0):
            main_local.link_tree.append(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys)])
        else:                                                           # new link_node
            # add the new link to the main local_node
            ln_key = nodes.link_node_key(self.header.local_id, self.header.dev_idx)
            ln = nodes.link_node(local = local_list[check_if_exists(self.header.local_id, local_ids)], key = ln_key)
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

    # check if lndevs are correct
    for lndev in link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx), link_keys)].lndev_list:
        if(lndev.key.dev.active == 1):
            active_known =  active_known + 1        # known lndev_active
    for dev in dev_list:
        if((dev.type != 0) and (dev.active == 1)):
            active_devices = active_devices + 1
    if(active_known < active_devices):              # if there is a mismatch, then there is new active device
        for dev in dev_list:
            if((dev.type != 0) and (dev.active == 1) and (dev.idx > len(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))].lndev_list))):  
                lndev = nodes.link_dev_node(key = nodes.link_dev_key(link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))], dev))
                link_list[check_if_exists(nodes.link_node_key(self.header.local_id, self.header.dev_idx))].lndev_list.append(lndev)                             # add lndev to the the link's lndev_list
                link_dev_list.append(lndev)     # store in global link_dev_node list
            
    main_local.pkt_received(self.header)

    




    # FRAMES TO BE SENT

    # HELLO_ADV
    # RP_ADV
    if(main_local.packet_sqn != self.header.pkt_sqn):
        pass
        # send LINK_REQ
        # send unsolicited LINK_ADV
    # LINK_ADV

    #                                   # update packet-related class attributes
    #     for frame in self.frames:
    #         if(type(frame) == frames.HELLO_ADV):    # HELLO_ADV
    #             for ln in local.link_tree:
    #                 ln.frame_received(frame)
    #         elif(type(frame) == frames.LINK_ADV):   # LINK_ADV
    #             local.link_adv_received(frame)
    #             for msg in local.link_adv:
    #                 link_key = nodes.link_node_key(msg.peer_local_id, msg.peer_dev_index)
    #                 for link in local.link_tree:
    #                     if()
                
    #             for ln in local.link_tree:  # has to check first how many lndev_nodes there are and where to add
    #                 lndev_key = nodes.link_dev_key
    #                 ln.linkdev_list.append(nodes.link_dev_node(key = lndev_key))

    #         elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
    #             local.dev_adv_received(frame)  
    #         elif(type(frame) == frames.RP_ADV):     # RP_ADV
    #             local.rp_adv_received(frame)  
    #     node_list.append(local)
    #     # node_IIDs.append(local.local_id)
    
    
    
    
    # elif(exists > 0):               # existing node (UPDATES only)
    #     node_list[exists].pkt_received(self.header)                         # update packet-related class attributes
    #     for frame in self.frames:
    #         if(type(frame) == frames.LINK_ADV):     # LINK_ADV
    #             node_list[exists].link_adv_received(frame)                  # update frame-related class attributes
    #         elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
    #             node_list[exists].dev_adv_received(frame)  
    #         elif(type(frame) == frames.RP_ADV):     # RP_ADV
    #             node_list[exists].rp_adv_received(frame)


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
            print('\t\t\t', "local = local", i1)
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
                print('\t\t\t\t\t\t\t', "link_node = link_node", i2)
                print('\t\t\t\t\t\t\t', "dev_node: ")
                print('\t\t\t\t\t\t\t', "    name = ", lndev.key.dev.name)
                print('\t\t\t\t\t\t\t', "    dev_idx = ", lndev.key.dev.idx)
                print('\t\t\t\t\t\t\t', "    ipv4 = ", lndev.key.dev.ipv4)
                print('\t\t\t\t\t\t\t', "    ipv6 = ", lndev.key.dev.ipv6)
                print('\t\t\t\t\t\t\t', "    mac = ", lndev.key.dev.mac)
                print('\t\t\t\t\t\t\t', "    type = ", lndev.key.dev.type)
                print('\t\t\t\t\t\t\t', "    active = ", lndev.key.dev.active)
                print('\t\t\t\t\t\t\t', "    channel = ", lndev.key.dev.channel)
                print('\t\t\t\t\t\t\t', "    umetric_min = ", lndev.key.dev.umetric_min)
                print('\t\t\t\t\t\t\t', "    umetric_max = ", lndev.key.dev.umetric_max)
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
        print("    best_rp_linkdev =", local.best_rp_linkdev)
        print("    best_tp_linkdev =", local.best_tp_linkdev)
        print("    best_linkdev =", local.best_linkdev)
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


# TESTING

packet_received(packet, '::1')
print_all(local_list)
# print("IIDs:", node_IIDs)