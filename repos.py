from asyncio.windows_events import NULL
import string
import sys
import hashlib
import time
import random

# from runtime import my_iid_repos
from frames import DESC_ADV_msg
import nodes
from dataclasses import dataclass, fields

start_time = time.perf_counter()

# my_iid_repos = runtime.my_iid_repos      
my_iid_repos = nodes.iid_repos()    # local IID repository that should hold all dhash_nodes

# reference funtion from orig bmx6: void update_my_description_adv(void)
def hash_description(desc): #hashes description from message
    dhash = hashlib.sha1()

    for field in fields(desc):
        if (field.name == 'trans_iid4x'):
            iid = desc.trans_iid4x
        else: 
            x = getattr(desc, field.name)
            try:
                dhash.update(x.encode())
            except AttributeError:
                x = "% s" % x
                dhash.update(x.encode())

    result = dhash.hexdigest()
    return result
    
#     # map description hash to its corresponding iid
#     my_iid_repos.arr[iid] = result


# creation of dhash_node

# def iid_new_myIID4x(dhnode):    #adds new IID entry given a dhash_node
#     if (my_iid_repos.arr_size > my_iid_repos.tot_used):
#         rand_iid = random.randint(0,my_iid_repos.arr_size)  #could also be max_free because arr_size + 1
#         mid = max(1,rand_iid)   # minimum iid value: IID_MIN_USED = 1

#         for entry in my_iid_repos.arr[mid:]:
#             try:
#                 if (entry.u8 == mid and entry.dhash_n):     # possibly remove 2nd condition since existing key implies existing node?
#                     mid += 1
#                     if (mid >= my_iid_repos.arr_size):
#                         mid = 1     # return to minimum iid 1
#             except KeyError: break
#     else:
#         mid = my_iid_repos.min_free

#     my_iid_repos.iid_set(mid,0,dhnode)

#     # return mid  # function should be called as dhash_node->myIID4orig = iid_new_myIID4x(dhnode);

# def get_node_by_neighIID4x(neighIID4x):
#     pass

# TESTING

# sample topology (modified from routing_test.py)
#
#        A ------------ B ------------ C
#    local_node
# holding my_iid_repos
#
# IID repo of A
# ----------------
# | IID |  Hash  |
# |  1  | Hash_A |
# |  2  | Hash_B |
# |  3  | Hash_C |
# ----------------
#                                                   A
#-----------------------------------------------------------------------------------------------------------------
#
# Neighbor repo of B                            IID repo of B
# -----------------------------                ----------------
# | IID |  myIID4x equivalent |                | IID |  Hash  |
# |  1  |          2          |                |  1  | Hash_B |
# |  2  |          1          |                |  2  | Hash_A |
# |  3  |          3          |                |  3  | Hash_C |
# -----------------------------                ----------------
#
#                                                    B
#-----------------------------------------------------------------------------------------------------------------

# Print initial my_iid_repos
# print ("Initial my_iid_repos")
# my_iid_repos.print_repos()

# Declaring test message and dhash_node values
msg1 = DESC_ADV_msg(2,'dev1',40,1,0,0,0,0,0,0,0)
msg2 = DESC_ADV_msg(1,'dev2',0,0,0,0,0,0,0,0,0)
msg3 = DESC_ADV_msg(0,'dev2',20,9,6,7,0,0,0,0,0)
dhnodeA = nodes.dhash_node(hash_description(msg1),0,2)
dhnodeB = nodes.dhash_node(hash_description(msg2),0,3)
dhnodeC = nodes.dhash_node(hash_description(msg3),0,4)

# Print new my_iid_repos
# Filling in my_iid_repos
my_iid_repos.iid_new_myIID4x(dhnodeA)
my_iid_repos.iid_new_myIID4x(dhnodeB)
my_iid_repos.iid_new_myIID4x(dhnodeC)
print ("Node A (my_iid_repos)")
my_iid_repos.print_repos()

# Initializing neighbor node
nodeB = nodes.neigh_node()
nodeB.iid_set_neighIID4x(1,2)
nodeB.iid_set_neighIID4x(2,1)
nodeB.iid_set_neighIID4x(3,3)
print ("Node B (nodeB.neighIID4x_repos)")
nodeB_repos = nodeB.neighIID4x_repos
nodeB_repos.print_repos()

# Getting node via neighbor
print ("Trying to get node via neighIID4x")
print("Node B myIID4x = 2 neighIID4x = 1")
print("directly calling from my_iid_repos")
dhn_direct = my_iid_repos.iid_get_node_by_myIID4x(2)
print (dhn_direct)
print("calling from nodeB_repos")
dhn_indirect = nodeB.get_node_by_neighIID4x(my_iid_repos, 1)
print(dhn_indirect)

# # Get entry with IID 1
print ("Get entry with IID 1")
print(my_iid_repos.get_iid_entry(1))

# Freeing IID 1
print ("my_iid_repos after removing myIID4x = 1")
my_iid_repos.iid_free(1)
my_iid_repos.print_repos()

# # Purging the repository
print ("Purging the repository")
my_iid_repos.purge_repos()
my_iid_repos.print_repos()