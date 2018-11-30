import helpers
import time
import json

class Solver:
    def __init__(self, G, seeds, k, **params):
        if len(G) == 0:
            raise Exception("Graph can not be empty")
        if len(seeds) == 0:
            raise Exception("Seeds can not be empty")
        if k > len(G) - len(seeds):
            raise Exception("Seeds can not be blocked: too large k")
        if k == 0:
            raise Exception("k should be greater than 0")
        self.G = G.copy()
        self.seeds = [int(node) for node in seeds]
        self.k = int(k)
        self.log = {}
        self.log['created'] = time.time()
        self.params = params
        self.clear()

    def clear(self):
        pass

    def get_name(self):
        return self.__class__.__name__
