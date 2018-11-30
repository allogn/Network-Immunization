import networkx as nx
from networkx.algorithms import approximation
import random
import sys
import time
import os
import argparse
import numpy as np
import hashlib
from scipy.sparse import csr_matrix

class Generator:
    def __init__(self, params):
        self.params = params
        self.generators = {
            'powerlaw_cluster': lambda: nx.powerlaw_cluster_graph(params["n"], params["m"], params["p"]),
            'grid': lambda: nx.convert_node_labels_to_integers(nx.grid_2d_graph(params['n'], params['n'])),
            'path': lambda: nx.path_graph(params["n"]),
            'binomial': lambda: nx.fast_gnp_random_graph(params['n'], params['p']),
            'watts_strogatz': lambda: nx.watts_strogatz_graph(params['n'], params['k'], params['p']),
            'karate': lambda: nx.karate_club_graph(),
            'gaussian_random_partition': lambda: nx.gaussian_random_partition_graph(params['n'], params['s'], params['v'], params['p_in'], params['p_out'])
        }

    def gen_graph_id(self):
        return str(self.get_static_hash(str(int(time.time())) + str(random.randint(10000, 99999)) + "_".join([str(self.params[p]) for p in self.params])))

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

    @staticmethod
    def analyze_graph(G):
        G.graph['directed'] = nx.is_directed(G)
        G_und = G.to_undirected()
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

    @staticmethod
    def get_static_hash(string):
        h = int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16)
        return h

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate graph with seeds")
    parser.add_argument("graph_type", type=str)
    parser.add_argument("graph_outfile", type=str)
    parser.add_argument("seed_outfile", type=str)
    parser.add_argument("-s", "--number_of_seeds", type=str, default=1)
    parser.add_argument("-b", "--both_directions", type=int, default=1)
    parser.add_argument("-w", "--weight_scale", type=float, default=0.3)
    parser.add_argument("-p", "--other_params", type=str, nargs="*")

    args = parser.parse_args()
    other_params = {"graph_type": args.graph_type,
                    "both_directions": args.both_directions,
                    "weight_scale": args.weight_scale,
                    "random_weight": 1}
    if args.other_params:
        for i in range(int(len(args.other_params)/2)):
            if args.other_params[2*i+1].isdigit():
                other_params[args.other_params[2*i]] = int(args.other_params[2*i+1])
            else:
                other_params[args.other_params[2*i]] = args.other_params[2*i+1]
    z = dict(other_params)
    gen = Generator(z)
    G = next(gen.generate())
    nx.write_gpickle(G, args.graph_outfile)
    n = args.number_of_seeds
    seeds = np.random.choice([node for node in G.nodes()], n, replace=False)
    np.savetxt(args.seed_outfile, seeds, fmt="%1u")
    print("Done.")
