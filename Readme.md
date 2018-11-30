# Introduction

The repository contains source files for Node Immunization algorithms. Given a directed network and a set of seed nodes, the problem is to select k nodes which to block/immunize so that the expected influence spread in the network is minimized. Simulations performed under Independent Cascade model.

Supported algorithms:
- Degree : degree heuristic
- Dom : DAVA, dominator tree based algorithm
- NetShape : Convex optimization of a hazard matrix
- NetShield : Minimization of a shield value
- Random : Random selection of blocked nodes

# Requirements

Required libraries: NetworkX, SciPy, NumPy.
```bash
pip3 install networkx scipy numpy
```

The repository is provided by Pipfile.

# Data

All algorithms require two files with a network and a seed set, in pickled NetworkX format for the network and csv file with node ids for seeds. Graphs should have 'graph_id' attribute.

For synthetic data, Generator class is used to generate random networks according to several growth models. Real-world networks are not included in the repository.

# Usage

## Graph Generation

```python
python3 Generator.py graph_type [-p other params]
```

For example:
```python
python3 Generator.py grid a.pkl b.csv -p n 10
```

## Benchmarking

The script run_solver.py applies an algorithm to a graph with seeds, and runs simulations for the objective evaluations (number of saved nodes in the graph).

Minimum usage:
```python
python3 run_solver.py path_to_graph path_to_seeds k algorithm_name
```

For other parameters run:
```python
python3 run_solver.py -h
```

If using pipenv, then all commands should precede by `pipenv run`.

# Notes

Walk8 Solver is not available as the code was provided by authors of "Scalable Approximation Algorithm for Network Immunization" and the algorithm is implemented in MATLAB.
