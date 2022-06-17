from dataclasses import dataclass
from frames import header, OGM_ADV, OGM_ADV_msg
from nodes import local_node, router_node, iid_repos, neigh_node


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


# creation of msgs and frame
msg1 = OGM_ADV_msg(None, None, None, 1)
msg2 = OGM_ADV_msg(None, None, None, 2)
msg3 = OGM_ADV_msg(None, None, None, 3)
ogmframe1 = OGM_ADV(header(" ", " ", " ", " "), " ", " ", [" "], [msg1, msg2, msg3])  # whitespaces are placeholder values

#display nodes and frames
nodeA.print_repos()
nodeB.print_repos()
B_neighnodeA.neighIID4x_repos.print_repos()
nodeC.print_repos()
C_neighnodeB.neighIID4x_repos.print_repos()
print(ogmframe1)

# node A
print("starting ........")
nodeA_local.set_iid_offset_for_ogm_msg(ogmframe1, nodeB)    # set iid_offset of the msgs in frame
print(ogmframe1)        # print updated ogm frame
print(nodeA_local)      # print stored originator info

print("--------------------")
print("traversing to node B")
print("--------------------")

# traverse to node B
nodeB_local.set_iid_offset_for_ogm_msg(ogmframe1, B_neighnodeA)     # set iid_offset of the msgs in frame
print(ogmframe1)        # print updated ogm frame
print(nodeB_local)      # print stored originator info
neigh_node.get_node_by_neighIID4x(nodeB, B_neighnodeA, nodeA_local.orig_routes)     # obtain hash of originator

print("--------------------")
print("traversing to node C")
print("--------------------")

# traverse to node C
nodeC_local.set_iid_offset_for_ogm_msg(ogmframe1, C_neighnodeB)     # set iid_offset of the msgs in frame
print(ogmframe1)        # print updated ogm frame
print(nodeC_local)      # print stored originator info
neigh_node.get_node_by_neighIID4x(nodeC, C_neighnodeB, nodeB_local.orig_routes)     # obtain hash of originator
