from typing import List
from bounding_box import BoundingBox
from detected_object import DetectedObject
import logging
import numpy as np

from guidance.edge_predictor import EdgePredictor


class MissingEdgeCalculator:
    def __init__(self, number_of_expected_edges: int):
        self.number_of_expected_edges: int = number_of_expected_edges

    def calculate_missing_edges(
        self, existing_edges: List[BoundingBox], bricks: List[BoundingBox]
    ) -> List[BoundingBox]:
        """
        Calculates the missing edges from the existing edges and the bricks on the stairs.
        Return: All the edges including the missing ones.
        """
        pass


class BricksBasedMissingEdgeCalculator(MissingEdgeCalculator):
    """
    Calculates the missing edges depending on the position of the bricks.
    """

    def __init__(self, number_of_expected_edges: int):
        self.number_of_expected_edges: int = number_of_expected_edges

    def calculate_missing_edges(
        self, existing_edges: List[BoundingBox], bricks: List[BoundingBox]
    ) -> List[BoundingBox]:
        """
        Calculates the missing edges from the existing edges and bricks on the stairs.
        Return: All the edges which can be calulated including the missing ones.
        """
        fixed_edges: List[BoundingBox] = existing_edges.copy()

        if len(fixed_edges) == self.number_of_expected_edges:
            logging.info("All edges provided")
            return fixed_edges

        if len(fixed_edges) < 2:
            logging.error("Impossible to calculate missing edges...")
            return fixed_edges

        fixed_edges = self.__calculate_edges_depending_on_bricks(fixed_edges, bricks)

        return fixed_edges

    def __calculate_edges_depending_on_bricks(
        self, edges: List[BoundingBox], bricks: List[BoundingBox]
    ) -> List[BoundingBox]:
        edge_predictor = EdgePredictor(edges)
        combined_edges = [
            edge_predictor.predict_edge(brick.v2 + 0.3 * brick.height_normalized())
            for brick in bricks
        ] + edges
        self.__sort_edges_from_highest_to_lowest(combined_edges)
        return self.__nms(combined_edges)

    def __sort_edges_from_highest_to_lowest(self, edges: List[BoundingBox]):
        edges.sort(reverse=False, key=lambda e: e.center_y())

    def __nms(
        self, boxes: List[BoundingBox], nms_threshold: float = 0.001
    ) -> List[BoundingBox]:
        """
        Non Maximum Suppresion with a very low threshhold is applied, since edges should not intersect at all.
        """
        x_coord = np.array([box.x1 for box in boxes]).astype(int)
        y_coord = np.array([box.y1 for box in boxes]).astype(int)
        width = np.array([box.width() for box in boxes]).astype(int)
        height = np.array([box.height() for box in boxes]).astype(int)

        box_confidences = np.array([box.confidence for box in boxes]).astype(int)

        areas = width * height
        ordered = box_confidences.argsort()[::-1]

        keep = list()
        while ordered.size > 0:
            # Index of the current element:
            i = ordered[0]
            keep.append(i)
            xx1 = np.maximum(x_coord[i], x_coord[ordered[1:]])
            yy1 = np.maximum(y_coord[i], y_coord[ordered[1:]])
            xx2 = np.minimum(x_coord[i] + width[i], x_coord[ordered[1:]] + width[ordered[1:]])
            yy2 = np.minimum(y_coord[i] + height[i], y_coord[ordered[1:]] + height[ordered[1:]])

            width1 = np.maximum(0.0, xx2 - xx1 + 1)
            height1 = np.maximum(0.0, yy2 - yy1 + 1)
            intersection = width1 * height1
            union = (areas[i] + areas[ordered[1:]] - intersection)
            iou = intersection / union
            indexes = np.where(iou <= nms_threshold)[0]
            ordered = ordered[indexes + 1]

        keep = np.array(keep).astype(int)
        return np.array(boxes)[keep].tolist()

class GapBasedMissingEdgeCalculator(MissingEdgeCalculator):
    """
    Calculates the missing edges depending on the gaps between the existing edges.
    """

    def __init__(self, number_of_expected_edges: int):
        self.number_of_expected_edges: int = number_of_expected_edges

    def calculate_missing_edges(
        self, existing_edges: List[BoundingBox], bricks: List[BoundingBox]
    ) -> List[BoundingBox]:
        """
        Calculates the missing edges from the existing edges on the stairs.
        Return: All the edges including the missing ones.
        """
        fixed_edges: List[BoundingBox] = existing_edges.copy()

        if len(fixed_edges) == self.number_of_expected_edges:
            logging.info("All edges provided")
            return fixed_edges

        if len(fixed_edges) < (self.number_of_expected_edges - 4):
            logging.error("Impossible to calculate missing edges...")
            return fixed_edges

        self.edge_predictor = EdgePredictor(fixed_edges)

        image_width = fixed_edges[0].image_width
        image_height = fixed_edges[0].image_height

        # Where does the highest and lowest edge have to be? -> All relative values
        self.border_size_high = 0.1
        self.border_size_low = 0.67

        # check if there is the lowest one
        if fixed_edges[0].center_v_normalized() >= self.border_size_low:
            logging.info("Has lowest edge")

        else:
            logging.info("Has not lowest edge - Added lowest edge")
            fixed_edges.append(
                BoundingBox(
                    DetectedObject.edge,
                    0.0,
                    0,
                    image_width,
                    (self.border_size_low + self.border_size_high * 0.5) * image_height,
                    image_height,
                    image_width,
                    image_height,
                )
            )
        self.__sort_edges_from_lowest_to_highest(fixed_edges)

        # check if there is the highest one
        if (
            fixed_edges[len(fixed_edges) - 1].center_v_normalized()
            <= self.border_size_high
        ):
            logging.info("Has highest edge")

        else:
            logging.info("Has not highest edge - Added highest edge")
            fixed_edges.append(
                self.edge_predictor.predict_edge(self.border_size_high / 4)
            )
            self.__sort_edges_from_lowest_to_highest(fixed_edges)

        # check how many else are missing in the center
        number_of_missing_edges = self.number_of_expected_edges - len(fixed_edges)

        if number_of_missing_edges > 0:
            logging.info(
                "There are still {0} edges missing".format(number_of_missing_edges)
            )
            missing_edges: List[BoundingBox] = self.calculate_missing_central_edges(
                number_of_missing_edges, fixed_edges
            )
            fixed_edges += missing_edges
            self.__sort_edges_from_lowest_to_highest(fixed_edges)

        return fixed_edges

    def calculate_missing_central_edges(
        self, number_of_missing_edges: int, found_edges: List[BoundingBox]
    ) -> List[BoundingBox]:
        missing_edges: List[BoundingBox] = []

        # initialize it with 0.25 -> check if this makes sense
        # TODO: calculate this better -> We don't know, that the second edge is missing... or not
        last_gap = 1 - self.border_size_low

        # fix the ones in the center
        # we can determine that an edge is missing if the distance between the center_v is increasing from down to top

        last_y = found_edges[0].center_v_normalized()

        for i in range(1, len(found_edges)):
            last_width = found_edges[i - 1].width()
            current_width = found_edges[i].width()
            width_ratio = current_width / float(last_width)

            last_y = found_edges[i - 1].center_v_normalized()
            current_y = found_edges[i].center_v_normalized()
            current_gap = last_y - current_y

            logging.info(
                "last_y {0}, current_y {1} at index {2}".format(last_y, current_y, i)
            )

            logging.info(
                "calculated distance between {0} and {1} is {2}".format(
                    i - 1, i, current_gap
                )
            )
            if (current_gap) > last_gap:
                # BUG: Calculate this better -> Terrible formula...
                logging.info(
                    f"current_gap {current_gap}, last_gap {last_gap} current_width {current_width} last_width {last_width}"
                )
                number_of_missing_edges_in_gap = max(min(
                    int(round(current_gap / (last_gap * width_ratio)) - 1),
                    number_of_missing_edges,
                ), 1)
                logging.info(
                    "found {0} missing edge(s) at index {1}".format(
                        number_of_missing_edges_in_gap, i
                    )
                )
                last_gap = current_gap / (number_of_missing_edges_in_gap + 1)
                logging.info("distance in between {0}".format(last_gap))

                for q in range(number_of_missing_edges_in_gap):
                    y_calculated = current_y + (q + 1) * last_gap
                    logging.info("y_calculated {0}".format(y_calculated))
                    missing_edges.append(self.edge_predictor.predict_edge(y_calculated))

            else:
                last_gap = current_gap

        return missing_edges

    def __sort_edges_from_lowest_to_highest(self, edges: List[BoundingBox]):
        edges.sort(reverse=True, key=lambda e: e.center_y())
