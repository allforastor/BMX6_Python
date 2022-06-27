# DUMP.PY

# DUMP CODE THAT MIGHT BE USED IN THE FUTURE HERE

#////////////////////////////////////////////////////////////////////////////////////////////
# NODES.PY

# @dataclass
# class if_link_node:
#     update_sqn: int = 0
#     changed: int = 0
#     index: int = 0
#     type: int = 0
#     alen: int = 0
#     flags: int = 0

#     addr: int = 0                                                               # ADDR_T
#     name: str = ""

#     if_addr_tree: list = field(default_factory=lambda:[])                       # avl_tree

# @dataclass
# class if_addr_node:
#     iln: if_link_node
#     dev: list = field(default_factory=lambda:[])                                # dev_node
#     rta_tb: list = field(default_factory=lambda:[])                             # array[]



# @dataclass
# class dev_ip_key:
#     ip: ipaddress.ip_address = ipaddress.ip_address('0.0.0.0')                  # copy of dev.if_llocal_addr.ip_addr
#     idx: int = -1                                                               # link_key.dev_idx (DEVADV_IDX_T)


# @dataclass
# class dev_node:
#     if_link: int                                                                # if_link_node
#     if_llocal_addr: int                                                         # if_addr_node
#     if_global_addr: int                                                         # if_addr_node

#     hard_conf_changed: int
#     soft_conf_changed: int
#     autoIP6configured: int                                                      # net_key
#     autoIP6ifindex: int
#     active: int
#     activate_again: int
#     activate_cancelled: int
#     tmp_flag_for_to_be_send_adv: int

#     dev_adv_msg: int

#     ifname_label: str                                                           # IFNAME_T
#     ifname_device: str                                                          # IFNAME_T

#     # dummy_lndev: link_dev_node
    
#     llip_key: dev_ip_key
#     mac: int                                                                    # MAC_T

#     ip_llocal_str: str                                                          # array[IPX_STR_LEN]
#     ip_global_str: str                                                          # array[IPX_STR_LEN]
#     ip_brc_str: str                                                             # array[IPX_STR_LEN]

#     llocal_unicast_addr: int                                                    # sockaddr_storage
#     tx_netwbrc_addr: int                                                        # sockaddr_storage

#     unicast_sock: int
#     rx_mcast_sock: int
#     rx_fullbrc_sock: int

#     link_hello_sqn: int                                                         # HELLO_SQN_T

#     tx_task_lists: list                                                         # array of scheduled frames (list_head - array[FRAME_TYPE_ARRSZ])
#     tx_task_interval_tree: int                                                  # avl_tree

#     announce: int

#     linklayer_conf: int
#     linklayer: int

#     channel_conf: int
#     channel: int

#     umetric_min_conf: int                                                       # UMETRIC_T
#     umetric_min: int                                                            # UMETRIC_T

#     umetric_max_conf: int                                                       # UMETRIC_T
#     umetric_max: int                                                            # UMETRIC_T

#     global_prefix_conf_: int                                                    # net_key
#     llocal_prefix_conf_: int                                                    # net_key
    
#     plugin_data: list                                                           # void*