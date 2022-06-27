import string
import sys
import hashlib
from frames import DESC_ADV_msg
from nodes import iid_repos, neigh_node
from dataclasses import dataclass, fields

my_iid_repos = iid_repos()      # local IID repository that should hold all dhash_nodes

# def hash_description(msg): #hashes description from message
#     dhash = hashlib.sha1()

#     for field in fields(msg):
#         if (field.name == 'trans_iid4x'):
#             iid = msg.trans_iid4x
#         else: 
#             x = getattr(msg, field.name)
#             try:
#                 dhash.update(x.encode())
#             except AttributeError:
#                 x = "% s" % x
#                 dhash.update(x.encode())

#     result = dhash.hexdigest()
    
#     # map description hash to its corresponding iid
#     my_iid_repos.arr[iid] = result

def iid_new_myIID4x(dhnode):
    pass

def iid_set_neighIID4x(neigh_rep, neighIID4x, myIID4x):
    pass


# Declaring test repository values
# Node A (this node)
my_iid_repos.arr[0] = 'HASH_A'
my_iid_repos.arr[1] = 'HASH_B'
my_iid_repos.arr[2] = 'HASH_C'
# Node B (neighbor)
nodeB = neigh_node(0,0,0,0,iid_repos(0,0,0,0,{0:1, 1:2, 2:0},0),0,0,0,0) 

my_iid_repos.print_repos()
nodeB.neighIID4x_repos.print_repos()

# Getting Node C's hash value via my repository vs. node B's repository
print("Hash of Node C accdg to Node A: " + my_iid_repos.arr[2])
print("Hash of Node C accdg to Node B: ")
nodeB.get_node_by_neighIID4x(1)