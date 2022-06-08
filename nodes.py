import ipaddress
from sys import getsizeof
import time
from collections import deque
from dataclasses import dataclass
import frames
import miscellaneous

# avl_tree link_tree

@dataclass
class link_node_key:
    local_id: int                       # local ID of the other node (LOCAL_ID_T)
    dev_idx: int                        # interface index of the other node (DEVADV_IDX_T)

@dataclass
class link_node:
    key: link_node_key                  # holds information about the other node

    link_ip: ipaddress.ip_address       # ip adress of the link (IPX_T)
    
    pkt_time_max: time                  # timeout value for packets (TIME_T)
    hello_time_max: time                # timeout value for the HELLO packet (TIME_T)

    hello_sqn_max: int                  # last sequence number (HELLO_SQN_T)

    local: list                         # local node (local_node)
    
    linkdev_list: list                  # list of link_devs (list_head)

@dataclass
class link_dev_key:
    link: link_node                     # link that uses the interface
    dev: list                           # **dev_node (look in ip.h)


# avl_tree link_dev_tree

@dataclass
class lndev_probe_record:
    hello_sqn_max: int = -1             # HELLO_SQN_T

    hello_array: deque = deque(128*[0], 128)
    hello_sum: int = 0
    hello_umetric: int = 0              # UMETRIC_T
    hello_time_max: time = 0            # TIME_T

    link_window: int = 48               # window size (48 default, 128 max)

    # TO DO: make a function that appends 0 when nothing is received after some time

    def update_record(self, update):
        if(update == 1):
            self.hello_array.append(1)
        elif(update == 0):
            self.hello_array.append(0)
        self.hello_sqn_max = self.hello_sqn_max + 1
        self.hello_time_max = time.localtime()
        current_time = time.strftime("%H:%M:%S", self.hello_time_max)
        print(current_time)

    def HELLO_received(self, sqn):
        if self.hello_sqn_max == -1:
            print("first received")
        if sqn == self.hello_sqn_max:
            self.update_record(1)
        elif(sqn > self.hello_sqn_max):
            while sqn != self.hello_sqn_max + 1:
                self.update_record(0)
            self.update_record(1)

    def get_link_qual(self):
        self.hello_sum = 0
        for x in range(self.link_window):
            self.hello_sum = self.hello_sum + self.hello_array[(len(self.hello_array) - 1) - x]
        self.hello_umetric = (self.hello_sum/self.link_window)*100

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
    list_n: list                        # list_node
    key: link_dev_key                   # holds information about the link and device

    tx_probe_umetric: int               # RP_ADV.rp_127range (UMETRIC_T)
    timeaware_tx_probe: int             # tx_probe_umetric which considers delay (UMETRIC_T) metrics.c
    rx_probe_record: lndev_probe_record # record that is used for link metric calculation
    timeaware_rx_probe: int             # rx_probe_record.hello_time_max which considers delay (UMETRIC_T) metrics.c

    tx_task_lists: list                 # array of scheduled frames (list_head - array[FRAME_TYPE_ARRSZ])
    link_adv_msg: int                   # frame counter of announced links (-1 if not announced)
    pkt_time_max: time                  # timeout value for packets (TIME_T)


# avl_tree local_tree

@dataclass
class local_node:
    local_id: int                       # LOCAL_ID_T
    link_tree: int                      # **avl_tree
    best_rp_linkdev: link_dev_node
    best_tp_linkdev: link_dev_node
    best_linkdev: link_dev_node
    neigh: list                         # neigh_node

    packet_sqn: int                     # PKT_SQN_T
    packet_time: time                   # TIME_T
    packet_link_sqn_ref: int            # LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)

    # from the latest LINK_ADV
    link_adv_sqn: int                   # sqn of the latest LINK_ADV (LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)
    link_adv_time: time                 # time of the latest LINK_ADV frame (TIME_T)
    link_adv_msgs: int                  #
    link_adv_msg_for_me: int
    link_adv_msg_for_him: int
    link_adv: frames.LINK_ADV           # msg_link_adv
    link_adv_dev_sqn_ref: int           # DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np)

    # from the latest DEV_ADV
    dev_adv_sqn: int                    # sqn of the latest DEV_ADV (DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np))
    dev_adv_msgs: int
    dev_adv: frames.DEV_ADV             # msg_dev_adv

    # from the latest RP_ADV
    rp_adv_time: time                   # time of the latest RP_ADV frame (TIME_T)
    rp_ogm_request_received: int        # IDM_T
    orig_routes: int


@dataclass
class metric_record:
    sqn_bit_mask: int                   # SQN_T (0 - 8191)

    clr: int                            # SQN_T (0 - 8191)
    set: int                            # SQN_T (0 - 8191)

    umetric: int                        # UMETRIC_T

@dataclass
class router_node:
    local_key: list                     # local_node

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
class orig_node:
    global_id: str                      # GLOBAL_ID_T (32 len) + PKID_T

    dhash_n: list                       # dhash_node
    desc: int                           # **description (MISSING???)
    desc_tlv_hash_tree: int             # **avl_tree

    updated_timestamp: time             # TIME_T

    desc_sqn: int                       # DESC_SQN_T (16 bits)

    ogm_sqn_range_min: int              # OGM_SQN_T (16 bits)
    ogm_sqn_range_size: int             # OGM_SQN_T (16 bits)

    primary_ip: ipaddress.ip_address    # IPX_T
    primary_ip_str: str                 # array[IPX_STR_LEN]
    blocked: int
    added: int

    path_metricalgo: int                # **host_metricalgo (HAROLD)

    ogm_sqn_max_received: int           # OGM_SQN_T (16 bits)

    ogm_sqn_next: int                   # OGM_SQN_T (16 bits)
    ogm_metric_next: int                # UMETRIC_T

    ogm_sqn_send: int                   # OGM_SQN_T (16 bits)

    metric_sqn_max_arr: int             # UMETRIC_T - *remove*

    rt_tree: int                        # **avl_tree

    best_rt_local: router_node          
    curr_rt_local: router_node
    curr_rt_linkdev: link_dev_node


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
    list_n: list                        # list_node

    ogm_advs: frames.OGM_ADV

    ogm_dest_field: list                # array[(OGM_DEST_ARRAY_BIT_SIZE/8)]
    ogm_dest_bytes: int

    aggregated_msgs: int

    sqn: int                            # AGGREG_SQN_T (8 bits)
    tx_attempt: int