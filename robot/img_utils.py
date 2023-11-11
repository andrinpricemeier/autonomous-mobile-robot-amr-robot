from path import Path
from typing import Any, List, Tuple
from bounding_box import BoundingBox
import imgaug.augmenters as iaa
import cv2
from line import Line
import numpy as np
from movement import Movement
from guidance.stairs_map import StairsMap, Cell

rendering_enabled: bool = True


def set_rendering_enabled(enabled: bool):
    global rendering_enabled
    rendering_enabled = enabled


def resize(img: Any, new_width: float, new_height: float) -> Any:
    seq = iaa.Sequential(
        [
            iaa.CenterPadToSquare(),
            iaa.Resize({"height": new_height, "width": new_width}),
        ]
    )
    return seq(image=img)

def pad_to_square(img: Any) -> Any:
    seq = iaa.Sequential(
        [
            iaa.CenterPadToSquare()
        ]
    )
    return seq(image=img)


def cut(img: Any, bounding_box: BoundingBox) -> Any:
    """Return the image cutted to the edges of the bounding_box."""
    return img.copy()[
        bounding_box.y1 : bounding_box.y2, bounding_box.x1 : bounding_box.x2
    ]


def render_boxes(
    img: Any, boxes: List[BoundingBox], color: Tuple[int, int, int] = (0, 0, 255)
) -> Any:
    if not rendering_enabled:
        return np.zeros((1, 1))
    annotated = img.copy()
    for box in boxes:
        annotated = render_box(
            annotated, (box.x1, box.y1, box.x2, box.y2), box.confidence
        )
    return annotated


def render_lines(
    img: Any, lines: List[Line], color: Tuple[int, int, int] = (0, 0, 255)
) -> Any:
    if not rendering_enabled:
        return np.zeros((1, 1))
    annotated = img.copy()
    for line in lines:
        annotated = render_line(annotated, (line.x1, line.y1, line.x2, line.y2))
    return annotated


def render_text(
    img: Any, text: str, x: int, y: int, color: Tuple[int, int, int] = (0, 0, 255)
) -> Any:
    if not rendering_enabled:
        return np.zeros((1, 1))
    annotated = img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    annotated = cv2.putText(annotated, text, (x, y), font, 1, color, 1, cv2.LINE_AA)
    return annotated


def render_box(
    img: Any,
    box: Tuple[float, float, float, float],
    confidence: float,
    color: Tuple[int, int, int] = (0, 0, 255),
) -> Any:
    """
    Render a box. Calculates scaling and thickness automatically.
    :param img: image to render into
    :param box: (x1, y1, x2, y2) - box coordinates
    :param color: (b, g, r) - box color
    :return: updated image
    """
    if not rendering_enabled:
        return np.zeros((1, 1))
    x1, y1, x2, y2 = box
    thickness = int(round((img.shape[0] * img.shape[1]) / (750 * 750)))
    thickness = max(1, thickness)
    img = render_text(img, str(round(confidence, 2)), int(x1), int(y1), (0, 255, 0))
    img = cv2.rectangle(
        img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness=thickness
    )
    return img


def render_line(
    img: Any,
    line: Tuple[float, float, float, float],
    color: Tuple[int, int, int] = (0, 0, 255),
) -> Any:
    """
    Render a line. Calculates scaling and thickness automatically.
    :param img: image to render into
    :param box: (x1, y1, x2, y2) - line coordinates
    :param color: (b, g, r) - line color
    :return: updated image
    """
    if not rendering_enabled:
        return np.zeros((1, 1))
    x1, y1, x2, y2 = line
    thickness = int(round((img.shape[0] * img.shape[1]) / (750 * 750)))
    thickness = max(1, thickness)

    img = cv2.line(
        img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness=thickness
    )
    return img


def render_map(map: StairsMap) -> Any:
    """
    Render a map.
    :param map The map to render.
    """
    if not rendering_enabled:
        return np.zeros((1, 1))
    scale = 10
    image = __draw_empty_map(map, scale)
    image = __draw_map(map, image, scale)

    if map.position is not None:
        image = __draw_position(map, image, scale)

    return image


def render_map_with_path(map: StairsMap, path: Path) -> Any:
    """
    Render a map with a path.
    :param map The map to render.
    :param map The map to render.
    """
    if not rendering_enabled:
        return np.zeros((1, 1))
    scale = 10
    image = __draw_empty_map(map, scale)
    image = __draw_path(map, image, path, scale)
    image = __draw_map(map, image, scale)

    if map.position is not None:
        image = __draw_position(map, image, scale)

    return image

def rotate_center_counter_clockwise(image: Any, angle: int) -> Any:
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)

def __draw_cell(
    map: StairsMap, image: Any, cell: Cell, color: Any, thickness: float, scale: float
) -> Any:
    y = map.height - cell.step_number

    return cv2.rectangle(
        image,
        (int(cell.cell_number + 1) * scale, int(y) * scale),
        (int(cell.cell_number) * scale, int(y - 1) * scale),
        color,
        thickness=thickness,
    )


def __draw_map(map: StairsMap, image: Any, scale: float) -> Any:
    for c in map.cells:
        color = (0, 0, 0)
        thickness = 1
        if c.is_obstacle:
            color = (0, 0, 255)
            thickness = -1
        elif c.is_start or c.is_end:
            color = (0, 0, 0)
            thickness = -1

        image = __draw_cell(map, image, c, color, thickness, scale)
    return image


def __draw_empty_map(map: StairsMap, scale: float) -> Any:

    image = np.zeros((map.height * scale, map.width * scale, 3), dtype=np.uint8)
    image.fill(255)
    return image


def __draw_position(map: StairsMap, image: Any, scale: float) -> Any:
    return __draw_cell(map, image, map.position, (255, 0, 0), -1, scale)


def __draw_path(map: StairsMap, image: Any, path: Path, scale: float) -> Any:
    cur_drawing_position: Cell = map.start
    image = __draw_cell(map, image, cur_drawing_position, (0, 255, 0), -1, scale)
    for movement in path.movements:
        if movement == Movement.left:
            cur_drawing_position = map.get_position(
                cur_drawing_position.cell_number - 1, cur_drawing_position.step_number
            )

        elif movement == Movement.right:
            cur_drawing_position = map.get_position(
                cur_drawing_position.cell_number + 1, cur_drawing_position.step_number
            )

        elif movement == Movement.climb:
            cur_drawing_position = map.get_position(
                cur_drawing_position.cell_number, cur_drawing_position.step_number + 1
            )

        image = __draw_cell(map, image, cur_drawing_position, (0, 255, 0), -1, scale)
    return image
