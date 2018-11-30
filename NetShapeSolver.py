import networkx as nx
import numpy as np
from scipy.linalg import eigh
import time
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Solver import *


class NetShapeSolver(Solver):
    def clear(self):
        np.warnings.filterwarnings('ignore')
        self.epsilon = self.params['epsilon']

    def transform_graph_to_matrix(self):
        self.nodelist = [n for n in self.G.nodes()]
        self.inverse_nodelist = {}
        for i in range(len(self.nodelist)):
            self.inverse_nodelist[self.nodelist[i]] = i
        F = nx.to_numpy_matrix(self.G, nodelist=self.nodelist, weight='weight')
        return F

    def init_variables(self):
        self.F = self.transform_graph_to_matrix()
        self.Delta = self.get_delta(self.F)
        self.R = np.sqrt(self.k)*np.max(np.abs(self.Delta))
        self.T = int(math.ceil((self.R/self.epsilon)**2))

        self.x = np.zeros(len(self.G))
        self.x_star = self.x.copy()

    def get_delta(self, F):
        delta = -F.copy()
        for s in self.seeds:
            node_index = self.inverse_nodelist[s]
            delta[node_index, :] = 0
        return delta

    def calculate_x_star(self):
        self.init_variables()
        for iteration in range(1,self.T+1):
            self.perform_iteration(iteration)
        return self.x_star

    def get_hazard_result(self):
        return np.multiply((1-(1/self.T)*self.get_x_matrix(self.x_star)), self.F), self.x_star

    def perform_iteration(self, iteration):
        M = self.F + np.multiply(self.get_x_matrix(self.x), self.Delta)
        M2 = 1/2*(M+M.transpose())
        N = M2.shape[0]
        W, V = eigh(M2, eigvals=(N-1, N-1), type=1, overwrite_a=True)
        max_eig = np.real(W[0])
        max_eigvec = V[:, 0].reshape(N, 1)

        u = max_eigvec
        subgrad_step = np.dot(u, u.transpose())
        Y = np.multiply(self.get_x_matrix(self.x), self.Delta) - self.R/np.sqrt(iteration) * subgrad_step
        self.x = self.get_projection(self.Delta, Y)
        self.x_star += np.real(self.x)
        return max_eig

    @staticmethod
    def get_x_matrix(x):
        x = np.reshape(x, (len(x), 1)).copy()
        return np.repeat(x, x.shape[0], axis=1)

    def get_projection(self, delta, y):
        delta_prime = self.get_delta_prime(delta)
        y_prime = self.get_y_prime(y, delta, delta_prime)

        N = len(self.G)
        mu1 = 2*np.multiply(y_prime, delta_prime)
        mu2 = mu1-2*delta_prime**2
        mu = np.concatenate((mu1, mu2))

        pi = np.flip(np.argsort(mu), axis=0)
        assert(mu[pi[0]] >= mu[pi[-1]])
        d = 0
        s = 0
        i = 0
        while s <= self.k and mu[pi[i]] >= 0:
            if pi[i] < N:
                if delta_prime[pi[i]] == 0:
                    i += 1
                    continue
                d += 1/(2*delta_prime[pi[i]]**2)
            else:
                if delta_prime[pi[i]-N] == 0:
                    i += 1
                    continue
                d -= 1/(2*delta_prime[pi[i]-N]**2)
            if mu[pi[i]] != mu[pi[i+1]]:
                s += d * (mu[pi[i]] - mu[pi[i+1]])
            i += 1
        z = np.max((0, mu[pi[i]] + (s-self.k)/d))

        x_prime = 2 * np.multiply(delta_prime, y_prime) - z
        x_prime = np.multiply(x_prime, np.reciprocal(2*delta_prime**2))
        x_prime = np.minimum(x_prime, 1)
        x_prime = np.maximum(x_prime, 0)
        np.nan_to_num(x_prime, copy=False)
        return x_prime

    @staticmethod
    def get_delta_prime(delta):
        return np.ravel(np.sqrt(np.sum(np.power(delta, 2), axis=1)))

    @staticmethod
    def get_y_prime(y, delta, delta_prime):
        y_prime = np.ravel(np.sum(np.multiply(y, delta), axis=1))
        dp = delta_prime.copy()
        dp[dp == 0] = 1
        y_prime /= dp
        return y_prime

    def get_blocked(self):
        node_indexes = np.argsort(self.x_star)[-self.k:]
        return [self.nodelist[i] for i in node_indexes]

    def run(self):
        # check if there is at least one edge from seeds
        check = False
        for s in self.seeds:
            for n in self.G.neighbors(s):
                check = True
                break
            if check:
                break

        t1 = time.time()
        if not check:
            self.log['Error'] = "Trivial problem: no paths from seeds"
            blocked = [n for n in self.G if n not in self.seeds][:self.k]
        else:
            self.calculate_x_star()
            blocked = self.get_blocked()
        t2 = time.time()

        self.log['Total time'] = (t2-t1)
        self.log['Blocked nodes'] = [int(node) for node in blocked]
