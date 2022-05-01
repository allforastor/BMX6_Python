from os import link
import string
import sys
from typing import NamedTuple

class header(NamedTuple):
    short_frm: int
    relevant_frm: int
    frm_type: int
    frm_len: int

class HELLO_ADV(NamedTuple):
    frm_header: header
    HELLO_sqn_no: int

class RP_ADV_msg(NamedTuple):
    rp_127range: int
    ogm_req: int

class RP_ADV(NamedTuple):
    frm_header: header
    rp_msgs: list

class OGM_ADV_msg(NamedTuple):
    metric_mantisse: int
    metric_exponent: int
    iid_offset: int
    ogm_sqn_no: int

class OGM_ADV(NamedTuple):
    frm_header: header
    agg_sqn_no: int
    ogm_dest_arr_size: int
    ogm_dest_arr: list
    ogm_msgs: list

class OGM_ACK(NamedTuple):
    frm_header: header
    ogm_dest: int
    agg_sqn_no: int

class LINK_REQ(NamedTuple):
    frm_header: header
    dest_local_id: int

class LINK_ADV_msg(NamedTuple):
    trans_dev_index: int
    peer_dev_index: int
    peer_local_id: int

class LINK_ADV(NamedTuple):
    frm_header: header
    dev_sqn_no_ref: int
    link_msgs: list

class DEV_REQ(NamedTuple):
    frm_header: header
    dest_local_id: int

class DEV_ADV_msg(NamedTuple):
    dev_index: int
    channel: int
    trans_bitrate_min: int
    trans_bitrate_max: int
    local_ipv6: int
    mac_address: int

class DEV_ADV(NamedTuple):
    frm_header: header
    dev_sqn_no: int
    dev_msgs: list

class DESC_REQ_msg(NamedTuple):
    dest_local_id: int
    receiver_iid: int

class DESC_REQ(NamedTuple):
    frm_header: header
    desc_msgs: list

class DESC_ADV_msg(NamedTuple):
    trans_iid4x: int
    name: str
    pkid: int
    code_version: int
    capabilites: int
    desc_sqn_no: int
    ogm_min_sqn_no: int
    ogm_range: int
    trans_interval: int
    ext_len: int
    ext_frm: int

class DESC_ADV(NamedTuple):
    frm_header: header
    desc_msgs: list

class HASH_REQ_msg(NamedTuple):
    dest_local_id: int
    receiver_iid: int

class HASH_REQ(NamedTuple):
    frm_header: header
    hash_msgs: list

class HASH_ADV(NamedTuple):
    frm_header: header
    trans_iid4x: int
    desc_hash: int
    hash_msgs: int

msg1 = HASH_REQ_msg(0,1)    #sample HASH_REQ_msg
msg2 = HASH_REQ_msg(2,4)    #sample HASH_REQ_msg
print(msg1, msg2)

def my_function(type):      #prints contents of a list
    for x in type:
        print(x)

msgs = [msg1, msg2]         #makes a list of messages
my_function(msgs)           #prints the list of messages

msg3 = HASH_REQ_msg(3,6)    #sample HASH_REQ_msg
msgs.append(msg3)           #adds the msg to the end of the list
my_function(msgs)           #prints the list of messages

#creates a HASH_REQ with a header and a list of messages
hash = HASH_REQ(header(0,0,0,0), msgs)
print(hash)                 #prints the entire frame
