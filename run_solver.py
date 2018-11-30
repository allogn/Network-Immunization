import os
import sys
import time
import hashlib
import argparse
import numpy as np
import signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from iMinSolver import *
from DegreeSolver import *
from DomSolver import *
from RandomSolver import *
from NetShapeSolver import *
from NetShieldSolver import *
from Walk8Solver import *

if __name__ == "__main__":
    t1 = time.time()
    parser = argparse.ArgumentParser(description="Run solver on a single graph with seeds")
    parser.add_argument("graph", type=str)
    parser.add_argument("seeds", type=str)
    parser.add_argument("nodes_to_block", type=int)
    parser.add_argument("algorithm", type=str)
    parser.add_argument("-j", "--simulation_iterations", type=int, default="100")
    parser.add_argument("-o", "--outfile", type=str, default="a.out")
    parser.add_argument("-p", "--other_params", type=str, nargs="*")
    args = parser.parse_args()

    G, seeds = helpers.load_graph_and_seed(args.graph, args.seeds)
    k = args.nodes_to_block
    problem_params = {}
    if args.problem_params:
        for i in range(int(len(args.problem_params)/2)):
            if args.problem_params[2*i+1].isdigit():
                problem_params[args.problem_params[2*i]] = int(args.problem_params[2*i+1])
            else:
                problem_params[args.problem_params[2*i]] = args.problem_params[2*i+1]
    z = dict(problem_params)

    Solver = eval(args.algorithm + "Solver")
    solver = Solver(G, seeds, k, **z)
    solver.run()
    print("%s blocked %d nodes in a graph of size %d." % (solver.get_name(), k, len(G)))
    print("Running simulations...")
    results = []
    for i in range(args.simulation_iterations):
        results.append(simulation.simulate(G, seeds, solver.log['Blocked nodes'])['saved nodes'])
    solver.log.update({"saved mean": np.mean(results), "saved std": np.std(results)})
    solver.save_log(args.outfile)
    print("Time: %1.5fs; Objective (saved): %1.1f pm %1.1f; Total time: %1.5s" % (solver.log["Total time"], np.mean(results), np.std(results), (time.time() - t1)))
    print("Logs saved to {}.".format(args.outfile))
