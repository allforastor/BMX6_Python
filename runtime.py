import ipaddress
from pickle import TRUE
import time
from sys import getsizeof
from collections import deque
from dataclasses import dataclass, field
import socket

from numpy import append

import psutil
import subprocess
# import bmx
# import nodes
# import frames
# import miscellaneous


# # TESTING
# ln_head = frames.header(0,0,0,0)
# ln_msg = frames.LINK_ADV_msg(1,1,1)
# ln_frame = frames.LINK_ADV(ln_head, 1, [ln_msg])
# head = bmx.packet_header(0,0,0,0,0,0,0,0)
# packet = bmx.packet(head, [ln_frame])

# node_list = []                  # list of local_nodes
# local_IDs = []                  # list of local_ids
# # node_IIDs = []                # list of local_IIDs (can be substituted by however Geom does)
# # rx_packets = []               # array of received (dataclass) packets


# # BMX6 PROCESS

#     # loid = local_id_generation()
#     # node_list.append(nodes.local_node(local_id = loid))
#     # local_IDs.append(id)

# def check_if_existing(id):
#     for x in local_IDs:
#         if(local_IDs[x] == id):     # if the ID is in the node_IIDs list, then it exists
#             return x
#     return -1

# def packet_received(self):
#     # check if the HELLO_ADV frame is from a new node or not
#     exists = check_if_existing(self.header.local_id)
#     if(exists == -1):               # new node (INITIALIZATION and UPDATES)
#         local = nodes.local_node(local_id = self.header.local_id)    # initialize local_node
#         local.pkt_received(self.header)                              # update packet-related class attributes
#         for frame in self.frames:
#             if(type(frame) == frames.HELLO_ADV):    # HELLO_ADV
#                 for ln in local.link_tree:
#                     ln.frame_received(frame)
#             elif(type(frame) == frames.LINK_ADV):   # LINK_ADV
#                 local.link_adv_received(frame)
#                 for msg in local.link_adv:
#                     link_key = nodes.link_node_key(msg.peer_local_id, msg.peer_dev_index)
#                     local.link_tree.append(nodes.link_node(local = local, key = link_key))
                
#                 for ln in local.link_tree:  # has to check first how many lndev_nodes there are and where to add
#                     lndev_key = nodes.link_dev_key
#                     ln.linkdev_list.append(nodes.link_dev_node(key = lndev_key))

#             elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
#                 local.dev_adv_received(frame)  
#             elif(type(frame) == frames.RP_ADV):     # RP_ADV
#                 local.rp_adv_received(frame)  
#         node_list.append(local)
#         # node_IIDs.append(local.local_id)
#     elif(exists > 0):               # existing node (UPDATES only)
#         node_list[exists].pkt_received(self.header)                         # update packet-related class attributes
#         for frame in self.frames:
#             if(type(frame) == frames.LINK_ADV):     # LINK_ADV
#                 node_list[exists].link_adv_received(frame)                  # update frame-related class attributes
#             elif(type(frame) == frames.DEV_ADV):    # DEV_ADV
#                 node_list[exists].dev_adv_received(frame)  
#             elif(type(frame) == frames.RP_ADV):     # RP_ADV
#                 node_list[exists].rp_adv_received(frame)


# def print_all(nodes):
#     i1 = 1
#     for local in nodes:
#         print("local_node", i1, ":")
#         print("    local_id =", local.local_id)
#         print("    link_tree:")
#         i2 = 1
#         for link in local.link_tree:
#             print('\t\t', "    link_node", i2, ":")
#             print('\t\t\t', "local = ...")
#             print('\t\t\t', "key =", link.key)
#             print('\t\t\t', "link_ip =", link.link_ip)
#             print('\t\t\t', "pkt_time_max =", link.pkt_time_max)
#             print('\t\t\t', "hello_time_max =", link.hello_time_max)
#             print('\t\t\t', "hello_sqn_max =", link.hello_sqn_max)
#             print('\t\t\t', "linkdev_list:")
#             i3 = 1
#             for lndev in link.linkdev_list:
#                 print('\t\t\t\t\t\t', "link_dev_node", i3, ":")
#                 print('\t\t\t\t\t\t', "    list_n = [...]")             # idk what this is yet
#                 print('\t\t\t\t\t\t', "    key =", lndev.key)           # dev node will add another level of depth
#                 print('\t\t\t\t\t\t', "    tx_probe_umetric =", lndev.tx_probe_umetric)
#                 print('\t\t\t\t\t\t', "    timeaware_tx_probe =", lndev.timeaware_tx_probe)
#                 print('\t\t\t\t\t\t', "    rx_probe_record:")
#                 print('\t\t\t\t\t\t\t', "hello_sqn_max:", lndev.rx_probe_record.hello_sqn_max)
#                 print('\t\t\t\t\t\t\t', "hello_array: [...]")
#                 print('\t\t\t\t\t\t\t', "hello_sum:", lndev.rx_probe_record.hello_sum)
#                 print('\t\t\t\t\t\t\t', "hello_umetric:", lndev.rx_probe_record.hello_umetric)
#                 print('\t\t\t\t\t\t\t', "hello_time_max:", lndev.rx_probe_record.hello_time_max)
#                 print('\t\t\t\t\t\t', "    timeaware_rx_probe =", lndev.timeaware_rx_probe)
#                 print('\t\t\t\t\t\t', "    tx_task_lists = []")
#                 print('\t\t\t\t\t\t', "    link_adv_msg =", lndev.link_adv_msg)
#                 print('\t\t\t\t\t\t', "    pkt_time_max:", lndev.pkt_time_max)
#                 i3 = i3 + 1
#             i2 = i2 + 1
#         print("    best_rp_linkdev =", local.best_rp_linkdev)
#         print("    best_tp_linkdev =", local.best_tp_linkdev)
#         print("    best_linkdev =", local.best_linkdev)
#         print("    neigh =", local.neigh)
#         print("    packet_sqn =", local.packet_sqn)
#         print("    packet_time =", local.packet_time)
#         print("    packet_link_sqn_ref =", local.packet_link_sqn_ref)
#         print("    link_adv_sqn =", local.link_adv_sqn)
#         print("    link_adv_time =", local.link_adv_time)
#         print("    link_adv_msgs =", local.link_adv_msgs)
#         print("    link_adv_msg_for_me =", local.link_adv_msg_for_me)
#         print("    link_adv_msg_for_him =", local.link_adv_msg_for_him)
#         print("    link_adv =", local.link_adv)
#         print("    link_adv_dev_sqn_ref =", local.link_adv_dev_sqn_ref)
#         print("    dev_adv_sqn =", local.dev_adv_sqn)
#         print("    dev_adv_msgs =", local.dev_adv_msgs)
#         print("    dev_adv =", local.dev_adv)
#         print("    rp_adv_time =", local.rp_adv_time)
#         print("    rp_ogm_request_received =", local.rp_ogm_request_received)
#         print("    orig_routes =", local.orig_routes)
#         i1 = i1 + 1


# # TESTING

# packet_received(packet)
# print_all(node_list)
# # print("IIDs:", node_IIDs)

@dataclass
class net_info:
    name: str = None
    ipv4: ipaddress.ip_address = None
    ipv6: ipaddress.ip_address = None
    mac: str = None
    channel: int = 0
    umetric_min: int = None
    umetric_max: int = None

netlist = []
for x, y in psutil.net_if_addrs().items():
    interface = net_info(name = x)
    for z in y:
        # print('\t', z, type(z))
        # print('\t\t', z.family)
        # print('\t\t', z.address)
        if((z.family is psutil.AF_LINK) or (z.family is socket.AF_PACKET)):
            interface.mac = z.address
        elif(z.family is socket.AF_INET):
            interface.ipv4 = z.address
        elif(z.family is socket.AF_INET6):
            interface.ipv6 = z.address
    if((interface.mac == "00:00:00:00:00:00") and (interface.ipv6 == '::1')):    # linux loopback interface
        interface.mac = None
    if((interface.umetric_min is None) and (interface.umetric_max is None)):
        if((interface.mac is None) and (interface.ipv6 == '::1')):              # loopback interface
            interface.umetric_min = 128849018880    # UMETRIC_MAX
            interface.umetric_max = 128849018880    # UMETRIC_MAX
        elif((interface.name[0] == 'e') or (interface.name[0] == 'E')):         # ethernet
            interface.channel = 255
            interface.umetric_min = 1000000000      # DEF_DEV_BITRATE_MIN_LAN
            interface.umetric_max = 1000000000      # DEF_DEV_BITRATE_MAX_LAN
        else:                                                                   # wireless
            interface.umetric_min = 6000000         # DEF_DEV_BITRATE_MIN_WIFI
            interface.umetric_max = 56000000        # DEF_DEV_BITRATE_MAX_WIFI

    netlist.append(interface)
    # print(interface, '\n')

for x in netlist:
    print("'",x.name,"':",sep='')
    if(x.ipv4 != None):
        print("    IPv4:",'\t', x.ipv4)
    if(x.ipv6 != None):
        print("    IPv6:",'\t', x.ipv6)
    if(x.mac != None):
        print("    MAC:",'\t', x.mac)
    print("    channel:",'\t', x.channel)
    print("    umetric_min:", x.umetric_min)
    print("    umetric_max:", x.umetric_max)

# devices = subprocess.check_output(['netsh','wlan','show','network'])
# devices = devices.decode('ascii')
# devices = devices.replace("\r","")

# print(subprocess.check_output("iwconfig"))
# print(psutil.net_if_addrs())