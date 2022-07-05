import string
import socket
import re, uuid
import ipaddress
from math import log2
from dataclasses import dataclass, field

def custom_log2(num):
    if num < 0:
        raise ValueError("negative values are not accepted..")
    if num == 0:
        return 0
    else:
        return round(log2(num))

@dataclass
class header:
    short_frm: int = 0
    relevant_frm: int = 0
    frm_type: int = 0
    frm_len: int = 0

@dataclass
class short_header:
    short_frm: int
    relevant_frm: int
    frm_type: int
    frm_len: int
    
@dataclass
class long_header:
    short_frm: int
    relevant_frm: int
    frm_type: int
    reserved: int
    frm_len: int
    
@dataclass
class HELLO_ADV:
    frm_header: header
    HELLO_sqn_no: int           # uint16_t (0 - 65535)          # sqn used for link metric calculation

@dataclass
class RP_ADV_msg:
    rp_127range: int            # 7 bits (0 - 127)              # report of the number of HELLO_ADV frames received
    ogm_req: int                # 1 bit (0 / 1)                 # set to 1 if it wants to receive OGMs from the RP_ADV receiver

@dataclass
class RP_ADV:
    frm_header: header
    rp_msgs: list[RP_ADV_msg]

@dataclass
class OGM_ADV_msg:
    metric_mantisse: int = 0    
    metric_exponent: int = 0
    iid_offset: int = None
    ogm_sqn_no: int = -1
        
    def fmetric(self):  # uses mantisse & exp values
        return self.metric_mantisse, self.metric_exponent

    """return (((UMETRIC_T) 1) << (fm.val.f.exp_fm16 + OGM_EXPONENT_OFFSET)) +
    (((UMETRIC_T) fm.val.f.mantissa_fm16) << (fm.val.f.exp_fm16));"""
    # [1 << (metric exp + 5)] + [metric mantissa << metric exp]
    def fmetric_to_umetric(self):
        return (1 << (self.metric_exponent + 5)) + (self.metric_mantisse + self.metric_exponent)

    def umetric(self):  # fmetric_to_umetric
        return self.fmetric_to_umetric()

    """3 cases
    note for c1: UMETRIC_MIN_NOT_ROUTABLE = ((((UMETRIC_T) 1) << OGM_EXPONENT_OFFSET) + OGM_MANTISSA_MIN__NOT_ROUTABLE) = (1 << 5) + 1 = 33
    note for c2: UMETRIC_MAX = ((((UMETRIC_T) 1) << (OGM_EXPONENT_OFFSET+OGM_EXPONENT_MAX)) + (((UMETRIC_T) FM8_MANTISSA_MASK) << ((OGM_EXPONENT_OFFSET+OGM_EXPONENT_MAX)-FM8_MANTISSA_BIT_SIZE))) = (1 << 5+31) + (((1<<3)-1) << ((1 << 5+31)- 3))
    case 1: argument < 64 (umetric_min_not_routable)                                                                                                                                         68719476736  + (     7     << (68719476736 - 3))
    case 2: argument >= umetric_max, case disregarded.. assuming argument wont exceed absurd value                                                                                                                                                               = absurdly large value
    case 3: else: """

    def umetric_to_fmetric(self, x):
        if x < 33:  # UMETRIC_MIN_NOT_ROUTABLE
            self.metric_exponent = 0
            self.metric_mantisse = 0
        else:
            tmp = x + x/79  # 79 from UMETRIC_TO_FMETRIC_INPUT_FIX
            exp_sum = custom_log2(x)
            self.metric_exponent = exp_sum - 5  # ogm_exponent_offset
            self.metric_mantisse = (tmp >> (exp_sum - 5)) - (1 << 5)  # ( (tmp>>(exp_sum-OGM_MANTISSA_BIT_SIZE)) - (1<<OGM_MANTISSA_BIT_SIZE) );


@dataclass
class OGM_ADV:
    frm_header: header
    agg_sqn_no: int = -1
    ogm_dest_arr_size: int = None
    ogm_dest_arr: list = field(default_factory=lambda: [])
    ogm_adv_msgs: list = field(default_factory=lambda: [])
        
    def best_ogm_msg(self) -> OGM_ADV_msg:          #comparison of OGM_ADV_msg inside OGM_ADV frame
        seq_no = []
        count = 0
        
        for i in self.ogm_adv_msgs:
            seq_no.append(i.ogm_sqn_no)

        max_seq_no = max(seq_no)

        for j in self.ogm_adv_msgs:
            if j.ogm_sqn_no != max_seq_no:
                count += 1
                continue

            else:
                best = self.ogm_msgs[count]

        return best

@dataclass
class OGM_ACK_msg:
    ogm_dest: int = None                # # tells the node who sent ogm adv; value is the position of the rx node in the link_adv of the tx
    agg_sqn_no: int = -1
    
@dataclass
class OGM_ACK:                         # sent twice by default  # only ack nodes who requested ogm frame
    frm_header: header
    ogm_ack_msgs: list = field(default_factory=lambda: [])

@dataclass
class LINK_REQ:
    frm_header: header
    dest_local_id: int          # uint32_t (0 - 4294967295)     # indicates which neighbor has to answer the LINK_REQ

@dataclass
class LINK_ADV_msg:
    trans_dev_index: int        # uint8_t (0 - 255)             # device index of the sending node
    peer_dev_index: int         # uint8_t (0 - 255)             # device index of the receiving node
    peer_local_id: int          # uint32_t (0 - 4294967295)     # local id of the receiving node

@dataclass
class LINK_ADV:
    frm_header: header
    dev_sqn_no_ref: int         # uint16_t (0 - 65535)          # sqn of the DEV_ADV related to this LINK_ADV
    link_msgs: list[LINK_ADV_msg]

@dataclass
class DEV_REQ:
    frm_header: header
    dest_local_id: int          # uint32_t (0 - 4294967295)

@dataclass
class DEV_ADV_msg:
    dev_index: int              # uint8_t (0 - 255)
    channel: int                # uint8_t (0 - 255)
    trans_bitrate_min: int      # FMETRIC_U8_T      
    trans_bitrate_max: int      # FMETRIC_U8_T 
    local_ipv6: int             # 16 bytes (hex)
    mac_address: int            # 6 bytes (hex)
        
@dataclass
class DEV_ADV:
    frm_header: header
    dev_sqn_no: int             # uint16_t (0 - 65535)
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
    name: str   # socket.gethostname()
    pkid: int   
    code_version: int
    capabilites: int
    desc_sqn_no: int
    ogm_min_sqn_no: int     # default 0
    ogm_range: int          # default 0 to 2^16
    trans_interval: int     # time interval for every packet sent
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
