#!/usr/bin/env python3

from tsp_module import *
from sys import stdout, stderr
from time import time


def main():
    try:
        start = time()
        algorithm_choices = {'brute': BruteForce, 'nearest_n': NearestNeighbor,
                            '2opt': TwoOpt, 'sim': Simulated,
                            'nearest_i': NearestInsertion}
        args = TakeArgs()
        algorithm = algorithm_choices[args.algorithm](args.filename)
        path, cost = algorithm.find_shortest_path()
        route = [node.name + ' -> ' for node in path[:-1]] + [path[-1].name]
        stdout.write('\n' + "\033[1m\033[93mPath\033[0m: " + ''.join(route) +
                    '\n' + '\n\033[1m\033[93mCost\033[0m: ' +
                    str(cost) + '\n' + '\n\033[1m\033[93mTime\033[0m: ' +
                    str(time() - start) + '\n\n')
    except Exception:
        stderr.write('Please check your input\n')
        exit(1)


if __name__ == '__main__':
    main()
