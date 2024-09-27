import xml.etree.ElementTree as ET
import pytmx,pygame
from collections import deque
from PQ import PQ

class Map:
    def __init__(self, starting_position, tasks, end_position, map_file, tmx_data):
        self.starting_position = starting_position
        self.tasks = tasks
        self.end_position = end_position
        self.tmx_data = tmx_data
        self.map = self.read_map(map_file)
        self.graph = {}


    def load_tmx(self,filename):
        """Load TMX file."""
        pygame.init()
        pygame.display.set_mode((800, 600))
        tmx_data = pytmx.load_pygame(filename)
        return tmx_data  

    def read_map(self, map_file):
        tmx_data = self.tmx_data
        passable_tiles = [0,1]
        matrix = [[0] * tmx_data.width for _ in range(tmx_data.height)]
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid not in passable_tiles:
                        matrix[y][x] = 1
        return matrix
    
    def create_graph(self):
        self.print_matrix(self.map)
        nodes = [self.starting_position, self.end_position]
        for task in self.tasks:
            nodes.append(task.location)
        for node1 in nodes:
            for node2 in nodes:
                if node1 != node2:
                    path,distance = self.bfs_distance(node1, node2)
                    self.graph[tuple(node1),tuple(node2)] = [path, distance - 1]
                else:
                    self.graph[tuple(node1),tuple(node2)] = [[], 0]


    def bfs_distance(self, node1, node2):
        matrix = self.map
        if node1 == node2:
            return [node1]

        visited = set()
        queue = PQ()
        queue.push((node1,[node1]),abs(node1[0]- node2[0]) + abs(node1[1]- node2[1]))

        while not queue.is_empty():
            current, path = queue.pop()
            visited.add(tuple(current))
            if current == node2:
                return path, len(path)

            neighbors = self.get_neighbors(matrix, tuple(current))
            for neighbor in neighbors:
                if neighbor not in visited:
                    new_path = path + [[neighbor[0],neighbor[1]]]
                    queue.push(([neighbor[0],neighbor[1]], new_path), abs(neighbor[0]- node2[0]) + abs(neighbor[1]- node2[1]))
                    visited.add(tuple(neighbor))
        raise Exception("NO PATH FOUND BETWEEN " +str(node1)+" AND "+str(node2))
    

    def get_neighbors(self, matrix, node):
        x, y = node
        neighbors = []

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            new_x, new_y = x + dx, y + dy

            if 0 <= new_x < len(matrix[0]) and 0 <= new_y < len(matrix):
                if matrix[new_x][new_y] == 0:
                    neighbors.append((new_x, new_y))
        return neighbors

    
    def print_matrix(self,matrix):
        for row in matrix:
            for elem in row:
                print(elem, end="\t")  # Use "\t" for tab separation
            print()  # Move to the next line after printing each row







    
