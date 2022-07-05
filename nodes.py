import time
import socket
import ipaddress
from sys import getsizeof
from weakref import ref
from random import randint
from collections import deque
from dataclasses import dataclass, field
from importlib.machinery import OPTIMIZED_BYTECODE_SUFFIXES
import frames

start_time = time.perf_counter()


@dataclass
class local_node:
    local_id: int = -1                                                          # LOCAL_ID_T
    link_tree: list = field(default_factory=lambda:[])                          # avl_tree
    best_rp_linkdev: list = field(default_factory=lambda:[])                    # link_dev_node
    best_tp_linkdev: list = field(default_factory=lambda:[])                    # link_dev_node
    best_linkdev: list = field(default_factory=lambda:[])                       # link_dev_node
    neigh: list = field(default_factory=lambda:[])                                  # neigh_node (GEOM)

    packet_sqn: int = -1                                                        # PKT_SQN_T
    packet_time: time = 0                                                       # TIME_T
    packet_link_sqn_ref: int = -1                                                # LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)

    # from the latest LINK_ADV
    link_adv_sqn: int = -1                                                       # sqn of the latest LINK_ADV (LINKADV_SQN_T (0 - 255)(frames.LINK_ADV.dev_sqn_no_ref)
    link_adv_time: time = 0                                                     # time of the latest LINK_ADV frame (TIME_T)
    link_adv_msgs: int = -1                                                     # number of msgs in the LINK_ADV frame
    link_adv_msg_for_me: int = -1                                               # index of the msg for this node
    link_adv_msg_for_him: int = -1                                              # index of msg for the other node
    link_adv: list = field(default_factory=lambda:[])                           # msg_link_adv (frames.LINK_ADV)
    link_adv_dev_sqn_ref: int = -1                                               # DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np)

    # from the latest DEV_ADV
    dev_adv_sqn: int = -1                                                        # sqn of the latest DEV_ADV (DEVADV_SQN_T (0 - 255)(frames.DEV_ADV.dev_sqn_np))
    dev_adv_msgs: int = -1                                                      # number of msgs in the DEV_ADV frame
    dev_adv: list = field(default_factory=lambda:[])                            # msg_dev_adv (frames.DEV_ADV)

    # from the latest RP_ADV
    rp_adv_time: time = 0                                                       # time of the latest RP_ADV frame (TIME_T)
    rp_ogm_request_received: int = -1                                               # IDM_T (HAROLD)
    orig_routes: int = -1                                                           # store originator (HAROLD)
    
    def pkt_received(self, packet_header, copy_only):
        self.packet_sqn = packet_header.pkt_sqn
        self.packet_time = (time.perf_counter() - start_time) * 1000
        self.packet_link_sqn_ref = packet_header.link_adv_sqn

        if(copy_only == 0):
            for ln in self.link_tree:
                if((ln.key.local_id == packet_header.local_id) and (ln.key.dev_idx == packet_header.dev_idx)):
                    ln.pkt_time_max = self.packet_time
                    for lndev in ln.lndev_list:
                        if(lndev.key.dev.active == 1):
                            lndev.pkt_time_max = self.packet_time

    def link_adv_received(self, frame):
        self.link_adv_sqn = self.packet_link_sqn_ref
        self.link_adv_time = self.packet_time
        self.link_adv_msgs = 0
        self.link_adv_msg_for_me = -1
        self.link_adv.clear()
        for x in frame.link_msgs:
            if(x.peer_local_id == self.local_id):
                self.link_adv_msg_for_me = self.link_adv_msgs
            self.link_adv_msgs = self.link_adv_msgs + 1
            self.link_adv.append(x)
        # self.link_adv_msg_for_him = 0     # SET THIS WHEN SENDING
        self.link_adv_dev_sqn_ref = frame.dev_sqn_no_ref
        if(self.dev_adv_sqn == -1):         # copy first dev_sqn_no_ref
            self.dev_adv_sqn = frame.dev_sqn_no_ref

    def dev_adv_received(self, frame):
        self.dev_adv_sqn = frame.dev_sqn_no
        self.dev_adv_msgs = 0
        self.dev_adv.clear()
        for x in frame.dev_msgs:
            self.dev_adv_msgs = self.dev_adv_msgs + 1
            self.dev_adv.append(x)  
    
    def dev_req_received(self, frame):
        if(frame.dest_local_id == self.local_id):
            return 1
        return 0 
        
    def link_req_received(self, frame):
        if(frame.dest_local_id == self.local_id):
            return 1
        return 0

    def rp_adv_received(self, frame):
        self.rp_adv_time = self.packet_time
        # self.rp_ogm_request_received = 0    # (HAROLD)
        # self.orig_routes = 0                # (HAROLD)

@dataclass
class link_node_key:
    local_id: int = -1                                                          # local ID of the other node (LOCAL_ID_T)
    dev_idx: int = -1                                                           # interface index of the other node (DEVADV_IDX_T)

@dataclass
class link_node:
    local: local_node = None                                                    # local node connected to this link

    key: link_node_key = link_node_key(-1,-1)                                   # holds information about the other node
    link_ip: ipaddress.ip_address = ipaddress.ip_address('0.0.0.0')                 # ip address of the link (IPX_T)
    pkt_time_max: time = 0                                                      # timeout value for packets (TIME_T)
    hello_time_max: time = 0                                                    # timeout value for the HELLO packet (TIME_T)

    hello_sqn_max: int = -1                                                     # last sequence number (HELLO_SQN_T)
    
    lndev_list: list = field(default_factory=lambda:[])                             # list of link_devs (list_head)

    def pkt_update(self):
        self.pkt_time_max = self.local.packet_time

    def hello_adv_received(self, frame):
        self.hello_time_max = self.pkt_time_max
        self.hello_sqn_max = frame.HELLO_sqn_no
        for lndev in self.lndev_list:
            if(lndev.key.dev.active == 1):
                lndev.hello_adv_received(frame)

@dataclass
class dev_node:         # our own implementation
    name: str = None
    idx: int = 0
    ipv4: ipaddress.ip_address = None
    ipv6: ipaddress.ip_address = None
    mac: str = None
    type: int = None
    active: int = None
    channel: int = 0
    umetric_min: int = None
    umetric_max: int = None
    fmu8_min: int = None
    fmu8_max: int = None

@dataclass
class link_dev_key:
    link: link_node = None                                             # link that uses the interface
    dev: dev_node = None                                               # outgoing interface for transmiting

@dataclass
class lndev_probe_record:
    hello_sqn_max: int = None                                                     # last sequence number (HELLO_SQN_T)

    hello_array: deque = deque(127*[0], 127)
    hello_sum: int = 0                                                          # number of HELLO_ADVs received within the window
    hello_umetric: int = 0                                                      # UMETRIC_T
    hello_time_max: time = 0                                                    # timeout value for the HELLO packet (TIME_T)

    link_window = 48                                                       # sliding window size (48 default, 128 max)

    def update_record(self, update):
        if(update == 1):
            self.hello_array.append(1)
        elif(update == 0):
            self.hello_array.append(0)
        self.hello_sqn_max = self.hello_sqn_max + 1

    def hello_adv_received(self, sqn):
        skipped = 0
        if self.hello_sqn_max is None:
            self.hello_sqn_max = sqn - 1
            self.update_record(1)
        else:
            while sqn != self.hello_sqn_max + 1:
                if(skipped == 127):                     # entire array is 0, so just skip to the 1
                    break
                elif(self.hello_sqn_max + 1 == 65535):  # loop once the uint16_t (2 bytes) limit is reached
                    self.hello_sqn_max = -1
                self.update_record(0)
                skipped = skipped + 1
            self.update_record(1)
        self.hello_sqn_max = sqn

    def get_link_qual(self):
        self.hello_sum = 0
        for x in range(self.link_window):
            self.hello_sum = self.hello_sum + self.hello_array[(len(self.hello_array) - 1) - x]
        self.hello_umetric = (self.hello_sum/self.link_window) * 128849018880   # UMETRIC_MAX

@dataclass
class link_dev_node:
    # list_n: list = field(default_factory=lambda:[])                           # UNUSED, just links it to the link_node's lndev_list
    key: link_dev_key = link_dev_key()                                          # holds information about the link and device

    tx_probe_umetric: int = 0                                                   # RP_ADV.rp_127range (UMETRIC_T)
    timeaware_tx_probe: int = 0                                                 # tx_probe_umetric which considers delay (UMETRIC_T) metrics.c
    rx_probe_record: lndev_probe_record = lndev_probe_record()                  # record that is used for link metric calculation
    timeaware_rx_probe: int = 0                                                 # rx_probe_record.hello_umetric which considers delay (UMETRIC_T) metrics.c

    # tx_task_lists: list = field(default_factory=lambda:[])                    # UNUSED, array of scheduled frames (list_head - array[FRAME_TYPE_ARRSZ])
    link_adv_msg: int = -1                                                      # frame counter of announced links (-1 if not announced)
    pkt_time_max: time = 0                                                      # timeout value for packets (TIME_T)

    def hello_adv_received(self, frame):
        self.rx_probe_record.hello_adv_received(frame.HELLO_sqn_no)
        self.rx_probe_record.get_link_qual()
        self.rx_probe_record.hello_time_max = self.key.link.pkt_time_max

    def update_tx(self):                                                        # every RP_ADV received
        rp_adv_time = self.key.link.local.rp_adv_time
        if(((time.perf_counter() - start_time) * 1000) - rp_adv_time < 3000):       # TP_ADV_DELAY_TOLERANCE (3s)
            self.timeaware_tx_probe = self.tx_probe_umetric
        elif(((time.perf_counter() - start_time) * 1000) - rp_adv_time < 20000):    # TP_ADV_DELAY_RANGE (20s)
            self.timeaware_tx_probe = self.tx_probe_umetric * ((20000 - (((time.perf_counter() - start_time) * 1000) - rp_adv_time))/20000)

    def update_rx(self):                                                        # every HELLO_ADV received
        hello_adv_time = self.rx_probe_record.hello_time_max
        if((((time.perf_counter() - start_time) * 1000)) - hello_adv_time < 3000):    # RP_ADV_DELAY_TOLERANCE (3s)
            self.timeaware_rx_probe = self.rx_probe_record.hello_umetric
        elif((((time.perf_counter() - start_time) * 1000)) - hello_adv_time < 20000): # RP_ADV_DELAY_RANGE (20s)
            self.timeaware_rx_probe = self.rx_probe_record.hello_umetric * ((20000 - ((((time.perf_counter() - start_time) * 1000)) - hello_adv_time))/20000)

    




@dataclass
class metric_record:
    sqn_bit_mask: int = 0               # SQN_T (0 - 8191)

    clr: int = 0                        # SQN_T (0 - 8191)
    set: int = 0                        # SQN_T (0 - 8191)

    umetric: int = 0                    # UMETRIC_T

@dataclass
class router_node:
    local_key: local_node = local_node()    # local_node

    metric_red: metric_record = metric_record()
    ogm_sqn_last: int = -1                  # latest sqn number of ogm frame # default 0
    ogm_umetric_last: int = -1              # UMETRIC_T

    path_metric_best: int = -1             # UMETRIC_T
    path_linkdev_best: link_dev_node = link_dev_node()

    def update_self(self, frame):    # update fields upon receiving OGM_ADV # called everytime receives OGM ADV
        if type(frame) == frames.OGM_ADV:
            diff = frame.agg_sqn_no - self.ogm_sqn_last
            if diff > 1:      # make sure no ogm frame is missed
                print("Warning! Missed an OGM_ADV frame!")
            self.ogm_sqn_last = frame.agg_sqn_no

@dataclass
class description:  
    name: str = None                    # hostname of node
    pkid: str = None                    # random part of global ID
    code_version: int = None            # replaced with git revision
    capabilites: int = 0                # Supposed to be used to indicate future capabilities of the BMX6 process.
    desc_sqn_no: int = -1               # starts at random
    ogm_min_sqn_no: int = 0             # default 0
    ogm_range: int = 65535              # default 0 to 2^16
    trans_interval: int = 500           # time interval for every packet sent in ms, default is 0.5s
    ext_len: int = None                 # not sure if this will be used
    ext_frm: int = None                 # not sure if this will be used
            
@dataclass
class description_hash:                 # UNUSED; simplified to string within dhash_node instead
    u8: int                             # array[HASH_SHA1_LEN] - [20]
    u32: int 

# avl_tree dhash_tree
# avl_tree dhash_invalid_tree

@dataclass
class dhash_node:
    dhash: str                               # description_hash              
    referred_by_me_timestamp: time = 0      # TIME_T

    # neigh: neigh_node = None

    myIID4orig: int = 0                     # myIID of this dhash_node
    # orig_n: list                            # orig_node

# avl_tree neigh_trees

@dataclass
class iid_ref:                                  # node's own iid_ref consistent in my_iid_repos and neigh_repos
    myIID4x: int                                # IID in this node (main_local) vocabulary
    referred_by_neigh_timestamp_sec: time = 0   # TIME_T

@dataclass
class iid_entry:
    u8: int                                     # can be either the neighIID or my IID
    ref: iid_ref                                # universal iid_ref
    dhash_n: dhash_node

@dataclass
class iid_repos:
    arr_size: int = 0                                       # number of allocated array fields
    min_free: int = 0                                       # first unused index from beginning of the list
    max_free: int = 0                                       # first unused index after the last used field
    tot_used: int = 0                                       # total number of used keys; len()
    
    arr: list = field(default_factory = lambda:[])          # serves as the table of iid_entry objects

    def print_repos(self):                                  # prints repository table contents
        print("arr_size: ", self.arr_size)
        print("min_free: ", self.min_free)
        print("max_free: ", self.max_free)
        print("tot_used: ", self.tot_used)
        print("u8 | myIID4x | dhash")
        for entry in self.arr:
            try:
                print(entry.u8, "|", entry.ref.myIID4x, "|", entry.dhash_n.dhash)
            except AttributeError:
                if (entry.ref is None):
                    print(entry.u8, "|", 0, "|", entry.dhash_n.dhash)
                elif (entry.dhash_n is None):
                    print(entry.u8, "|", entry.ref.myIID4x, "|", 0)
        print("----")

    def get_iid_entry(self, iid):                           # prints repository table contents
        existing = None
        for entry in self.arr:
            if (entry.u8 == iid):
                existing = entry
        return existing

    def purge_repos(self):
        self.arr_size = 0
        self.min_free = 0
        self.max_free = 0
        self.tot_used = 0
        self.arr.clear()

    def iid_free(self, iid):       # freeing the list item of the given IID
        # deleting the iid_entry object from the list
        entry_num = (self.get_iid_entry(iid)).u8 - 1
        del self.arr[entry_num]

        # re-setting attributes
        self.min_free = min(self.min_free, iid)
        if (self.max_free == iid + 1):
            self.max_free = iid
        self.tot_used -= 1


    def iid_set(self, IIDpos, myIID4x, dhnode):
        # setting iid_repos attributes
        self.tot_used += 1
        self.max_free = max(self.max_free, IIDpos + 1)
        self.arr_size = self.max_free - 1

        min = self.min_free        
        if (min == IIDpos):
            min += 1
            for min in range (self.arr_size + 1):           # increment until next free position
                if (self.get_iid_entry(min) is None):
                    break
        self.min_free = self.max_free
        
        # adding iid_entry object into list
        if (myIID4x):
            ref = iid_ref(myIID4x,(time.perf_counter() - start_time) * 1000)
            self.arr.insert(IIDpos-1,iid_entry(IIDpos, ref, None))
        else:
            ref = iid_ref(0,0)
            self.arr.insert(IIDpos-1, iid_entry(IIDpos, ref, dhnode))
            dhnode.referred_by_me_timestamp = (time.perf_counter() - start_time) * 1000


    def iid_new_myIID4x(self, dhnode):                      # called by my_iid_repos only; adds new IID entry given a dhash_node
        if (self.arr_size >= self.tot_used):
            rand_iid = randint(0,self.arr_size)
            mid = max(1,rand_iid)                           # minimum iid value: IID_MIN_USED = 1

            for mid in range(1,self.arr_size + 1):
                mid += 1
                if (self.get_iid_entry(mid) is None):
                    break
                elif (mid >= self.arr_size):
                    mid = 1                                 # return to minimum iid value            
        else:
            mid = self.min_free

        self.iid_set(mid,0,dhnode)
        # return mid  # function should be called as dhash_node->myIID4orig = iid_new_myIID4x(dhnode);

    def iid_get_node_by_myIID4x(self, myIID4x):   # to be called ONLY by my_iid_repos
        if (self.max_free <= myIID4x):
            return None

        dhn = (self.get_iid_entry(myIID4x)).dhash_n

        # possible error if (dhn && !dhn->on), meaning myIID4x invalidated
        
        return dhn

@dataclass
class neigh_node:
    neigh_node_key: int = 0                                                     # index of this node in local_node's neigh list
    dhash_n: int = 0                                                            # corresponding myIID containing the corresponding dhash_node in my_iid_repos                
    local: local_node = None                                                    # local_node

    neighIID4me: int = 0                                                        # neighIID that neighbor uses for itself
    neighIID4x_repos: iid_repos = iid_repos()                                   # repository according to the neighbor's vocabulary

    ogm_new_aggregation_received: time = 0                                      # TIME_T
    ogm_aggregation_cleared_max: int = 0                                        # AGGREG_SQN_T  # ack'd
    ogm_aggregations_not_acked: list = field(default_factory = lambda:[])       # array[AGGREG_ARRAY_BYTE_SIZE] # not ack'd
    ogm_aggregations_received: list = field(default_factory = lambda:[])        # array[AGGREG_ARRAY_BYTE_SIZE]

    def ogm_adv_received(self, frame):  # modified function name from update_self to ogm_adv_received
        self.ogm_aggregations_received = frame.agg_sqn_no
        self.ogm_new_aggregation_received = frame.agg_sqn_no

    def iid_set_neighIID4x(self, neighIID4x, myIID4x):
        self.referred_by_me_timestamp = (time.perf_counter() - start_time) * 1000
        neigh_rep = self.neighIID4x_repos

        if (neigh_rep.max_free > neighIID4x):
            ref_iid = (neigh_rep.get_iid_entry()).myIID     #gets myIID corresponding to neighIID

        # while (repos.arr_size <= neighIID4x):   # for catching errors and ectending repos; might not be needed
        #     if (repos.arr_size > 32 and repos.arr_size > my_iid_repos.arr_size):
        #         print("IID_REPOS USAGE WARNING")

        neigh_rep.iid_set(neighIID4x, myIID4x, None)

    def get_node_by_neighIID4x(self, my_repos, neighIID4x):  
        neigh_rep = self.neighIID4x_repos
        ref = (neigh_rep.get_iid_entry(neighIID4x)).ref

        if (ref is None):
            print("neighIID4x=",neighIID4x," not recorded by neigh_repos")
        elif (((time.perf_counter() - start_time) * 1000) - ref.referred_by_neigh_timestamp_sec > 270):
            print("neighIID4x=",neighIID4x," outdated in neigh_repos")
        else:
            ref.referred_by_neigh_timestamp_sec = (time.perf_counter() - start_time) * 1000
            if (ref.myIID4x < my_repos.max_free):
                dhn = (my_repos.get_iid_entry(ref.myIID4x)).dhash_n
                if (dhn):
                    return dhn

        return None

    # def get_node_by_neighIID4x(self, my_iid, neighIID4x):    # added by harold from repos.py 
    #     if self.get_myIID4x_by_neighIID4x(neighIID4x) == -1:
    #         send HASH_REQ message
    #         print("Neighbor IID unknown. Sending Hash Request")
    #     else:
    #         myIID4x = self.get_myIID4x_by_neighIID4x(neighIID4x)

    #         if my_iid.arr[myIID4x] == KeyError:
    #             send DESC_REQ message
    #             print("Node description unknown. Sending Description Request")
    #         else:
    #             print("Retrieved hash from local IID repository: " + my_iid.arr[myIID4x])


# avl_tree orig_tree                           # array[HASH_SHA1_LEN/4] - [20/4]

@dataclass
class desc_tlv_hash_node:
    prev_hash: str         # SHA1_T
    curr_hash: str         # SHA1_T
    test_hash: str         # SHA1_T
    tlv_type: int
    test_changed: int
    prev_changed: int
        
@dataclass  
class host_metricalgo:
    fmetric_u16_min: float  # FMETRIC_U16_T

    umetric_min: int  # UMETRIC_T
    algo_type: int  # ALGO_T
    flags: int  # uint16_t              # seen in hna.h
    algo_rp_exp_numerator: int = 1      # default 1 (0-3) (uint8_t)
    algo_rp_exp_divisor: int = 2        # default 2 (0-3) (uint8_t)
    algo_tp_exp_numerator: int = 1      # default 1 (0-3) (uint8_t)
    algo_tp_exp_divisor: int = 1        # default 1 (1-2) (uint8_t)

    window_size: int = 5                # default 5 (1-250) (uint8_t)
    lounge_size: int = 1                # deafult 1 (0-10) (uint8_t)
    regression: int = 1                 # default 1 (1-255) (uint8_t)
    # fast_regression: int   # uint8_t
    # fast_regression_impact: int    # uint8_t
    #hystere: int  # uint8_t         # used for HNA annoucements # excluded for now
    hop_penalty: int = 0             # (uint8_t) default 0 (0-255) #Penalize non-first received OGM ADVs in 1/255 (each hop will substract metric*(VALUE/255) from current path-metric).
    #late_penalty: int  # uint8_t    # penalize non-first received ogm advs  # excluded for now

@dataclass
class orig_node:
    global_id: str = None                           # GLOBAL_ID_T (32 len) + PKID_T # default None

    dhash_n: dhash_node = None                      # dhash_node
    desc: description = None                        # **description (MISSING???) # default = None # DESC_ADV
    #desc_tlv_hash_tree: int                        # **avl_tree   # removed

    updated_timestamp: time = 0                     # TIME_T   # last time this orig node's description was updated # default # dependedent on last received DESC_ADV

    desc_sqn: int = -1                              # DESC_SQN_T (16 bits) # DESC_ADV

    ogm_sqn_range_min: int = 0                      # OGM_SQN_T (16 bits) # default 0  # DESC_ADV
    ogm_sqn_range_size: int = 65535                 # OGM_SQN_T (16 bits)  # default 65535    # DESC_ADV

    primary_ip: ipaddress.ip_address = ipaddress.ip_address('0.0.0.0')         # ip of link (IPX_T)
    #primary_ip_str: str                            # array[IPX_STR_LEN], removed
    #blocked: int                                   # indicates whether this node is blocked, assume no functionality of blocking nodes
    #added: int

    path_metricalgo: host_metricalgo = None         # **host_metricalgo (HAROLD)

    ogm_sqn_max_received: int = -1                  # OGM_SQN_T (16 bits)

    ogm_sqn_next: int = -1                          # OGM_SQN_T (16 bits)
    ogm_metric_next: int = -1                       # UMETRIC_T

    ogm_sqn_send: int = -1                          # OGM_SQN_T (16 bits)

    #metric_sqn_max_arr: int                        # UMETRIC_T , removed

    #rt_tree: int                                   # removed

    best_rt_local: router_node = None
    curr_rt_local: router_node = None
    curr_rt_linkdev: link_dev_node = None

    def update_self(self, frame):               # modified
        if type(frame) == frames.DESC_ADV:      # receiving new description
            self.updated_timestamp = (time.perf_counter() - start_time) * 1000  # bmx6_time
            self.desc_sqn = frame.desc_sqn_no
            self.primary_ip = socket.gethostbyname(frame.name)

        elif type(frame) == frames.OGM_ADV:
            self.ogm_sqn_max_received = frame.agg_sqn_no
            self.ogm_sqn_next = frame.agg_sqn_no + 1
            self.ogm_sqn_send = frame.agg_sqn_no

    def update_path_metrics(self):              # update seen from line 966, metrics.c
        pass

    def ack_ogm_frame(self, frame):             # function to ack ogm frames by creating ogm ack msgs
        if type(frame) == frames.OGM_ADV:       # check if ogm adv is received
            ack_msg1 = frames.OGM_ACK_msg       # assign 2 ack msgs with sqn number of ogm frame
            ack_msg2 = frames.OGM_ACK_msg
            ack_msg1.agg_sqn_no = frame.agg_sqn_no
            ack_msg2.agg_sqn_no = frame.agg_sqn_no
            self.ogm_sqn_max_received = frame.agg_sqn_no
            self.ogm_sqn_next = frame.agg_sqn_no + 1
            self.ogm_sqn_send = frame.agg_sqn_no

        return ack_msg1, ack_msg2



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

    ogm_advs: list = field(default_factory=lambda: [])

    ogm_dest_field: list = field(default_factory=lambda: [])   # array[(OGM_DEST_ARRAY_BIT_SIZE/8)]  # store dests where ogm frame is supposed to be sent
    #ogm_dest_bytes: int                        # removed from original

    aggregated_msgs_sqn_no: int = 0             # originally aggregated_msgs # deviated from original

    sqn: int = 0  # AGGREG_SQN_T (8 bits)
    #tx_attempt: int                            # removed from original
    
    def update_self(self, frame):               # initialize / update self after receiving ogm_adv frames
        if type(frame) == frames.OGM_ADV:
            self.ogm_advs.append(frame)

    def set_sqn_no_ogmframes_and_msgs(self):    # set aggregated seq no for ogm frame and sqn_no for msgs
        for frame in self.ogm_advs:             # n^2 time complexity
            for msgs in frame.ogm_adv_msgs:
                if msgs.ogm_sqn_no < 0:         # check if the msg has not yet been given a sqn number (-1 is default)
                    msgs.ogm_sqn_no = self.aggregated_msgs_sqn_no
                    self.aggregated_msgs_sqn_no += 1

                else:
                    continue                    # if msgs already given a sqn number, ignore
            assert self.aggregated_msgs_sqn_no < 65536      # make sure sqn no for msgs doesnt exceed ogm sqn range size

            if frame.agg_sqn_no < 0:            # check if the frame has not yet been given a sqn number (-1 is default)
                frame.agg_sqn_no = self.sqn
                self.sqn += 1

            else:
                continue                        # # if frame already given a sqn number, ignore
                
    def set_iid_offset_for_ogm_msg(self, neighbor):   # initialize iid offset for msgs 
        for frame in self.ogm_advs:
            for msg in frame.ogm_adv_msgs:
                if msg.iid_offset is None:      # ogm msg is in the originator, initialization # maybe change to < 0
                    msg.iid_offset = 0
                    iid = msg.iid_offset
                else:
                    neighiid = msg.iid_offset   # ogm msg contains iid of the originator
                    iid = neighbor.get_myIID4x_by_neighIID4x(neighiid)
                    msg.iid_offset = iid

        return iid                              # store iid value to local node
                
