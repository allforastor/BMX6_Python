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

def iid_new_myIID4x(dhnode):    #adds new IID entry given a dhash_node
    if (my_iid_repos.arr_size > my_iid_repos.tot_used):
        rand_iid = random.randint(0,my_iid_repos.arr_size)  #could also be max_free because arr_size + 1
        mid = max(1,rand_iid)   # minimum iid value: IID_MIN_USED = 1

        for entry in my_iid_repos.arr[mid:]:
            try:
                if (entry.u8 == mid and entry.dhash_n):     # possibly remove 2nd condition since existing key implies existing node?
                    mid += 1
                    if (mid >= my_iid_repos.arr_size):
                        mid = 1     # return to minimum iid 1
            except KeyError: break
    else:
        mid = my_iid_repos.min_free

    my_iid_repos.iid_set(mid,0,dhnode)

    # return mid  # function should be called as dhash_node->myIID4orig = iid_new_myIID4x(dhnode);

def get_node_by_neighIID4x(neighIID4x):
    pass

# TESTING
# Print initial my_iid_repos
print ("Initial my_iid_repos")
my_iid_repos.print_repos()

# Declaring test message values
msg1 = DESC_ADV_msg(2,'dev1',40,1,0,0,0,0,0,0,0)
msg2 = DESC_ADV_msg(1,'dev2',0,0,0,0,0,0,0,0,0)
dhnode1 = nodes.dhash_node(hash_description(msg1),0,2)
dhnode2 = nodes.dhash_node(hash_description(msg2),0,3)
my_iid_repos.iid_new_myIID4x(dhnode1)

# Print new my_iid_repos
print ("New my_iid_repos after adding dhnode 1")
my_iid_repos.print_repos()

my_iid_repos.iid_new_myIID4x(dhnode2)

print ("New my_iid_repos after adding dhnode 2")
my_iid_repos.print_repos()

# # Get entry with IID 1
# print ("Get entry with IID 1")
# print(my_iid_repos.get_iid_entry(1))

# Purging the repository
print ("Purging the repository")
my_iid_repos.purge_repos()
my_iid_repos.print_repos()


# # Declaring test repository values
# # Node A (this node)
# my_iid_repos.arr[0] = 'HASH_A'
# my_iid_repos.arr[1] = 'HASH_B'
# my_iid_repos.arr[2] = 'HASH_C'
# # Node B (neighbor)
# # nodeB = nodes.neigh_node(0,0,0,0,iid_repos(0,0,0,0,{0:1, 1:2, 2:0},0),0,0,0,0) 

# my_iid_repos.print_repos()
# # nodeB.neighIID4x_repos.print_repos()

# # Getting Node C's hash value via my repository vs. node B's repository
# print("Hash of Node C accdg to Node A: " + my_iid_repos.arr[2])
# print("Hash of Node C accdg to Node B: ")
# # nodeB.get_node_by_neighIID4x(1)