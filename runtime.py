import ipaddress
import time
from sys import getsizeof
from collections import deque
from dataclasses import dataclass, field

from numpy import append
# import bmx
import nodes
import frames
import miscellaneous

node_list = []              # list of local_nodes
node_IIDs = []              # local_IIDs
rx_frames = []              # array of received (dataclass) frames

# initialize an avl_tree that will hold node structures

def check_if_existing(id):
    for x in node_IIDs:
        if(node_IIDs[x] == id):     # if the ID is in the node_IIDs list, then it exists
            return x
    return -1

def packet_received(self):
    # check if the HELLO_ADV frame is from a new node or not
    exists = check_if_existing(self.packet_header.local_id)
    if(exists == -1):               # new node (INITIALIZATION and UPDATES)
        local = nodes.local_node(local_id = self.packet_header.local_id)    # initialize local_node
        local.pkt_received(self.packet_header)                              # update packet-related class attributes
        for frame in self.frames:
            local.frame_received(frame)                                     # update frame-related class attributes

    elif(exists > 0):               # existing node (UPDATES only)
        node_list[exists].pkt_received(self.packet_header)                  # update packet-related class attributes
        for frame in self.frames:
            node_list[exists].frame_received(frame)                         # update frame-related class attributes
            