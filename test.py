from ctypes import sizeof
from dataclasses import dataclass, field
import sys
import time
import ipaddress
import random
import socket
import psutil

from nodes import dev_node
from scipy import rand

## DATACLASSES

# @dataclass
# class header:
#     short_frm: int
#     relevant_frm: int
#     frm_type: int
#     frm_len: int

# @dataclass
# class RP_ADV_msg:
#     rp_127range: int
#     ogm_req: int

# @dataclass
# class RP_ADV:
#     frm_header: header
#     rp_msgs: list[RP_ADV_msg]

# msg1 = RP_ADV_msg(0,1)      # sample RP_ADV_msg
# msg2 = RP_ADV_msg(2,4)      # sample RP_ADV_msg
# print(msg1, msg2)

# def my_function(type):      # prints contents of a list
#     print("Printing list:")
#     for x in type:
#         print(x)
#     print("\n")

# msgs = [msg1, msg2]         # makes a list of messages
# my_function(msgs)           # prints the list of messages

# msg3 = RP_ADV_msg(3,6)      # sample RP_ADV_msg
# msgs.append(msg3)           # adds the msg to the end of the list
# my_function(msgs)           # prints the list of messages

# # creates a RP_ADV with a header and a list of messages
# rp = RP_ADV(header(0,0,0,0), msgs)
# print("RP_ADV frame with newly added RP_ADV msg:")
# print(rp)                   # prints the entire frame
# print("\n")

# # individual value changes are now possible
# rp.frm_header.frm_len = 4
# rp.frm_header.frm_type = 3
# rp.frm_header.relevant_frm = 2
# rp.frm_header.short_frm = 1

# print("updated RP_ADV frame after changing frame header:")
# print(rp)                   # prints the entire frame
# print("\n")

# # the entire field can also be changed using the right data type
# rp.frm_header = header(2,2,2,2)

# print("updated RP_ADV frame after changing frame header:")
# print(rp)                   # prints the entire frame



## GET TIME

# start_time = time.perf_counter()
# print(start_time)



## POINTER WORKAROUND

# @dataclass
# class big:
#     smaller: list = field(default_factory=lambda:[])
#     # smallest: list = []

# @dataclass
# class small:
#     bigger: big
#     id: int = 0
#     name: str = "small"

#     def __post_init__(self):
#         self.name = self.name+str(self.id)

# @dataclass
# class s:
#     bigger: list
#     count: int = 0
#     name: str = "s"

#     def __post_init__(self):
#         self.name = self.name+str(self.count)

# big_class = big()
# small_class1 = small(big_class, 1)
# s1 = s(big_class, 1)
# s1 = s([], 1)

# print("BIG:\t", big_class)
# print("SMALL:\t", small_class1)
# print("S:\t", s1)

# # print(sys.getsizeof(big_class))
# # print(sys.getsizeof(small_class))

# big_class.smaller.append(small_class1)
# big_class.smallest.append(s1)
# s1.bigger.append(big_class)

# print("BIG:\t", big_class)
# print("SMALL:\t", small_class1)
# print("S:\t", s1)

# small_class2 = small(big_class, 2)
# big_class.smaller.append(small_class2)
# # print(sys.getsizeof(big_class))
# # print(sys.getsizeof(small_class))

# print("BIG:\t", big_class)
# print("SMALL:\t", small_class1)
# print("SMALL:\t", small_class2)

# small_class3 = small(big_class, 3)
# big_class.smaller.append(small_class3)

# # print("BIG:\t", big_class)

# def print_big(big): 
#     print("Printing smaller objects:")
#     for x in big.smaller:
#         print(x.bigger)
        # print(x.bigger)

# # print("SMALL:\t", small_class1)
# # print("SMALL:\t", small_class2)
# print("SMALL:\t", small_class3)
# print("BIG:\t", big_class)
# print_big(big_class)
# print("SMALL:\t", small_class1)
# l = list([big_class, small_class1, small_class2])
# print(l)

# print(sys.getsizeof(big_class))
# print(sys.getsizeof(small_class1))
# print(sys.getsizeof(small_class2))
# print(sys.getsizeof(small_class3))



## TIME TESTING

# time.sleep(1)
# end_time = time.perf_counter()
# print(end_time)
# elapsed = (end_time - start_time) * 1000
# print(elapsed)



## GETTING UMETRIC_MAX

# OGM_EXPONENT_OFFSET = 5
# OGM_EXPONENT_MAX = ((1 << 5) - 1)
# # 11111
# FM8_MANTISSA_BIT_SIZE = 8 - 5
# FM8_MANTISSA_MASK = ((1 << FM8_MANTISSA_BIT_SIZE) - 1)
# # 111
# UMETRIC_MAX = (((1) << (OGM_EXPONENT_OFFSET + OGM_EXPONENT_MAX)) + ((FM8_MANTISSA_MASK) << ((OGM_EXPONENT_OFFSET+OGM_EXPONENT_MAX)-FM8_MANTISSA_BIT_SIZE)))
# # [1 << 36] + [111 << 33]
# # 68719476736 + 60129542144
# print("UMETRIC_MAX: ",UMETRIC_MAX)
# i = UMETRIC_MAX/111
# print(int(i))



## CHECKING HOW LIST ELEMENTS ARE AFFECTED

# @dataclass
# class x:
#     l : list = field(default_factory=lambda:[])

#     def app(self, lis):
#         self.l[0].append(lis)

# local_x = x([])
# local_y = x([])
# numlist = [1,2,3]
# local_x.l.append(numlist)
# local_x.l.append(numlist)
# print("x:",local_x.l,'\t',"y:",local_y.l)
# local_x.l[0].append(4)
# print("x:",local_x.l,'\t',"y:",local_y.l)
# local_x.app(5)
# print("x:",local_x.l,'\t',"y:",local_y.l)



## TEST IPV6

# @dataclass
# class node:                      # holds information about the other node
#     ip: ipaddress.ip_address = ipaddress.ip_address('0.0.0.0')    

# addr = '::1'
# test_node = node(ipaddress.ip_address(addr))
# print(test_node)
# print(type(test_node.ip))
# print(hex(int(test_node.ip)))
# print(sizeof(hex(1)))


## TEST RANDOM

# randy = random.randint(0,100)
# print(randy)
# randy = randy + 1
# print(randy)


## TEST APPEND

# @dataclass
# class no_holder:
#     numlist: list
#     num: int

# no = 24
# nolist = [0,2,4]
# frames = []
# frames.append(no_holder(numlist = nolist, num = no))
# print(nolist)
# print(frames)
# no = 34
# nolist.clear()
# print(nolist)
# print(frames)


## TEST MAC CONVERSION

# mac = "AB:CD:EF:12:34:56"
# mac_converted = int(mac[0]+mac[1], 16) << 8
# mac_converted = mac_converted + int(mac[3]+mac[4], 16) << 8
# mac_converted = mac_converted + int(mac[6]+mac[7], 16) << 8
# mac_converted = mac_converted + int(mac[9]+mac[10], 16) << 8
# mac_converted = mac_converted + int(mac[12]+mac[13], 16) << 8
# mac_converted = mac_converted + int(mac[15]+mac[16], 16)

# mac_converted2 = int(mac[0]+mac[1]+mac[3]+mac[4]+mac[6]+mac[7]+mac[9]+mac[10]+mac[12]+mac[13]+mac[15]+mac[16], 16)
# print(mac_converted)
# print(mac_converted2)

###############################################################################

def get_interfaces(iflist):
    dev_id = len(iflist)
    
    if(len(iflist) == 0):
        iflist.append(dev_node())
        dev_id = dev_id + 1

    def check_interface(name, iflist):
        for itf in iflist:
            if((itf.name == name) and (itf.idx > 0)):
                return itf.idx
        return -1

    def inactive(iflist):
        for itf in iflist:                                                      # assume all interfaces inactive
            itf.active = 0

    inactive(iflist)
    for x, y in psutil.net_if_addrs().items():
        id = check_interface(x, iflist)
        if(id == -1):
            interface = dev_node(name = x, idx = dev_id, active = 1)  # new interfaces always active
        else:
            interface = iflist[id]                                          # if found, mark as active
            iflist[id].active = 1  
        for z in y:
            # print('\t', z, type(z))
            # print('\t\t', z.family)
            # print('\t\t', z.address)
            if(z.family is socket.AF_INET):
                interface.ipv4 = z.address
            elif(z.family is socket.AF_INET6):
                interface.ipv6 = z.address
            else:
                interface.mac = z.address
        if((interface.mac == "00:00:00:00:00:00") and (interface.ipv6 == '::1')):   # linux loopback interface
            interface.mac = None
        if((interface.umetric_min is None) and (interface.umetric_max is None)):
            if((interface.mac is None) and (interface.ipv6 == '::1')):              # loopback interface
                interface.type = 0
                interface.umetric_min = 128849018880    # UMETRIC_MAX
                interface.umetric_max = 128849018880    # UMETRIC_MAX
                interface.fmu8_min = 255                # 0xff (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 255                # 0xff (converted UMETRIC to FMETRIC_U8_T)
            elif((interface.name[0] == 'e') or (interface.name[0] == 'E')):         # ethernet
                interface.type = 1
                interface.channel = 255
                interface.umetric_min = 1000000000      # DEF_DEV_BITRATE_MIN_LAN
                interface.umetric_max = 1000000000      # DEF_DEV_BITRATE_MAX_LAN
                interface.fmu8_min = 199                # 0xc7 (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 199                # 0xc7 (converted UMETRIC to FMETRIC_U8_T)
            else:
                interface.type = 2                                                  # wireless
                interface.umetric_min = 6000000         # DEF_DEV_BITRATE_MIN_WIFI
                interface.umetric_max = 56000000        # DEF_DEV_BITRATE_MAX_WIFI
                interface.fmu8_min = 139                # 0x8b (converted UMETRIC to FMETRIC_U8_T)
                interface.fmu8_max = 165                # 0xa5 (converted UMETRIC to FMETRIC_U8_T)
        if(interface.type == 0):
            interface.idx = 0
            iflist[0] = interface
        elif(id == -1):
            iflist.append(interface)
            dev_id = dev_id + 1
        else:
            iflist[id] = interface
        # print(interface, '\n')
    
    for interface in iflist:
        if(interface.type == 1):
            return interface.mac                                        # use ethernet mac addr for local_id generation
    return -1

def print_interfaces(iflist):
    for x in iflist:
        print(x.idx," - '",x.name,"':",sep='')
        if(x.ipv4 is not None):
            print("    IPv4:",'\t', x.ipv4)
        if(x.ipv6 is not None):
            print("    IPv6:",'\t', x.ipv6)
        if(x.mac is not None):
            print("    MAC:",'\t', x.mac)
        print("    type:",'\t', x.type)
        print("    active:",'\t', x.active)
        print("    channel:",'\t', x.channel)
        print("    umetric_min:", x.umetric_min)
        print("    umetric_max:", x.umetric_max)
        print("    fmu8_min:", x.fmu8_min)
        print("    fmu8_max:", x.fmu8_max)
    print()


interfaces = []
get_interfaces(interfaces)

print_interfaces(interfaces)
