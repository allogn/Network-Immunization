import networkx as nx
import time
import numpy as np
from Solver import *

class RandomSolver(Solver):

    def run(self):
        t1 = time.time()
        random_blocked_set = np.random.choice([node for node in self.G.nodes() if node not in self.seeds], self.k, replace=False)
        t2 = time.time()

        self.log['Total time'] = (t2-t1)
        self.log['Blocked nodes'] = [int(node) for node in random_blocked_set]
