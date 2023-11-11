import image_logging
from typing import Dict, List, Optional, Any
from graphviz import Digraph
import heapq
import logging
import img_utils
import os
import sys
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from guidance.path_finder import PathFinder
from guidance.stairs_map import StairsMap, Cell
from movement import Movement
from path import Path


class Node:
    def __init__(self, cell: Cell) -> None:
        self.cell = cell

    def __lt__(self, other: Any) -> bool:
        if self.cell.step_number < other.cell.step_number:
            return True
        elif self.cell.step_number == other.cell.step_number:
            return self.cell.cell_number < other.cell.cell_number
        else:
            return False


class DirectedEdge:
    def __init__(self, start: Node, end: Node, movement: Movement) -> None:
        self.start = start
        self.end = end
        self.movement = movement


class PriorityQueue:
    def __init__(self) -> None:
        self.elements = []

    def empty(self) -> bool:
        return not self.elements

    def put(self, item: Any, priority: float) -> None:
        heapq.heappush(self.elements, (priority, item))

    def get(self) -> Any:
        return heapq.heappop(self.elements)[1]


class AStarPathFinderObstacleAvoider(PathFinder):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: List[Node] = []
        self.edges: List[DirectedEdge] = []

    def find_path(self, stairs_map: StairsMap, start: Cell, goal: Cell) -> Path:
        self.nodes: List[Node] = []
        self.edges: List[DirectedEdge] = []
        # TODO: actually care about the end cell...
        self.start = start
        self.stairs_map = stairs_map
        self.goal = goal

        self.start.is_start = True
        self.goal.is_end = True

        self.create_graph(start)

        start_node = next(iter([n for n in self.nodes if n.cell.is_start]), None)
        end_node = next(iter([n for n in self.nodes if n.cell.is_end]), None)

        # No Path found -> end_node is not a part of the graph
        if end_node is None:
            logging.info("AStarPathFinderObstacleAvoider no path found")
            return None

        came_from, cost_so_far = self.a_star_search(start_node, end_node)

        self.path_nodes = []
        self.path_edges = []
        cur = end_node

        self.path_nodes.append(cur)

        while cur != start_node:
            prev = came_from[cur]
            e = next(
                iter([e for e in self.edges if e.start == prev and e.end == cur]), None
            )
            self.path_edges.append(e)
            self.path_nodes.append(prev)
            cur = prev

        movements = self.calculate_movements()
        path: Path = Path(movements, stairs_map.cell_width_in_cm)
        image_logging.log(
            "stairs_map_with_obstacles.jpg",
            img_utils.render_map_with_path(stairs_map, path),
        )

        return path

    def a_star_search(self, start: Node, goal: Node) -> Any:
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from: Dict[Node, Optional[Node]] = {}
        cost_so_far: Dict[Node, float] = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current: Node = frontier.get()

            if current == goal:
                break

            for next in self.neighbours(current):
                new_cost = cost_so_far[current] + self.cost(current, next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(next, goal)
                    frontier.put(next, priority)
                    came_from[next] = current
        return came_from, cost_so_far

    def heuristic(self, a: Node, b: Node) -> float:
        return b.cell.step_number - a.cell.step_number

    def neighbours(self, current: Node) -> List[Node]:
        neighbour_nodes = []
        for e in self.edges:
            if e.start == current:
                neighbour_nodes.append(e.end)
        return neighbour_nodes

    def cost(self, a: Node, b: Node) -> float:
        if b.cell.is_end:
            return b.cell.step_number - a.cell.step_number
        else:
            cell_dist = abs(a.cell.cell_number - b.cell.cell_number)
            step_dist = abs(a.cell.step_number - b.cell.step_number)
            if step_dist > 0:
                step_dist += (self.stairs_map.width//2 - self.stairs_map.get_minimal_sideways_obstacle_distance(b.cell.cell_number, b.cell.step_number))**2
            return cell_dist + step_dist

    def create_graph(self, current: Cell) -> Any:
        left = next(
            iter(
                [
                    c
                    for c in self.stairs_map.cells
                    if c.step_number == current.step_number
                    and c.cell_number == current.cell_number - 1
                    and not c.is_obstacle
                ]
            ),
            None,
        )
        right = next(
            iter(
                [
                    c
                    for c in self.stairs_map.cells
                    if c.step_number == current.step_number
                    and c.cell_number == current.cell_number + 1
                    and not c.is_obstacle
                ]
            ),
            None,
        )
        up = next(
            iter(
                [
                    c
                    for c in self.stairs_map.cells
                    if c.step_number == current.step_number + 1
                    and c.cell_number == current.cell_number
                    and not c.is_obstacle
                ]
            ),
            None,
        )
        current_node = next(iter([n for n in self.nodes if n.cell == current]), None)
        if current_node is None:
            current_node = Node(current)
            self.nodes.append(current_node)
        if left is not None:
            existing_edge = next(
                iter(
                    [
                        e
                        for e in self.edges
                        if e.start.cell == current and e.end.cell == left
                    ]
                ),
                None,
            )
            if existing_edge is None:
                left_node = next(iter([n for n in self.nodes if n.cell == left]), None)
                if left_node is None:
                    left_node = Node(left)
                    self.nodes.append(left_node)
                left_edge = DirectedEdge(current_node, left_node, Movement.left)
                self.edges.append(left_edge)
                self.create_graph(left)
        if right is not None:
            existing_edge = next(
                iter(
                    [
                        e
                        for e in self.edges
                        if e.start.cell == current and e.end.cell == right
                    ]
                ),
                None,
            )
            if existing_edge is None:
                right_node = next(
                    iter([n for n in self.nodes if n.cell == right]), None
                )
                if right_node is None:
                    right_node = Node(right)
                    self.nodes.append(right_node)
                right_edge = DirectedEdge(current_node, right_node, Movement.right)
                self.edges.append(right_edge)
                self.create_graph(right)
        if up is not None:
            existing_edge = next(
                iter(
                    [
                        e
                        for e in self.edges
                        if e.start.cell == current and e.end.cell == up
                    ]
                ),
                None,
            )
            if existing_edge is None:
                up_node = next(iter([n for n in self.nodes if n.cell == up]), None)
                if up_node is None:
                    up_node = Node(up)
                    self.nodes.append(up_node)
                up_edge = DirectedEdge(current_node, up_node, Movement.climb)
                self.edges.append(up_edge)
                self.create_graph(up)

    def calculate_movements(self) -> List[Movement]:
        start_edge = next(
            iter([e for e in self.path_edges if e.start.cell == self.start]), None
        )
        current_edge = start_edge
        movements: List[Movement] = []
        while current_edge is not None:
            movements.append(current_edge.movement)
            current_edge = next(
                iter(
                    [
                        e
                        for e in self.path_edges
                        if e.start.cell == current_edge.end.cell
                    ]
                ),
                None,
            )

        return movements

    def draw_graph(
        self,
        nodes_to_draw: List[Node],
        edges_to_draw: List[DirectedEdge],
        img_path: str,
    ) -> None:
        dot = Digraph(comment="Labyrinth", engine="neato", format="jpg")
        for n in nodes_to_draw:
            dot.node(
                f"{n.cell.step_number}-{n.cell.cell_number}",
                f"{n.cell.step_number}-{n.cell.cell_number}",
            )
        for e in edges_to_draw:
            dot.edge(
                f"{e.start.cell.step_number}-{e.start.cell.cell_number}",
                f"{e.end.cell.step_number}-{e.end.cell.cell_number}",
                constraint="false",
            )
        dot.render(img_path)
