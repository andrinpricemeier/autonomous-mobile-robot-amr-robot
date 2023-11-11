from enum import Enum
from movement import Movement
from path import Path
from typing import List

import cv2
import numpy as np
import image_logging
import logging
import math


class Cell:
    def __init__(self, step_number, cell_number):
        self.step_number = step_number
        self.cell_number = cell_number
        self.is_obstacle = False
        self.is_start = False
        self.is_end = False

    def __eq__(self, o: object) -> bool:
        return (
            self.cell_number == o.cell_number
            and self.step_number == o.step_number
            and self.is_obstacle == o.is_obstacle
        )

    def __repr__(self) -> str:
        return f"Cell: step_number : {self.step_number}, cell_number : {self.cell_number}, is_obstacle : {self.is_obstacle}, is_start : {self.is_start}, is_end : {self.is_end}"


class StairsMap:
    def __init__(self, width: int, height: int, cell_width_in_cm, robot_width_in_cm: int) -> None:
        self.width: int = width
        self.height: int = height
        self.cells: List[Cell] = []
        self.cell_width_in_cm: int = cell_width_in_cm
        self.position: Cell = None
        self.start: Cell = None
        self.goal: Cell = None
        self.robot_width_in_cm: int = robot_width_in_cm

    def initialize(self) -> None:
        for step_number in reversed(range(self.height)):
            for cell_number in range(self.width):
                self.cells.append(Cell(step_number, cell_number))

        self.__set_obstacles_on_side()

    def clear_obstacles(self) -> None:
        for cell in self.cells:
            cell.is_obstacle = False
        
        self.__set_obstacles_on_side()

    def set_start(self, normalized_x_position: float):
        """
        Sets the start in the start area depending on the normalized_x_position.
        """
        logging.info(
            f"set_start calculated normalized_x_position : {normalized_x_position}"
        )
        start_cells = [cell for cell in self.cells if cell.step_number == 0]
        logging.info(
            f"set_start calculated cell : {int(self.width * normalized_x_position)}, amount of cells: {len(start_cells)}"
        )
        self.start = start_cells[int(self.width * normalized_x_position)]
        self.start.is_start = True
        self.position = self.start

    def set_start_cell(self, start_cell: Cell):
        """
        Sets the start to the provided cell.
        """
        logging.info(f"set_start to cell : {start_cell}")
        if self.start is not None:
            self.start.is_start = False
            logging.info(f"remove old start_cell : {self.start}")

        self.start = start_cell
        self.start.is_start = True

    def __get_goal_cells(self) -> List[Cell]:
        return [
            cell for cell in self.cells if cell.step_number == (self.height - 1)
        ]

    def set_goal(self, normalized_x_position: float):
        """
        Sets the goal in the target area depending on the normalized_x_position.
        """
        logging.info(
            f"set_goal calculated normalized_x_position : {normalized_x_position}"
        )

        goal_cells = self.__get_goal_cells()
        logging.info(
            f"set_goal calculated cell : {int(self.width * normalized_x_position)}, amount of cells: {len(goal_cells)}"
        )
        self.goal = goal_cells[int(self.width * normalized_x_position)]
        self.goal.is_end = True

    def set_obstacle_left(self):
        """
        Sets the cell left to the current position to an obstacle.
        Raises Exception if this position is outside the map.
        """
        return self.set_obstacle(
            self.position.cell_number - 1, self.position.step_number
        )

    def set_obstacle_left_in_distance(self, distance_in_cm: int):
        """
        Sets the cell distance_in_cm left to the robot to an obstacle.
        Raises Exception if this position is outside the map.
        """
        return self.set_obstacle(
            self.position.cell_number - max(math.ceil(self.__cm_to_cells(distance_in_cm)), 1), self.position.step_number
        )

    def set_obstacle_right(self):
        """
        Sets the cell right to the current position to an obstacle.
        Raises Exception if this new position is outside the map.
        """
        return self.set_obstacle(
            self.position.cell_number + 1, self.position.step_number
        )

    
    def set_obstacle_right_in_distance(self, distance_in_cm: int):
        """
        Sets the cell distance_in_cm right to the robot to an obstacle.
        Raises Exception if this position is outside the map.
        """
        return self.set_obstacle(
            self.position.cell_number + max(math.ceil(self.__cm_to_cells(distance_in_cm)),1), self.position.step_number
        )

    def set_obstacle_front(self):
        """
        Sets the cell in fron to the current position to an obstacle.
        Raises Exception if this new position is outside the map.
        """
        return self.set_obstacle(
            self.position.cell_number, self.position.step_number + 1
        )

    def move_position_left(self):
        """
        Moves position in the map one cell to the left.
        Raises Exception if this new position is outside the map.
        """
        # TODO: Return False or change cell if we are on an obstacle!
        self.position = self.get_position(
            self.position.cell_number - 1, self.position.step_number
        )

    def move_position_left_in_distance(self, distance_in_cm: int):
        """
        Moves position in the map distance_in_cm to the left.
        Raises Exception if this new position is outside the map.
        """
        # TODO: Return False or change cell if we are on an obstacle!
        self.position = self.get_position(
            self.position.cell_number - int(self.__cm_to_cells(distance_in_cm)), self.position.step_number
        )

    def move_position_right(self):
        """
        Moves position in the map one cell to the right.
        Raises Exception if this new position is outside the map.
        """
        # TODO: Return False or change cell if we are on an obstacle!
        self.position = self.get_position(
            self.position.cell_number + 1, self.position.step_number
        )

    def move_position_right_in_distance(self, distance_in_cm: int):
        """
        Moves position in the map distance_in_cm to the right.
        Raises Exception if this new position is outside the map.
        """
        # TODO: Return False or change cell if we are on an obstacle!
        self.position = self.get_position(
            self.position.cell_number + int(self.__cm_to_cells(distance_in_cm)), self.position.step_number
        )

    def is_in_target_area(self):
        return self.position is not None and self.position in self.__get_goal_cells()

    def is_in_start_area(self):
        return self.position is not None and self.position.step_number == 0

    def move_position_up(self):
        """
        Moves position in the map one cell up.
        Raises Exception if this new position is outside the map.
        """
        # TODO: Return False or change cell if we are on an obstacle!
        self.position = self.get_position(
            self.position.cell_number, self.position.step_number + 1
        )

    def get_position(self, cell_number: int, step_number: int) -> Cell:
        """
        Gets the position in the map from the passed coordinates.
        Raises Exception if this new position is outside the map.
        """
        new_position = self.__get_cell(cell_number, step_number)
        if new_position is None:
            logging.error(
                f"Impossible get this position, not available, cell_number: {cell_number}, step_number: {step_number}"
            )
            raise Exception(
                f"Impossible to move to this position, not available, cell_number: {cell_number}, step_number: {step_number}"
            )

        return new_position

    def set_obstacle(self, cell_number: int, step_number: int) -> Cell:
        """
        Sets the cell with the coordinates to an obstacle.
        Raises Exception if this new position is outside the map.
        """
        cell: Cell = self.get_position(cell_number, step_number)
        cell.is_obstacle = True

    def get_minimal_sideways_obstacle_distance(self, cell_number: int, step_number: int) -> int:
        distance_to_obstacle_left: int = 0
        distance_to_obstacle_right: int = 0

        for right_cell_number in range(cell_number, self.width):
            distance_to_obstacle_right += 1
            if self.get_position(right_cell_number, step_number).is_obstacle == True:
                break

        for left_cell_number in reversed(range(0, cell_number)):
            distance_to_obstacle_left += 1
            if self.get_position(left_cell_number, step_number).is_obstacle == True:
                break

        return min(distance_to_obstacle_left, distance_to_obstacle_right)    

    def __get_cell(self, cell_number: int, step_number: int) -> Cell:
        possible_cells = [
            cell
            for cell in self.cells
            if cell.cell_number == cell_number and cell.step_number == step_number
        ]
        return possible_cells[0] if len(possible_cells) > 0 else None

    def __cm_to_cells(self, distance_in_cm) -> int:
        """
        Converts a distance in cm to an amount of cells.
        """
        return distance_in_cm / float(self.cell_width_in_cm)

    def __set_obstacles_on_side(self) -> None:
        """
        Sets a half a robot as an obstacle on each side.
        """
        cell_distance_to_side = math.ceil(self.__cm_to_cells(self.robot_width_in_cm  * 0.5))
        for cell in self.cells:
            if (cell.cell_number < cell_distance_to_side) or (cell.cell_number >= (self.width - cell_distance_to_side)):
                self.set_obstacle(cell.cell_number, cell.step_number)

    def __eq__(self, o: object) -> bool:
        return self.cells == o.cells
