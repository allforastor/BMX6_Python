from ctypes import sizeof
from dataclasses import dataclass, field
import sys
import time
import ipaddress
import random

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

mac = "AB:CD:EF:12:34:56"
mac_converted = int(mac[0]+mac[1], 16) << 8
mac_converted = mac_converted + int(mac[3]+mac[4], 16) << 8
mac_converted = mac_converted + int(mac[6]+mac[7], 16) << 8
mac_converted = mac_converted + int(mac[9]+mac[10], 16) << 8
mac_converted = mac_converted + int(mac[12]+mac[13], 16) << 8
mac_converted = mac_converted + int(mac[15]+mac[16], 16)

mac_converted2 = int(mac[0]+mac[1]+mac[3]+mac[4]+mac[6]+mac[7]+mac[9]+mac[10]+mac[12]+mac[13]+mac[15]+mac[16], 16)
print(mac_converted)
print(mac_converted2)