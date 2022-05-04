import string
import sys
from time import time
from typing import NamedTuple


# avl_tree local_tree

class local_node(NamedTuple):
    local_id: int                       # LOCAL_ID_T
    link_tree: int                      # **avl_tree
    best_rp_linkdev: int                # **link_dev_node
    best_tp_linkdev: int                # **link_dev_node
    best_linkdev: int                   # **link_dev_node
    neigh: int                          # **neigh_node

    packet_sqn: int                     # PKT_SQN_T
    packet_time: time
    packet_link_sqn_ref: int            # LINK_ADV_SQN_T

    # from the latest LINK_ADV
    packet_link_sqn: int                # LINK_ADV_SQN_T
    link_adv_msgs: int
    link_adv_msgs_for_me: int
    link_adv_msgs_for_them: int
    link_adv: int                       # **msg_link_adv (frames.LINK_ADV?)
    link_adv_dev_sqn_ref: int           # DEVADV_SQN_T (frames.DEV_ADV.dev_sqn_np)

    # from the latest DEV_ADV
    dev_adv_sqn: int                    # DEVADV_SQN_T (frames.DEV_ADV.dev_sqn_np)
    dev_adv_msgs: int
    dev_adv: int                        # **msg_dev_adv (frames.DEV_ADV)

    # from the latest RP_ADV
    rp_adv_time: time
    rp_ogm_request_received: int        # **IDM_T
    orig_routes: int


# avl_tree link_tree

class link_node_key(NamedTuple):
    local_id: int                       # LOCAL_ID_T
    dev_idx: int                        # **DEVADV_IDX_T

class link_node(NamedTuple):
    key: link_node_key

    link_ip: int                        # **IPX_T
    
    pkt_time_max: time
    hello_time_max: time

    hello_sqn_max: int

    local: local_node
    
    linkdev_list: int                   # **list_head

class link_dev_key(NamedTuple):
    link: link_node
    dev: int                            # **dev_node


# avl_tree link_dev_tree

class link_dev_node(NamedTuple):
    list: int                           # **list_node
    key: link_dev_key

    tx_probe_umetric: int               # **UMETRIC_T
    timeaware_tx_probe: int             # **UMETRIC_T
    timeaware_rx_probe: int             # **UMETRIC_T
    rx_probe_record: int                # **lndev_probe_record

    tx_task_lists: int                  # **list_head - array[FRAME_TYPE_ARRSZ]
    link_adv_msg: int
    pkt_time_max: time

class router_node(NamedTuple):
    local_key: local_node

    metric_red: int                     # **metric_record
    ogm_sqn_last: int
    ogm_umetric_last: int               # **UMETRIC_T

    path_metric_best: int               # **UMETRIC_T
    path_linkdev_best: link_dev_node


# avl_tree neigh_trees

class neigh_node(NamedTuple):
    neigh_node_key: int                 # **neigh_node
    dhash_n: int                        # **dhash_node                 

    local: local_node

    neighIID4me: int                    # IID_T

    neighIID4x_repos: int               # **iid_repos

    ogm_new_aggregation_received: time
    ogm_aggregation_cleared_max: int    # AGGREG_SQN_T
    ogm_aggregations_not_acked: int     # array[AGGREG_ARRAY_BYTE_SIZE]
    ogm_aggregations_received: int      # array[AGGREG_ARRAY_BYTE_SIZE]


# avl_tree orig_tree

class desc_tlv_hash_node(NamedTuple):
    prev_hash: int                      # SHA1_T
    curr_hash: int                      # SHA1_T
    test_hash: int                      # SHA1_T
    tlv_type: int
    test_changed: int
    prev_changed: int

class orig_node(NamedTuple):
    global_id: int                      # GLOBAL_ID_T

    dhash_n: dhash_node
    desc: int                           # **description
    desc_tlv_hash_tree: int             # **avl_tree

    updated_timestamp: time

    desc_sqn: int                       # DESC_SQN_T

    ogm_sqn_range_min: int              # OGM_SQN_T
    ogm_sqn_range_size: int             # OGM_SQN_T

    primary_ip: int                     # IPX_T
    primary_ip_str: str                 # array[IPX_STR_LEN]
    blocked: int
    added: int

    path_metricalgo: int                # **host_metricalgo

    ogm_sqn_max_received: int           # OGM_SQN_T

    ogm_sqn_next: int                   # OGM_SQN_T
    ogm_metric_next: int                # UMETRIC_T

    ogm_sqn_send: int                   # OGM_SQN_T

    metric_sqn_max_arr: int             # UMETRIC_T - *remove*

    rt_tree: int                        # **avl_tree

    best_rt_local: router_node          # *remove*
    curr_rt_local: router_node
    cutt_rt_linkdev: link_dev_node


# avl_tree dhash_tree
# avl_tree dhash_invalid_tree

class dhash_node(NamedTuple):
    dhash: int                          # description_hash

    referred_by_me_timestamp: time

    neigh: neigh_node

    myIID4origL: int                    # IID_T
    
    orig_n: orig_node


# avl_tree blacklisted_tree

class black_node(NamedTuple):
    dhash: int                          # description_hash

class throw_node(NamedTuple):
    list: int                           # **list_node
    addr: int
    netmask: int

class ogm_aggreg_node(NamedTuple):
    list: int                           # **list_node

    ogm_advs: int                       # **msg_ogm_adv (frames.OGM_ADV)

    ogm_dest_field: int                 # array[(OGM_DEST_ARRAY_BIT_SIZE/8)]
    ogm_dest_bytes: int

    aggregated_msgs: int

    sqn: int                            # **AGGREG_SQN_T
    tx_attempt: int


