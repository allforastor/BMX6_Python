import string
from dataclasses import dataclass

@dataclass
class header:
    short_frm: int
    relevant_frm: int
    frm_type: int
    frm_len: int

@dataclass
class HELLO_ADV:
    frm_header: header
    HELLO_sqn_no: int

@dataclass
class RP_ADV_msg:
    rp_127range: int
    ogm_req: int

@dataclass
class RP_ADV:
    frm_header: header
    rp_msgs: list[RP_ADV_msg]

@dataclass
class OGM_ADV_msg:
    metric_mantisse: int
    metric_exponent: int
    iid_offset: int
    ogm_sqn_no: int

@dataclass
class OGM_ADV:
    frm_header: header
    agg_sqn_no: int
    ogm_dest_arr_size: int
    ogm_dest_arr: list[int]
    ogm_msgs: list[OGM_ADV_msg]

@dataclass
class OGM_ACK:
    frm_header: header
    ogm_dest: int
    agg_sqn_no: int

@dataclass
class LINK_REQ:
    frm_header: header
    dest_local_id: int

@dataclass
class LINK_ADV_msg:
    trans_dev_index: int
    peer_dev_index: int
    peer_local_id: int

@dataclass
class LINK_ADV:
    frm_header: header
    dev_sqn_no_ref: int
    link_msgs: list[LINK_ADV_msg]

@dataclass
class DEV_REQ:
    frm_header: header
    dest_local_id: int

@dataclass
class DEV_ADV_msg:
    dev_index: int
    channel: int
    trans_bitrate_min: int
    trans_bitrate_max: int
    local_ipv6: int
    mac_address: int

@dataclass
class DEV_ADV:
    frm_header: header
    dev_sqn_no: int
    dev_msgs: list[DEV_ADV_msg]

@dataclass
class DESC_REQ_msg:
    dest_local_id: int
    receiver_iid: int

@dataclass
class DESC_REQ:
    frm_header: header
    desc_msgs: list[DESC_REQ_msg]

@dataclass
class DESC_ADV_msg:
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

@dataclass
class DESC_ADV:
    frm_header: header
    desc_msgs: list[DESC_ADV_msg]

@dataclass
class HASH_REQ_msg:
    dest_local_id: int
    receiver_iid: int

@dataclass
class HASH_REQ:
    frm_header: header
    hash_msgs: list[HASH_REQ_msg]

@dataclass
class HASH_ADV:
    frm_header: header
    trans_iid4x: int
    desc_hash: int