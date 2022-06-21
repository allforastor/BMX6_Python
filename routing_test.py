from dataclasses import dataclass
import time
import frames
import nodes
from frames import header, OGM_ADV, OGM_ADV_msg, OGM_ACK, OGM_ACK_msg   # modified
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
# ver 6.21.2022 - included ogm frame sqn number testing from ogm aggreg node, polished initialization of frames and msgs
#

# creation of msgs and frame    # modified
msg1 = OGM_ADV_msg()
msg2 = OGM_ADV_msg()
msg3 = OGM_ADV_msg()
msg4 = OGM_ADV_msg()
msg5 = OGM_ADV_msg()
msg6 = OGM_ADV_msg()
ogmframe1 = OGM_ADV(header())
ogmframe1.ogm_adv_msgs.extend([msg1, msg2, msg3])


########################################################################################################
#test iid_offset generation
#
#initialize node A's iid repo
nodeA = iid_repos(dict(), 0)
nodeA.arr[0] = "Hash_A"
nodeA.arr[1] = "Hash_B"
nodeA.arr[2] = "Hash_C"

#initialize local node for node A, store originator
nodeA_local = local_node(" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                   " ", " ", " ")  # stores originator info

#initialize node B's iid repo
nodeB = iid_repos(dict(), 0)
nodeB.arr[0] = "Hash_B"
nodeB.arr[1] = "Hash_A"
nodeB.arr[2] = "Hash_C"

#initialize local node for node B, store originator
nodeB_local = local_node(" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                   " ", " ", " ")  # stores originator info

# initialize neighbor repository of B for A
B_neighnodeA = neigh_node(0, 0, 0, 0, iid_repos({0: 1, 1: 0, 2: 2}, 0), 0, 0, 0, 0)

#initialize node C's iid repo
nodeC = iid_repos(dict(), 0)
nodeC.arr[0] = "Hash_C"
nodeC.arr[1] = "Hash_B"
nodeC.arr[2] = "Hash_A"

#initialize local node for node C, store originator
nodeC_local = local_node(" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                   " ", " ", " ")  # stores originator info

#initialize neighbor repository of C for B
C_neighnodeB = neigh_node(0,0,0,0,iid_repos({0:1, 1:2, 2:0},0),0,0,0,0)


#display nodes and frames
nodeA.print_repos()
nodeB.print_repos()
B_neighnodeA.neighIID4x_repos.print_repos()
nodeC.print_repos()
C_neighnodeB.neighIID4x_repos.print_repos()


# node A
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display current iid offset (before)
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("--------------------")
nodeA_local.set_iid_offset_for_ogm_msg(ogmframe1, nodeB)    # set iid_offset of the msgs in frame
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node A:", nodeA_local.orig_routes)      # print stored originator info

print("--------------------")
print("traversing to node B")
print("--------------------")

# traverse to node B
nodeB_local.set_iid_offset_for_ogm_msg(ogmframe1, B_neighnodeA)     # set iid_offset of the msgs in frame
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node B:", nodeB_local.orig_routes)      # print stored originator info
neigh_node.get_node_by_neighIID4x(nodeB, B_neighnodeA, nodeA_local.orig_routes)     # obtain hash of originator

print("--------------------")
print("traversing to node C")
print("--------------------")

# traverse to node C
nodeC_local.set_iid_offset_for_ogm_msg(ogmframe1, C_neighnodeB)     # set iid_offset of the msgs in frame
for idx, msgs in enumerate(ogmframe1.ogm_adv_msgs):         # display updated iid offset
    print("IID offsets of the msg{}: {}".format(idx+1, msgs.iid_offset))
print("Stored IID in node C:", nodeC_local.orig_routes)      # print stored originator info
neigh_node.get_node_by_neighIID4x(nodeC, C_neighnodeB, nodeB_local.orig_routes)     # obtain hash of originator

############################################################################################################################

# test aggregated ogm frame sqn no  # modified
#ogmframe2 = OGM_ADV(header())
#nodeA_ogm_aggreg = ogm_aggreg_node()
#nodeA_ogm_aggreg.ogm_advs.extend([ogmframe1, ogmframe2])
#nodeA_router = router_node("", "", "", 0, 0, "")
#
#nodeA_ogm_aggreg.set_sqn_no_ogmframes_and_msgs()  # set aggregated sqqn no for each frame
#
#ogmframe3 = OGM_ADV(header())
#ogmframe3.ogm_adv_msgs.extend([msg4, msg5, msg6])
#nodeA_ogm_aggreg.ogm_advs.append(ogmframe3)
#nodeA_ogm_aggreg.set_sqn_no_ogmframes_and_msgs()
##print(ogmframe3)
#nodeA_ogm_aggreg.ogm_advs.remove(ogmframe2)
#nodeA_ogm_aggreg.set_sqn_no_ogmframes_and_msgs()
#for things in nodeA_ogm_aggreg.ogm_advs:
#    print(things)
#
#print(nodeA_ogm_aggreg.aggregated_msgs_sqn_no, nodeA_ogm_aggreg.sqn)
##########################################################################################
# test ack ogm frame
#nodeA_orig = orig_node(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
#result = nodeA_orig.ack_ogm_frame(ogmframe1)
#
#for x in result:
#    print(x.agg_sqn_no)

