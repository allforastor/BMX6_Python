import string
import sys
import hashlib
from frames import DESC_ADV_msg
from nodes import iid_repos, neigh_node

my_iid_repos = iid_repos(dict(),0)

def hash_description(msg): #hashes description from message
    dhash = hashlib.sha1()

    for x in msg[1:]:
        try:
            dhash.update(x.encode())
        except AttributeError:
            dhash.update(str(x).encode())

    result = dhash.hexdigest()
    
    # return result
    my_iid_repos.arr[msg[0]] = result

def get_node_by_neighIID4x(nnode, neighIID4x):
    if (nnode.get_myIID4x_by_neighIID4x(neighIID4x) == -1):
        # send HASH_REQ message
        print ("Neighbor IID unknown. Sending Hash Request")
    else:
        myIID4x = nnode.get_myIID4x_by_neighIID4x(neighIID4x)
        
        if (my_iid_repos.arr[myIID4x] == KeyError):
            # send DESC_REQ message
            print ("Node description unknown. Sending Description Request")
        else:
            print("Retrieved hash from local IID repository: " + my_iid_repos.arr[myIID4x])
            

# Declaring test repository values
# Node A (this node)
my_iid_repos.arr[0] = 'HASH_A'
my_iid_repos.arr[1] = 'HASH_B'
my_iid_repos.arr[2] = 'HASH_C'
# Node B (neighbor)
nodeB = neigh_node(0,0,0,0,iid_repos({0:1, 1:2, 2:0},0),0,0,0,0) 

my_iid_repos.print_repos()
nodeB.neighIID4x_repos.print_repos()

# Getting Node C's hash value via my repository vs. node B's repository
print("Hash of Node C accdg to Node A: " + my_iid_repos.arr[2])
print("Hash of Node C accdg to Node B: ")
get_node_by_neighIID4x(nodeB, 1)





