# Introduction

The repository contains source files for Node Immunization algorithms. Given a directed network and a set of seed nodes, the problem is to select k nodes which to block/immunize so that the expected influence spread in the network is minimized. Simulations performed under Independent Cascade model.

# Requirements

The repository is provided by the pipenv file that includes necessary requirements.

# Data

All algorithms require two files with a network and a seed set, in pickled NetworkX format for the network and csv file with node ids for seeds. Generator class generate random networks according to several growth models.

# Usage

The script run_solver.py applies an algorithm to a graph with seeds, and runs simulations for the objective evaluations (number of saved nodes in the graph).

Minimum usage:
'''
python3 run_solver.py path_to_graph path_to_seeds k algorithm_name
'''

'python3 run_solver.py' for other parameters.

Supported algorithms:
- Degree : degree heuristic
- Dom : DAVA, dominator tree based algorithm
- NetShape : Convex optimization of a hazard matrix
- NetShield : Minimization of a shield value
- Random : Random selection of blocked nodes

# Notes

Walk8 Solver is not available as the code was provided by authors of "Scalable Approximation Algorithm for Network Immunization" and the algorithm is implemented in MATLAB.
