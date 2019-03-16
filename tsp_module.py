from math import sqrt, exp
from os.path import isfile
from os import access, R_OK
from sys import stderr, argv
from itertools import permutations
from argparse import ArgumentParser
from abc import ABC, abstractmethod
from random import random, sample


class TakeArgs:

    def __init__(self):

        self.algo_choice = ['nearest_n', '2opt', 'brute', 'sim', 'nearest_i']

        # set the parser
        parser = ArgumentParser(description='Solution for TSP')
        parser.add_argument('filename', type=str)
        parser.add_argument('-a', '--algo',
                            metavar='algorithm',
                            nargs='?',
                            const='nearest_n',
                            default='nearest_n',
                            choices=self.algo_choice,
                            help="choose from " + str(self.algo_choice))
        args = parser.parse_args()

        # set attribute
        self.filename = args.filename
        self.algorithm = args.algo


class Node:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y


class Graph(ABC):

    def __init__(self, filename):
        self.filename = filename
        self.node_list = self.get_node_list(self.filename)

    def get_node_list(self, filename):

        try:
            node_list = []
            with open(filename) as file:
                for line in file:
                    line = line.strip().split(',')
                    node = Node(line[0], float(line[1]), float(line[2]))
                    node_list.append(node)
                return node_list
        except Exception:
            stderr.write('Invalid file\n')
            exit(1)

    def calculate_distance(self, node_1, node_2):
        return sqrt((node_1.x - node_2.x)**2 +
             (node_1.y - node_2.y)**2)

    def calculate_cost(self, path):
        cost = 0
        for i in range(1, len(path)):
            node_1 = path[i-1]
            node_2 = path[i]
            temp_cost = self.calculate_distance(node_1, node_2)
            cost += temp_cost
        return cost

    # set find_shortest_path as an abstract method
    @abstractmethod
    def find_shortest_path(self):
        pass


class BruteForce(Graph):

    def find_shortest_path(self):

        perms = list(permutations(self.node_list))
        temp_list = []

        for perm in perms:
            cost = self.calculate_cost(perm)
            temp_list.append((perm, cost))

        min_path, min_cost = min(temp_list, key=lambda i: i[0])
        return min_path, min_cost


class NearestNeighbor(Graph):

    def find_shortest_path(self):
        node_list = self.node_list.copy()
        min_node = node_list.pop(0)
        path = [min_node]
        cost = 0

        while node_list:
            temp = []

            for node in node_list:
                distance = self.calculate_distance(min_node, node)
                temp.append((node, distance))

            min_node, min_cost = min(temp, key=lambda i: i[1])
            cost += min_cost
            path.append(min_node)
            node_list.remove(min_node)

        return path, cost


class TwoOpt(Graph):

    # create a new 2-adjacent path
    def create_new_path(self, path, cost):

        improved = False
        # i in nodes eligible to be swapped
        for i in range(1, len(path) - 1):
            # j > i
            for j in range(i+1, len(path)):
                new_path = path[:i] + path[j:i-1:-1] + path[j+1:]
                new_cost = self.calculate_cost(new_path)
                # if the new path is better than the current path
                if new_cost < cost:
                    path = new_path
                    cost = new_cost
                    improved = True
            if improved:
                break

        return improved, path, cost

    def find_shortest_path(self):
        path = self.node_list.copy()
        cost = self.calculate_cost(path)
        improved, path, cost = self.create_new_path(path, cost)

        # keep looping if improvement is made
        while improved:
            improved, path, cost = self.create_new_path(path, cost)


        return path, cost


class Simulated(Graph):

    # create a new 2-adjacent path
    def create_new_path(self, path, cost):

        [i, j] = sorted(sample(range(1, len(path)), 2));
        new_path = path[:i] + path[j:j+1] + path[i+1:j] + path[i:i+1] + path[j+1:]
        new_cost = self.calculate_cost(new_path)

        return new_path, new_cost

    def find_shortest_path(self):
        path, cost = NearestNeighbor(self.filename).find_shortest_path()
        temp = 10000

        # increase coolingRate -> decrease temp reduce speed -> more meticulous
        coolingRate = 0.000001

        while (temp > 0.001):
            print('\x1b[31mTEMP: ' + str(temp) + '\x1b[0m')
            new_path, new_cost = self.create_new_path(path, cost)
            # the worse the solution in ratio to the higher temp (the smaller the delta)
            # -> the larger the exponential
            # -> the more likely for the algorithm to accept that solution
            if (cost != new_cost) and (abs(cost - new_cost) < 0.0000001):
                break
            if cost - new_cost > 0:
                path = new_path
                cost = new_cost
            elif exp((cost - new_cost)/temp) > random():
                path = new_path
                cost = new_cost
            print('\x1b[33mCOST: ' + str(cost) + '\x1b[0m\n')

            temp *= 1 - coolingRate

        return path, cost


class NearestInsertion(Graph):

    def find_closest_node(self, node_list, path):

        distance_list = []
        for i, current_node in enumerate(node_list):
            temp_distance = 0
            for j, inside_node in enumerate(path):
                temp_distance += self.calculate_distance(current_node,
                                                                inside_node)
            distance_list.append((current_node, temp_distance))

        node_k, _ = min(distance_list, key=lambda i: i[1])
        return node_k

    def calculate_edge(self, node_k, node_i, node_j):

        distance1 = self.calculate_distance(node_i, node_k)
        distance2 = self.calculate_distance(node_k, node_j)
        distance3 = self.calculate_distance(node_i, node_j)
        distance = distance1 + distance2 - distance3
        return distance

    def find_minimum_edge(self, node_k, path):

        temp_list = []

        for i in range(len(path) - 1):
            node_i = path[i]
            node_j = path[i + 1]
            temp_distance = self.calculate_edge(node_k, node_i, node_j)
            temp_list.append((temp_distance, i))

        _, pos = min(temp_list, key=lambda i: i[0])
        return pos

    def find_shortest_path(self):

        node_list = self.node_list.copy()
        current_node = node_list.pop(0)
        path = [current_node]
        next_node = self.find_closest_node(node_list, path)
        node_list.remove(next_node)
        path.append(next_node)

        while len(path) < len(self.node_list):
            node_k = self.find_closest_node(node_list, path)
            pos = self.find_minimum_edge(node_k, path)
            path.insert(pos + 1, node_k)
            node_list.remove(node_k)
            print(str(round(len(path)/len(self.node_list)*100, 2)) + '%')

        cost = self.calculate_cost(path)

        return path, cost
