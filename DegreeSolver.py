import networkx as nx
import time
from Solver import *

class DegreeSolver(Solver):

    def run(self):
        t1 = time.time()
        degrees = [(node, self.G.degree([node])[node]) for node in self.G.nodes() if node not in self.seeds]
        blocked = []
        degrees.sort(key=lambda t: t[1])
        for i in range(self.k):
            blocked.append(degrees.pop()[0])
        t2 = time.time()

        self.log['Total time'] = (t2-t1)
        self.log['Blocked nodes'] = [int(node) for node in blocked]
