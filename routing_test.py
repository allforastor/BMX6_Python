from dataclasses import dataclass
import time
import socket
import frames
import nodes
from frames import header, OGM_ADV, OGM_ADV_msg, OGM_ACK, OGM_ACK_msg   
from nodes import local_node, router_node, iid_repos, neigh_node, ogm_aggreg_node, orig_node


##############################################################################
# TESTING AREA
##############################################################################


# sample topology
#
#       A ------------ B ------------ C
# originator of
#   OGM frame
#
#
# IID repo of A
# ----------------
# | IID |  Hash  |
# |  0  | Hash_A |
# |  1  | Hash_B |
# |  2  | Hash_C |
# ----------------
#                                                   A
#-----------------------------------------------------------------------------------------------------------------
#
# Neighbor repo of B for A                     IID repo of B
# -----------------------------                ----------------
# | IID |  Node B equivalent  |                | IID |  Hash  |
# |  0  |          1          |                |  0  | Hash_B |
# |  1  |          0          |                |  1  | Hash_A |
# |  2  |          2          |                |  2  | Hash_C |
# -----------------------------                ----------------
#
#                                                    B
#-----------------------------------------------------------------------------------------------------------------
#
# Neighbor repo of C for B                     IID repo of C
# -----------------------------                ----------------
# | IID |  Node B equivalent  |                | IID |  Hash  |
# |  0  |          1          |                |  0  | Hash_C |
# |  1  |          2          |                |  1  | Hash_B |
# |  2  |          0          |                |  2  | Hash_A |
# -----------------------------                ----------------
#
#                                                    C
#-----------------------------------------------------------------------------------------------------------------
# ver 6.29.2022 - improvements as how it would be expected in runtime
# assumptions: local_node, iid_repos, neigh_node are already instantiated
#

#initialize node A's iid repo
nodeA = iid_repos(dict(), 0)
nodeA.arr[0] = "Hash_A"
nodeA.arr[1] = "Hash_B"
nodeA.arr[2] = "Hash_C"

#initialize local node for node A, store originator
nodeA_local = local_node()  # stores originator info

#initialize node B's iid repo
nodeB = iid_repos(dict(), 0)
nodeB.arr[0] = "Hash_B"
nodeB.arr[1] = "Hash_A"
nodeB.arr[2] = "Hash_C"

#initialize local node for node B, store originator
nodeB_local = local_node()# stores originator info

# initialize neighbor repository of B for A
B_neighnodeA = neigh_node(0, 0, 0, 0, iid_repos({0: 1, 1: 0, 2: 2}, 0), 0, 0, 0, 0)

#initialize node C's iid repo
nodeC = iid_repos(dict(), 0)
nodeC.arr[0] = "Hash_C"
nodeC.arr[1] = "Hash_B"
nodeC.arr[2] = "Hash_A"

#initialize local node for node C, store originator
nodeC_local = local_node()  # stores originator info

#initialize neighbor repository of C for B
C_neighnodeB = neigh_node(0,0,0,0,iid_repos({0:1, 1:2, 2:0},0),0,0,0,0)


#display nodes and frames
nodeA.print_repos()
nodeB.print_repos()
B_neighnodeA.neighIID4x_repos.print_repos()
nodeC.print_repos()
C_neighnodeB.neighIID4x_repos.print_repos()


# creation of msgs and frame
msg1 = OGM_ADV_msg()
msg2 = OGM_ADV_msg()
msg3 = OGM_ADV_msg()
msg4 = OGM_ADV_msg()
msg5 = OGM_ADV_msg()
msg6 = OGM_ADV_msg()
ogmframe1 = OGM_ADV(header())
ogmframe1.ogm_adv_msgs.extend([msg1, msg2, msg3])   # for loop for every new msgs in actual runtime

#after msgs are done being collected to the frame and is ready to be sent out (every 5s)
nodeA_ogm_aggreg_node = ogm_aggreg_node()
nodeA_ogm_aggreg_node.update_self(ogmframe1)
nodeA_ogm_aggreg_node.set_sqn_no_ogmframes_and_msgs()
print(nodeA_ogm_aggreg_node)

# node A
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display current iid offset (before)
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
nodeA_local.orig_routes = nodeA_ogm_aggreg_node.set_iid_offset_for_ogm_msg(nodeB)     # set iid offset     # no connection yet between local node and other nodes hence this implementation
print("--------------------------")
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node A:", nodeA_local.orig_routes)      # print stored originator info

print("--------------------")
print("traversing to node B")
print("--------------------")

# traverse to node B
nodeB_ogm_aggreg_node = ogm_aggreg_node()                       # create aggreg node for B
nodeB_ogm_aggreg_node.update_self(ogmframe1)                    # update node B
nodeB_local.orig_routes = nodeB_ogm_aggreg_node.set_iid_offset_for_ogm_msg(B_neighnodeA)     # set iid_offset  # no connection yet between local node and other nodes hence this implementation
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset                # presentation purposes
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node B:", nodeB_local.orig_routes)      # print stored originator info             # presentation purposes
B_neighnodeA.get_node_by_neighIID4x(nodeB, nodeA_local.orig_routes)     # obtain hash of originator     # presentation purposes

print("--------------------")
print("traversing to node C")
print("--------------------")

# traverse to node C
nodeC_ogm_aggreg_node = ogm_aggreg_node()                       # create aggreg node for C
nodeC_ogm_aggreg_node.update_self(ogmframe1)                    # update node C
nodeC_local.orig_routes = nodeC_ogm_aggreg_node.set_iid_offset_for_ogm_msg(C_neighnodeB)     # set iid_offset  # no connection yet between local node and other nodes hence this implementation
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset                # presentation purposes
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node C:", nodeC_local.orig_routes)      # print stored originator info             # presentation purposes
C_neighnodeB.get_node_by_neighIID4x(nodeC, nodeB_local.orig_routes)     # obtain hash of originator     # presentation purposes



