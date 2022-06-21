from importlib.machinery import OPTIMIZED_BYTECODE_SUFFIXES
import ipaddress
from sys import getsizeof
import time
from collections import deque
from dataclasses import dataclass, field
# import bmx
import frames
import miscellaneous


start_time = time.perf_counter()

# avl_tree local_tree

@dataclass
class local_node:
    local_id: int = -1                                                          # LOCAL_ID_T
    link_tree: list = field(default_factory=lambda:[])                          # avl_tree
    best_rp_linkdev: list = field(default_factory=lambda:[])                        # link_dev_node
    best_tp_linkdev: list = field(default_factory=lambda:[])                        # link_dev_node
    best_linkdev: list = field(default_factory=lambda:[])                           # link_dev_node
    neigh: list = field(default_factory=lambda:[])                                  # neigh_node

    packet_sqn: int = -1                                                        # PKT_SQN_T
    packet_time: time = 0                                                       # TIME_T
    packet_link_sqn_ref: int = -1                                               # LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)

    # from the latest LINK_ADV
    link_adv_sqn: int = -1                                                      # sqn of the latest LINK_ADV (LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)
    link_adv_time: time = 0                                                     # time of the latest LINK_ADV frame (TIME_T)
    link_adv_msgs: int = 0                                                      # number of msgs in the LINK_ADV frame
    link_adv_msg_for_me: int = 0                                                # number of msgs for this node
    link_adv_msg_for_him: int = 0                                               # number of msgs for other nodes
    link_adv: list = field(default_factory=lambda:[])                           # msg_link_adv (frames.LINK_ADV)
    link_adv_dev_sqn_ref: int = -1                                              # DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np)

    # from the latest DEV_ADV
    dev_adv_sqn: int = -1                                                       # sqn of the latest DEV_ADV (DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np))
    dev_adv_msgs: int = 0                                                       # number of msgs in the DEV_ADV frame
    dev_adv: list = field(default_factory=lambda:[])                            # msg_dev_adv (frames.DEV_ADV)

    # from the latest RP_ADV
    rp_adv_time: time = 0                                                       # time of the latest RP_ADV frame (TIME_T)
    rp_ogm_request_received: int = -1                                               # IDM_T
    orig_routes: int = -1                                                           # store originator
    
    def pkt_received(self, packet_header):
        self.packet_sqn = packet_header.pkt_sqn
        self.packet_time = (time.perf_counter() - start_time) * 1000            # bmx.start_time
        self.packet_link_sqn_ref = packet_header.link_adv_sqn

        for ln in self.link_tree:
            ln.pkt_update()

    def link_adv_received(self, frame):
        # LOCAL_NODE
        self.link_adv_sqn = self.packet_link_sqn_ref
        self.link_adv_time = (time.perf_counter() - start_time) * 1000      # bmx.start_time
        self.link_adv_msgs = 0
        self.link_adv_msg_for_me = 0
        self.link_adv_msg_for_him = 0
        self.link_adv.clear()
        for x in frame.link_msgs:
            self.link_adv_msgs = self.link_adv_msgs + 1
            if(x.peer_local_id == self.local_id):
                self.link_adv_msg_for_me = self.link_adv_msg_for_me + 1
            else:
                self.link_adv_msg_for_him = self.link_adv_msg_for_him + 1
            self.link_adv.append(x)
        self.link_adv_dev_sqn_ref = frame.dev_sqn_no_ref

        # LINK_NODE, LINK_NODE_KEY
        
        
    def dev_adv_received(self, frame):
        self.dev_adv_sqn = frame.dev_sqn_no
        self.dev_adv_msgs = 0
        self.dev_adv.clear()
        for x in frame.dev_msgs:
            self.dev_adv_msgs = self.dev_adv_msgs + 1
            self.dev_adv.append(x)  
        
    def rp_adv_received(self, frame):
        self.rp_adv_time = (time.perf_counter() - start_time) * 1000        # bmx.start_time
        req = 0
        for x in frame.rp_msgs:
            req = req + x.ogm_req
        if(req > 0):    # check if neighbor as well
            self.rp_ogm_request_received = 1
        else:
            self.rp_ogm_request_received = 0
        self.orig_routes = 0

    #def set_iid_offset_for_ogm_msg(self, OGM_ADV, neighbor):   # initialize iid offset for msgs # migrate to somewhere # works for 1 frame only # modified
    #    for msg in OGM_ADV.ogm_adv_msgs:
    #        if msg.iid_offset is None:  # ogm msg is in the originator, initialization # maybe change to < 0
    #            msg.iid_offset = 0
    #            iid = msg.iid_offset
    #        else:
    #            neighiid = msg.iid_offset   # ogm msg contains iid of the originator
    #            iid = neighbor.get_myIID4x_by_neighIID4x(neighiid)
    #            msg.iid_offset = iid
    #
    #    self.orig_routes = iid  # store iid value to local node



# avl_tree link_tree

@dataclass
class link_node_key:
    local_id: int = -1                                                          # local ID of the other node (LOCAL_ID_T)
    dev_idx: int = -1                                                           # interface index of the other node (DEVADV_IDX_T)

@dataclass
class link_node:
    local: local_node                                                           # local node connected to this link

    key: link_node_key = link_node_key(-1,-1)                                   # holds information about the other node
    link_ip: ipaddress.ip_address = ipaddress.ip_address('0.0.0.0')                 # ip address of the link (IPX_T)
    pkt_time_max: time = 0                                                      # timeout value for packets (TIME_T)
    hello_time_max: time = 0                                                    # timeout value for the HELLO packet (TIME_T)

    hello_sqn_max: int = -1                                                     # last sequence number (HELLO_SQN_T)
    
    linkdev_list: list = field(default_factory=lambda:[])                           # list of link_devs (list_head)

    def pkt_update(self):
        self.pkt_time_max = self.local.packet_time
        
    def frame_received(self, frame):
        if(type(frame) == frames.HELLO_ADV):
            self.hello_time_max = (time.perf_counter() - start_time) * 1000     # bmx.start_time
            self.hello_sqn_max = frame.HELLO_sqn_no



@dataclass
class dev_node:
    if_link: int                                                                # if_link_node
    if_llocal_addr: int                                                         # if_addr_node
    if_global_addr: int                                                         # if_addr_node

    hard_conf_changed: int
    soft_conf_changed: int
    autoIP6configured: int                                                      # net_key
    autoIP6ifindex: int
    active: int
    activate_again: int
    activate_cancelled: int
    tmp_flag_for_to_be_send_adv: int

    dev_adv_msg: int

    ifname_label: int                                                           # IFNAME_T
    ifname_device: int                                                          # IFNAME_T

    # dummy_lndev: link_dev_node
    
    llip_key: int                                                               # dev_ip_key
    mac: int                                                                    # MAC_T

    ip_llocal_str: str                                                          # array[IPX_STR_LEN]
    ip_global_str: str                                                          # array[IPX_STR_LEN]
    ip_brc_str: str                                                             # array[IPX_STR_LEN]

    llocal_unicast_addr: int                                                    # sockaddr_storage
    tx_netwbrc_addr: int                                                        # sockaddr_storage

    unicast_sock: int
    rx_mcast_sock: int
    rx_fullbrc_sock: int

    link_hello_sqn: int                                                         # HELLO_SQN_T

    tx_task_lists: list                                                         # array of scheduled frames (list_head - array[FRAME_TYPE_ARRSZ])
    tx_task_interval_tree: int                                                  # avl_tree

    announce: int

    linklayer_conf: int
    linklayer: int

    channel_conf: int
    channel: int

    umetric_min_conf: int                                                       # UMETRIC_T
    umetric_min: int                                                            # UMETRIC_T

    umetric_max_conf: int                                                       # UMETRIC_T
    umetric_max: int                                                            # UMETRIC_T

    global_prefix_conf_: int                                                    # net_key
    llocal_prefix_conf_: int                                                    # net_key
    
    plugin_data: list                                                           # void*


@dataclass
class link_dev_key:
    link: int = 0 #link_node = link_node()                                               # link that uses the interface
    # dev: dev_node = dev_node()                                                # outgoing interface for transmiting (dev_node)


# avl_tree link_dev_tree

@dataclass
class lndev_probe_record:
    hello_sqn_max: int = -1                                                     # last sequence number (HELLO_SQN_T)

    hello_array: deque = deque(128*[0], 128)
    hello_sum: int = 0                                                          # number of HELLO_ADVs received within the window
    hello_umetric: int = 0                                                      # UMETRIC_T
    hello_time_max: time = 0                                                    # timeout value for the HELLO packet (TIME_T)

    link_window = 48                                                       # sliding window size (48 default, 128 max)

    # TO DO: make a function that appends 0 when nothing is received after some time

    def update_record(self, update):
        if(update == 1):
            self.hello_array.append(1)
        elif(update == 0):
            self.hello_array.append(0)
        self.hello_sqn_max = self.hello_sqn_max + 1

    def HELLO_received(self, sqn):
        # if self.hello_sqn_max == -1:
        #     print("first received")
        if sqn == self.hello_sqn_max:
            self.update_record(1)
        elif(sqn > self.hello_sqn_max):
            while sqn != self.hello_sqn_max + 1:
                self.update_record(0)
            self.update_record(1)
        self.hello_time_max = (time.perf_counter() - start_time) * 1000         # bmx.start_time
        print(self.hello_time_max)

    def get_link_qual(self):
        self.hello_sum = 0
        for x in range(self.hello_array):
            self.hello_sum = self.hello_sum + self.hello_array[x]
        # for x in range(self.link_window):
        #     self.hello_sum = self.hello_sum + self.hello_array[(len(self.hello_array) - 1) - x]
        self.hello_umetric = (self.hello_sum/self.link_window) * 128849018880   # UMETRIC_MAX

# # lndev_probe_record testing functions
# lndev = lndev_probe_record(hello_array = deque(8*[0], 8), link_window = 4)
# print(lndev.hello_array)
# lndev.update_record(1)
# lndev.update_record(1)
# print(lndev.hello_array)
# lndev.HELLO_received(3)
# print(lndev.hello_array)
# lndev.get_link_qual()
# print(lndev.hello_umetric)

@dataclass
class link_dev_node:
    list_n: list = field(default_factory=lambda:[])                             # list_node
    key: link_dev_key = link_dev_key()                                          # holds information about the link and device

    tx_probe_umetric: int = 0                                                   # RP_ADV.rp_127range (UMETRIC_T)
    timeaware_tx_probe: int = 0                                                 # tx_probe_umetric which considers delay (UMETRIC_T) metrics.c
    rx_probe_record: lndev_probe_record = lndev_probe_record()                  # record that is used for link metric calculation
    timeaware_rx_probe: int = 0                                                 # rx_probe_record.hello_umetric which considers delay (UMETRIC_T) metrics.c

    tx_task_lists: list = field(default_factory=lambda:[])                      # array of scheduled frames (list_head - array[FRAME_TYPE_ARRSZ])
    link_adv_msg: int = -1                                                      # frame counter of announced links (-1 if not announced)
    pkt_time_max: time = 0                                                      # timeout value for packets (TIME_T)

    def update_tx(self, umetric):                                               # every RP_ADV received
        rp_adv_time = link_dev_key.link.local.rp_adv_time
        self.tx_probe_umetric = umetric
        if(((time.perf_counter() - start_time) * 1000) - rp_adv_time < 3000):       # TP_ADV_DELAY_TOLERANCE (3s)
            self.timeaware_tx_probe = self.tx_probe_umetric
        elif(((time.perf_counter() - start_time) * 1000) - rp_adv_time < 20000):    # TP_ADV_DELAY_RANGE (20s)
            self.timeaware_tx_probe = self.tx_probe_umetric * (20000 - ((time.perf_counter() - start_time) * 1000)/20000)

    def update_rx(self):                                                        # every HELLO_ADV received
        hello_adv_time = self.rx_probe_record.hello_time_max
        if(((time.perf_counter() - start_time) * 1000) - hello_adv_time < 3000):    # RP_ADV_DELAY_TOLERANCE (3s)
            self.timeaware_rx_probe = self.rx_probe_record.hello_umetric
        elif(((time.perf_counter() - start_time) * 1000) - hello_adv_time < 20000): # RP_ADV_DELAY_RANGE (20s)
            self.timeaware_rx_probe = self.rx_probe_record.hello_umetric * (20000 - ((time.perf_counter() - start_time) * 1000)/20000)

    




@dataclass
class metric_record:
    sqn_bit_mask: int = 0               # SQN_T (0 - 8191)

    clr: int = 0                        # SQN_T (0 - 8191)
    set: int = 0                        # SQN_T (0 - 8191)

    umetric: int = 0                    # UMETRIC_T

@dataclass
class router_node:
    local_key: local_node               # local_node

    metric_red: metric_record
    ogm_sqn_last: int                   # OGM_SQN_T
    ogm_umetric_last: int               # UMETRIC_T

    path_metric_best: int               # UMETRIC_T
    path_linkdev_best: link_dev_node


# avl_tree neigh_trees

@dataclass
class iid_ref:
    myIID4x: int                         # IID_T
    referred_by_neigh_timestamp_sec: int        

@dataclass
class iid_repos:
    # arr_size: int
    # min_free: int
    # max_free: int
    # tot_used: int
    arr: dict                           # maps IID to its hash 
    ref: iid_ref

    def print_repos(self):              # prints repository table contents
        print(self.arr)
        print("-----")

@dataclass
class neigh_node:
    neigh_node_key: list                # neigh_node
    dhash_n: list                       # dhash_node                 

    local: list                         # local_node

    neighIID4me: int                    # IID_T

    neighIID4x_repos: iid_repos

    ogm_new_aggregation_received: time  # TIME_T
    ogm_aggregation_cleared_max: int    # AGGREG_SQN_T
    ogm_aggregations_not_acked: list    # array[AGGREG_ARRAY_BYTE_SIZE]
    ogm_aggregations_received: list     # array[AGGREG_ARRAY_BYTE_SIZE]

    def get_myIID4x_by_neighIID4x(self, neighIID4x):
        myIID4x = self.neighIID4x_repos.arr[neighIID4x]

        try:
            return myIID4x
        except KeyError:
            return -1
        
    def get_node_by_neighIID4x(self, neigh, neighIID4x):    # added by harold from repos.py
        if neigh.get_myIID4x_by_neighIID4x(neighIID4x) == -1:
            # send HASH_REQ message
            print("Neighbor IID unknown. Sending Hash Request")
        else:
            myIID4x = neigh.get_myIID4x_by_neighIID4x(neighIID4x)

            if self.arr[myIID4x] == KeyError:
                # send DESC_REQ message
                print("Node description unknown. Sending Description Request")
            else:
                print("Retrieved hash from local IID repository: " + self.arr[myIID4x])

# avl_tree orig_tree

@dataclass
class description_hash:
    u8: int                             # array[HASH_SHA1_LEN] - [20]
    u32: int                            # array[HASH_SHA1_LEN/4] - [20/4]

@dataclass
class desc_tlv_hash_node:
    prev_hash: description_hash         # SHA1_T
    curr_hash: description_hash         # SHA1_T
    test_hash: description_hash         # SHA1_T
    tlv_type: int
    test_changed: int
    prev_changed: int
        
@dataclass  
class host_metricalgo:
    fmetric_u16_min: float  # FMETRIC_U16_T

    umetric_min: int  # UMETRIC_T
    algo_type: int  # ALGO_T
    flags: int  # uint16_t
    algo_rp_exp_numerator: int  # uint8_t
    algo_rp_exp_divisor: int  # uint8_t
    algo_tp_exp_numerator: int  # uint8_t
    algo_tp_exp_divisor: int  # uint8_t

    window_size: int  # uint8_t
    lounge_size: int  # uint8_t
    regression: int  # uint8_t
    # fast_regression: int   # uint8_t
    # fast_regression_impact: int    # uint8_t
    hystere: int  # uint8_t
    hop_penalty: int  # uint8_t
    late_penalty: int  # uint8_t

@dataclass
class orig_node:    
    global_id: int   # GLOBAL_ID_T (32 len) + PKID_T # default -1

    dhash_n: list  # dhash_node   # default dhash_node
    desc: int  # **description (MISSING???)
    desc_tlv_hash_tree: int  # **avl_tree

    updated_timestamp: time  # TIME_T   # last time this orig node's description was updated # default

    desc_sqn: int  # DESC_SQN_T (16 bits)

    ogm_sqn_range_min: int  # OGM_SQN_T (16 bits) # default -1
    ogm_sqn_range_size: int  # OGM_SQN_T (16 bits)  # default -1

    primary_ip: ipaddress.ip_address    # ip of link (IPX_T), default = ipaddress.ip_address('0.0.0.0')
    primary_ip_str: str  # array[IPX_STR_LEN]
    blocked: int
    added: int

    path_metricalgo: host_metricalgo  # **host_metricalgo (HAROLD) # modified

    ogm_sqn_max_received: int  # OGM_SQN_T (16 bits)

    ogm_sqn_next: int  # OGM_SQN_T (16 bits)
    ogm_metric_next: int  # UMETRIC_T

    ogm_sqn_send: int  # OGM_SQN_T (16 bits)

    metric_sqn_max_arr: int  # UMETRIC_T - *remove*

    rt_tree: int  # **avl_tree

    best_rt_local: router_node
    curr_rt_local: router_node
    curr_rt_linkdev: link_dev_node

    def ack_ogm_frame(self, frame):  # function to ack ogm frames by creating ogm ack msgs
        if type(frame) == frames.OGM_ADV:  # check if ogm adv is received
            ack_msg1 = frames.OGM_ACK_msg  # assign 2 ack msgs with sqn number of ogm frame
            ack_msg2 = frames.OGM_ACK_msg
            ack_msg1.agg_sqn_no = frame.agg_sqn_no
            ack_msg2.agg_sqn_no = frame.agg_sqn_no
            self.ogm_sqn_max_received = frame.agg_sqn_no
            self.ogm_sqn_next = frame.agg_sqn_no + 1
            self.ogm_sqn_send = frame.agg_sqn_no

        return ack_msg1, ack_msg2


# avl_tree dhash_tree
# avl_tree dhash_invalid_tree

@dataclass
class dhash_node:
    dhash: description_hash             

    referred_by_me_timestamp: time      # TIME_T

    neigh: list                         # neigh_node

    myIID4origL: int                    # IID_T
    
    orig_n: list                        # orig_node


# avl_tree blacklisted_tree

@dataclass
class black_node:
    dhash: list                         # description_hash

@dataclass
class throw_node:
    list_n: list                        # list_node
    addr: int
    netmask: int

@dataclass
class ogm_aggreg_node:
    #list_n: list = field(default_factory=lambda: [])  # list_node  # excluded for now, uncomment whenever relevant

    ogm_advs: list = = field(default_factory=lambda: [])

    ogm_dest_field: list = = field(default_factory=lambda: [])   # array[(OGM_DEST_ARRAY_BIT_SIZE/8)]  # store dests where ogm frame is supposed to be sent
    #ogm_dest_bytes: int                # removed from original

    aggregated_msgs_sqn_no: int = 0    # originally aggregated_msgs # deviated from original

    sqn: int = 0  # AGGREG_SQN_T (8 bits)
    #tx_attempt: int                    # removed from original
    
    def set_sqn_no_ogmframes_and_msgs(self):  # set aggregated seq no for ogm frame and sqn_no for msgs 
        for frame in self.ogm_advs:     # n^2 time complexity
            for msgs in frame.ogm_adv_msgs:
                if msgs.ogm_sqn_no < 0:     # check if the msg has not yet been given a sqn number (-1 is default)
                    msgs.ogm_sqn_no = self.aggregated_msgs_sqn_no
                    self.aggregated_msgs_sqn_no += 1

                else:
                    continue    # if msgs already given a sqn number, ignore

            if frame.agg_sqn_no < 0:   # check if the frame has not yet been given a sqn number (-1 is default)
                frame.agg_sqn_no = self.sqn
                self.sqn += 1

            else:
                continue    # # if frame already given a sqn number, ignore

                
