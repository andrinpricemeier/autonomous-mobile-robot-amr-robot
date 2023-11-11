from sklearn.linear_model import LinearRegression
import numpy as np
from typing import List
from bounding_box import BoundingBox
import logging
from detected_object import DetectedObject


class EdgePredictor:
    """
    Predicts the width and the x positions of an edge depending on the normalized y position and the existing edges.
    """

    def __init__(self, existing_edges: List[BoundingBox]):
        self.existing_edges = existing_edges
        self.x1_predictor = self.__fit_x1_predictor()
        self.width_predictor = self.__fit_width_predictor()
        self.image_width = self.existing_edges[0].image_width
        self.image_height = self.existing_edges[0].image_height

    def predict_edge(self, y_normalized_predicting_edge: float) -> BoundingBox:
        box_height = 0.05 * self.image_height * (1 + y_normalized_predicting_edge)
        box_width = self.__predict_width(y_normalized_predicting_edge)

        # TODO: Move calculations to different function

        logging.debug(
            "y_normalized_predicting_edge {0}, predicted box_width {1}".format(
                y_normalized_predicting_edge, box_width
            )
        )

        x1 = self.__predict_x1(y_normalized_predicting_edge)
        logging.debug(
            "y_normalized_predicting_edge {0}, predicted x1 {1}".format(
                y_normalized_predicting_edge, x1
            )
        )

        x2 = x1 + box_width
        logging.debug(
            "y_normalized_predicting_edge {0}, calculated x2 {1}".format(
                y_normalized_predicting_edge, x2
            )
        )

        abs_y_center = y_normalized_predicting_edge * self.image_height
        logging.debug(
            "y_normalized_predicting_edge {0}, calculated abs_y_center {1}".format(
                y_normalized_predicting_edge, abs_y_center
            )
        )

        logging.debug(
            "y_normalized_predicting_edge {0}, calculated box_height {1}".format(
                y_normalized_predicting_edge, box_height
            )
        )

        y1 = y_normalized_predicting_edge * self.image_height - 0.5 * box_height
        logging.debug(
            "y_of_predicting_edge {0}, calculated y1 {1}".format(
                y_normalized_predicting_edge, y1
            )
        )

        y2 = y_normalized_predicting_edge * self.image_height + 0.5 * box_height
        logging.debug(
            "y_of_predicting_edge {0}, calculated y2 {1}".format(
                y_normalized_predicting_edge, y2
            )
        )

        return BoundingBox(
            DetectedObject.edge,
            0.0,
            x1,
            x2,
            y1,
            y2,
            self.image_width,
            self.image_height,
        )

    def __fit_x1_predictor(self) -> LinearRegression:
        X = np.zeros([len(self.existing_edges), 1])
        y = np.zeros(len(self.existing_edges))

        for i in range(len(self.existing_edges)):
            X[i, 0] = self.existing_edges[i].center_v_normalized()
            y[i] = self.existing_edges[i].x1

        return LinearRegression().fit(X, y)

    def __predict_x1(self, y_of_predicting_edge: float):
        """
        Returns the prediction of x1 of an edge at this normalized y position.
        """
        return self.x1_predictor.predict(
            np.array([y_of_predicting_edge]).reshape(1, -1)
        )[0]

    def __fit_width_predictor(self):
        X = np.zeros([len(self.existing_edges), 1])
        y = np.zeros(len(self.existing_edges))

        for i in range(len(self.existing_edges)):
            X[i, 0] = self.existing_edges[i].center_v_normalized()
            y[i] = self.existing_edges[i].width()

        return LinearRegression().fit(X, y)

    def __predict_width(self, y_normalized_predicting_edge: float):
        """
        Returns the prediction of the absolute width of an edge at this normalized y position.
        """
        return self.width_predictor.predict(
            np.array([y_normalized_predicting_edge]).reshape(1, -1)
        )[0]
