from ctypes import sizeof
from dataclasses import dataclass
import sys

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

# pointer workaround

@dataclass
class big:
    smaller: list
    # smallest: list = []

@dataclass
class small:
    bigger: big
    id: int = 0
    name: str = "small"

#     def __post_init__(self):
#         self.name = self.name+str(self.id)

# @dataclass
# class s:
#     bigger: list
#     count: int = 0
#     name: str = "s"

#     def __post_init__(self):
#         self.name = self.name+str(self.count)

big_class = big([])
small_class1 = small(big_class, 1)
# s1 = s(big_class, 1)
# s1 = s([], 1)

print("BIG:\t", big_class)
print("SMALL:\t", small_class1)
# print("S:\t", s1)

# # print(sys.getsizeof(big_class))
# # print(sys.getsizeof(small_class))

big_class.smaller.append(small_class1)
# big_class.smallest.append(s1)
# s1.bigger.append(big_class)

print("BIG:\t", big_class)
print("SMALL:\t", small_class1)
# print("S:\t", s1)

small_class2 = small(big_class, 2)
big_class.smaller.append(small_class2)
# # print(sys.getsizeof(big_class))
# # print(sys.getsizeof(small_class))

print("BIG:\t", big_class)
print("SMALL:\t", small_class1)
# print("SMALL:\t", small_class2)

# small_class3 = small(big_class, 3)
# big_class.smaller.append(small_class3)

# # print("BIG:\t", big_class)

def print_big(big): 
    print("Printing smaller objects:")
    for x in big.smaller:
        print(x.bigger)
        # print(x.bigger)

# # print("SMALL:\t", small_class1)
# # print("SMALL:\t", small_class2)
# print("SMALL:\t", small_class3)
# print("BIG:\t", big_class)
print_big(big_class)

# print(sys.getsizeof(big_class))
# print(sys.getsizeof(small_class1))
# print(sys.getsizeof(small_class2))
# print(sys.getsizeof(small_class3))

# x = int(10)
# print(type(x))
# if(type(x) == int):
#     print("Wow, it's an int!")