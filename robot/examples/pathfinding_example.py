from enum import Enum

from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import heapq
from graphviz import Digraph
import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from stairs_area import StairsInformation
from detected_object import DetectedObject
from bounding_box import get_bounding_boxes_of_object, BoundingBox
from guidance.stairs_map import Movement
from guidance.stairs_map_creator import (
    AdvancedStairsMapCreator,
    StairsMapCreator,
)
from path_object_detection import PathObjectDetection
import img_utils
from guidance.a_star_path_finder import AStarPathFinder
from guidance.a_star_space_optimized_path_finder import AStarSpaceOptimizedPathFinder
from guidance.path_finder import PathFinder
import logging.config
import logging
import image_logging
from pytorch_object_detection import PyTorchObjectDetection


image_logging.configure(fname="../robot.conf")
logging.config.fileConfig(fname="../logger.conf")

triton = PyTorchObjectDetection(r"..\models\yolov5-v4.0", "../../tensorrt/latest_weights/weights.pt")


ROBOT_WIDTH_IN_CM = 40
MOVEMENTS_IN_CM = 5
STEP_LENGTH_IN_CM = 135
STEP_HEIGHT_IN_CM = 20

stairs_information: StairsInformation = StairsInformation(
    step_width_in_cm=STEP_LENGTH_IN_CM,
    step_height_in_cm=STEP_HEIGHT_IN_CM,
)

stairs_map_creator: StairsMapCreator = AdvancedStairsMapCreator(
    robot_width_in_cm=ROBOT_WIDTH_IN_CM,
    movements_in_cm=MOVEMENTS_IN_CM,
    stairs_information=stairs_information,
)

def __cut_boxes_to_steps_size(
        
        steps: BoundingBox,
        boxes: List[BoundingBox],
        remove_outliers: bool = False,
    ) -> List[BoundingBox]:
        """
        Cuts the boxes to an image of the position and size of the steps BoundingBox.
        :param remove_outliers This will drop all boxes intersecting with the steps since this should not happen.
        """

        logging.debug(f"__cut_boxes_to_steps_size remove_outliers: {remove_outliers}")

        if remove_outliers:
            logging.debug("remove_outliers")
            boxes = __filter_boxes_intersecting_steps(steps, boxes)

        return [__cut_box_to_steps_size(steps, box) for box in boxes]

def __cut_box_to_steps_size(
    steps: BoundingBox, box: BoundingBox
) -> BoundingBox:
    """
    Cuts the box to an image of the position and size of the steps BoundingBox.
    """
    return BoundingBox(
        box.detected_object,
        box.confidence,
        max(0, box.x1 - steps.x1),
        steps.width() - max(0, steps.x2 - box.x2),
        max(0, box.y1 - steps.y1),
        steps.height() - max(0, steps.y2 - box.y2),
        steps.width(),
        steps.height(),
    )

def __filter_boxes_intersecting_steps(
    steps: BoundingBox, boxes: List[BoundingBox]
) -> List[BoundingBox]:
    """
    This will remove all the boxes intersecting with the borders of the steps.
    """
    logging.debug("Remove outliers!")
    return [
        box
        for box in boxes
        if (box.x1 >= steps.x1)
        and (box.x2 <= steps.x2)
        and (box.y1 >= steps.y1)
        and (box.y2 <= steps.y2)
    ]

for x in range(1):
    logging.info("Try number {}".format(x))
    for path in range(1, 14):
        logging.info("Next path: {}".format(path))
        # like this I can reproduce the error!
        img = cv2.imread("../tests/camera_images/path/path_{}.jpg".format(path))
        if img is None:
            continue
        result = triton.detect(img, confidence=0.6)
        steps_box = next(
            iter(
                [obj for obj in result if obj.detected_object == DetectedObject.steps]
            ),
            None,
        )

        for b in result:
            logging.debug(b)

        image_logging.log(
            "first_image_path_{}_try_{}.jpg".format(path, x),
            img_utils.render_boxes(img, result),
        )

        cv2.imwrite("first_image_path_{}_try_{}.jpg".format(path, x), img_utils.render_boxes(img, result))

        if steps_box:
            path_object_detection = PathObjectDetection(triton)
            path_object_detection_result = path_object_detection.detect(img)
            steps = path_object_detection_result.get_steps()
            image = path_object_detection_result.image
            steps_image = steps.extract(image)

            # detect bricks on complete image since it works better there
            bricks = __cut_boxes_to_steps_size(
                steps, path_object_detection_result.get_bricks()
            )
            # detect edges on complete image since it works better there
            edges = __cut_boxes_to_steps_size(
                steps,
                path_object_detection_result.get_edges(min_width_normalized=0.2)
            )

            try:
                stairs_map = stairs_map_creator.convert_to_stairs_map(
                    steps_image, bricks, edges
                )

                if stairs_map is None:
                    print(
                        "ERROR impossible to calculate stairs_map, edges detection failed!"
                    )

                else:
                    
                    stairs_map.set_start(0.5)
                    stairs_map.set_goal(0.5)
                    start_cells = [
                        cell for cell in stairs_map.cells if cell.step_number == 0
                    ]
                    start_cell = start_cells[int(len(start_cells) / 2)]
                    end_cells = [cell for cell in stairs_map.cells if cell.step_number == 6]
                    end_cell = end_cells[int(len(end_cells) / 2)]

                    #path_finder: PathFinder = AStarPathFinder()
                    path_finder: PathFinder = AStarSpaceOptimizedPathFinder()
                    movements: List[Movement] = path_finder.find_path(
                        stairs_map, start_cell, end_cell
                    )
            except Exception as e:
                logging.exception("Error")

        else:
            logging.error("No steps detected!!!!!")
