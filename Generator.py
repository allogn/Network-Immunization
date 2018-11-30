import networkx as nx
from networkx.algorithms import approximation
import random
import sys
import time
import os
import argparse
import numpy as np
import scipy.io
import logging
from scipy.sparse import csr_matrix
sys.path.append(os.path.join(os.environ['PHD_ROOT'], 'imin', 'src'))
sys.path.append(os.path.join(os.environ['PHD_ROOT'], 'imin', 'scripts'))
import helpers
from FileManager import *

class Generator:
    def __init__(self, params):
        self.params = params
        self.generators = {
            'powerlaw_cluster': lambda: nx.powerlaw_cluster_graph(params["n"], params["m"], params["p"]),
            'stanford': lambda: self.get_stanford_graph(),
            'gnutella': lambda: self.get_gnutella_graph(),
            'grid': lambda: nx.convert_node_labels_to_integers(nx.grid_2d_graph(params['n'], params['n'])),
            'path': lambda: nx.path_graph(params["n"]),
            'binomial': lambda: nx.fast_gnp_random_graph(params['n'], params['p']),
            'watts_strogatz': lambda: nx.watts_strogatz_graph(params['n'], params['k'], params['p']),
            'karate': lambda: nx.karate_club_graph(),
            'vk': lambda: self.get_vk_graph(),
            'gaussian_random_partition': lambda: nx.gaussian_random_partition_graph(params['n'], params['s'], params['v'], params['p_in'], params['p_out'])
        }

    def gen_graph_id(self):
        return str(helpers.get_static_hash(str(int(time.time())) + str(random.randint(10000, 99999)) + "_".join([str(self.params[p]) for p in self.params])))

    def generate(self, number_of_graphs=1):
        for i in range(number_of_graphs):
            G = self.generators[self.params["graph_type"]]()
            if self.params["graph_type"] != 'vk':
                if self.params["graph_type"] not in ["gnutella", "stanford"]:
                    G = self.add_random_directions(G, self.params["both_directions"])
                else:
                    if self.params["both_directions"]:
                        raise Exception("Not implemeted")
                G = self.assign_weights(G, self.params["weight_scale"], self.params["random_weight"])
            G.graph['graph_id'] = self.gen_graph_id()
            G.graph.update(self.params)
            yield G

    @staticmethod # used in tests
    def assign_weights(G, weight_scale, random_weight):
        if random_weight:
            for e in G.edges():
                a = np.random.random()*weight_scale
                G[e[0]][e[1]]['weight'] = np.random.random()*weight_scale
        else:
            for e in G.edges():
                G[e[0]][e[1]]['weight'] = weight_scale
        return G

    @staticmethod
    def add_random_directions(G, both=False):
        assert(not nx.is_directed(G))
        dG = nx.DiGraph()
        for e in G.edges():
            if both:
                dG.add_edge(e[0],e[1])
                dG.add_edge(e[1],e[0])
                for key in G[e[0]][e[1]]:
                    dG[e[0]][e[1]][key] = G[e[0]][e[1]][key]
                    dG[e[1]][e[0]][key] = G[e[0]][e[1]][key]
            else:
                if np.random.random() < 0.5:
                    dG.add_edge(e[0],e[1])
                    for key in G[e[0]][e[1]]:
                        dG[e[0]][e[1]][key] = G[e[0]][e[1]][key]
                else:
                    dG.add_edge(e[1],e[0])
                    for key in G[e[1]][e[0]]:
                        dG[e[1]][e[0]][key] = G[e[0]][e[1]][key]
        return dG

    def get_stanford_graph(self):
        mat = scipy.io.loadmat(os.path.join(os.environ['ALLDATA_PATH'], 'imin', 'wb-cs-stanford.mat'))
        sparse = mat['Problem'][0][0][2]
        m = csr_matrix(sparse)
        g = nx.DiGraph()
        G = nx.from_numpy_matrix(m.toarray(), create_using=g)
        return G
        # g = G
        # g = G.to_undirected() -- mistake
        # nodeset = []
        # for g1 in nx.connected_components(g):
        #     if len(g1) > 1000:
        #         nodeset = g1
        #         break
        # return G.subgraph(nodeset).copy()

    def get_gnutella_graph(self):
        edges = []
        with open(os.path.join(os.environ['ALLDATA_PATH'], 'imin', 'p2p-Gnutella31.txt')) as f:
            nodes, edge_count = f.readline().split()
            nodes = int(nodes)
            edge_count = int(edge_count)
            for line in f:
                edges.append((int(line.split()[0]), int(line.split()[1])))
        assert(len(edges) == edge_count)
        G = nx.DiGraph()
        G.add_nodes_from(range(nodes))
        G.add_edges_from(edges)
        return G

    def get_vk_graph(self):
        G = nx.read_gpickle(os.path.join(os.environ['ALLDATA_PATH'], 'imin', 'vk_graph_cleaned.pkl'))
        return G

    @staticmethod
    def analyze_graph(G):
        G.graph['directed'] = nx.is_directed(G)
        G_und = G.to_undirected()
        # if G.graph['directed']:
        #     G.graph['weakly_connected_components'] = nx.number_weakly_connected_components(G)
        #     G.graph['largest_weak_component'] = max(nx.weakly_connected_components(G), key=len)
        #     G.graph['strongly_connected_components'] = nx.number_strongly_connected_components(G)
        # else:
        G.graph['connected_components'] = nx.number_connected_components(G_und)
        G.graph['largest_component'] = len(max(nx.connected_components(G_und), key=len))

        logging.info("Graph ID {}: components analyzed.".format(G.graph['graph_id']))
        G.graph['average_clustering'] = approximation.average_clustering(G_und)
        logging.info("Graph ID {}: clustering analyzed.".format(G.graph['graph_id']))
        degrees = [d for n, d in G.degree()]
        G.graph['min_degree'] = min(degrees),max(degrees),np.mean(degrees),np.median(degrees)
        G.graph['max_degree'] = max(degrees)
        G.graph['avg_degree'] = np.mean(degrees)
        G.graph['std_degree'] = np.std(degrees)
        G.graph['median_degree'] = np.median(degrees)
        logging.info("Graph ID {}: degrees analyzed.".format(G.graph['graph_id']))
