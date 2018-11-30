import time
import networkx as nx
import random
import numpy as np
import logging
from collections import defaultdict
import warnings

class Simulator():

    def __init__(self, G, seeds):
        self.G = G
        self.seeds = seeds
        self.blocked = {}
        self.log = {}

    def add_blocked(self, name, node_set):
        self.blocked[name] = node_set

    def run(self, iterations):
        assert(sum([not self.G.has_node(n) for n in self.seeds]) == 0)
        for key in self.blocked:
            blocked_list = self.blocked[key]
            assert(sum([not self.G.has_node(n) for n in blocked_list]) == 0) # any blocked or seed node should exist in the graph
        self.log['iterations'] = iterations
        iteration_results = []
        for i in range(iterations):
            iteration_results.append(self.run_iteration())
        self.log.update(self.merge_results_across_iterations(iteration_results))
        return self.log

    def run_iteration(self):
        return self.simuation_as_possible_world()

    def simuation_as_possible_world(self):
        '''
        Allows to calculate the number of saved nodes
        '''
        t1 = time.time()
        front_nodes = self.seeds
        active_series = []
        active_series.append(len(front_nodes))
        active = set()
        active.update(self.seeds)

        iterations = 0
        active_edges = set()
        active_subgraph = nx.DiGraph()
        active_subgraph.add_nodes_from([key for key in active])
        while (len(front_nodes) > 0):
            front_edges = self.get_front_edges(front_nodes)
            active_edges.update(front_edges)
            front_nodes = [e[1] for e in front_edges if e[1] not in active]
            active.update(front_nodes)
            active_series.append(active_series[-1]+len(front_nodes))
            iterations += 1
        active_subgraph.add_edges_from(active_edges)
        results = {}
        results['iterations until termination in unblocked graph'] = iterations
        results['active nodes in unblocked graph'] = len(active_subgraph)
        results['solvers'] = {}
        for blocked_set_name in self.blocked:
            blocked_list = self.blocked[blocked_set_name]
            results['solvers'][blocked_set_name] = {}
            active_subgraph_with_blocked = active_subgraph.subgraph([node for node in active_subgraph.nodes() if node not in blocked_list])
            active_subgraph_with_blocked = self.get_reachable_subgraph_from_seeds(active_subgraph_with_blocked)
            activated_node_amount = len(active_subgraph_with_blocked)
            saved_node_amount = results['active nodes in unblocked graph'] - activated_node_amount
            results['solvers'][blocked_set_name]['activated nodes'] = activated_node_amount
            results['solvers'][blocked_set_name]['saved nodes'] = saved_node_amount
            results['solvers'][blocked_set_name]['fraction of saved nodes to active nodes'] = saved_node_amount/results['active nodes in unblocked graph']
        t2 = time.time()
        results['simulation time'] = t2 - t1
        return results

    def get_reachable_subgraph_from_seeds(self, G):
        G = G.copy()
        G.add_node("superseed")
        G.add_edges_from([("superseed", n) for n in self.seeds])
        node_subset = nx.descendants(G, "superseed")
        return G.subgraph(node_subset - set(["superseed"]))

    def get_front_edges(self, front_nodes):
        new_front_edges = []
        for v in front_nodes:
            for u in self.G.successors(v):
                if (np.random.rand() <= self.G[v][u]['weight']):
                    new_front_edges.append((v,u))
        return new_front_edges

    def merge_results_across_iterations(self, results):
        assert(len(results) > 0)
        r = results[0]
        N = len(results)
        merged = {}
        for key in r:
            if key == "solvers":
                continue
            merged[key] = self.get_list_stats([results[i][key] for i in range(N)])
        merged['solvers'] = {}
        for alg in r['solvers']:
            merged['solvers'][alg] = {}
            for key in r['solvers'][alg]:
                l = [results[i]['solvers'][alg][key] for i in range(N)]
                merged['solvers'][alg][key] = self.get_list_stats([results[i]['solvers'][alg][key] for i in range(N)])
        return merged

    def get_list_stats(self, l):
        s = {}
        warnings.simplefilter("ignore", category=RuntimeWarning)
        s['mean'] = np.mean(l)
        s['var'] = np.var(l, ddof=1)
        return s
