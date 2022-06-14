import string
from dataclasses import dataclass
import socket
import re, uuid

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
        
    def __post_init__(self):  
        if self.metric_mantisse is None:
            self.metric_mantisse = 0
        if self.metric_exponent is None:
            self.metric_exponent = 0

@dataclass
class OGM_ADV:
    frm_header: header
    agg_sqn_no: int
    ogm_dest_arr_size: int
    ogm_dest_arr: list[int]
    ogm_msgs: list[OGM_ADV_msg]
        
    def best_ogm_msg(self) -> OGM_ADV_msg:          #comparison of OGM_ADV_msg inside OGM_ADV frame
        seq_no = []
        count = 0
        
        for i in self.ogm_msgs:
            seq_no.append(i.ogm_sqn_no)

        max_seq_no = max(seq_no)

        for j in self.ogm_msgs:
            if j.ogm_sqn_no != max_seq_no:
                count += 1
                continue

            else:
                best = self.ogm_msgs[count]

        return best

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
        
    def get_local_ipv6(self):  #gets the ipv6 address of the device
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.connect(('2001:4860:4860::8888', 1))
            self.local_ipv6 = s.getsockname()[0]

        except:
            self.local_ipv6 = '::1'

        finally:
            if 's' in locals():
                s.close()
                
    def get_mac_address(self): #gets the mac address of the device
        self.mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        
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
