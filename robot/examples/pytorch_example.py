import cv2
import os,sys,inspect
from PIL import Image
from imgaug.augmenters.meta import Sequential
import numpy as np
from typing import List
import xml.etree.ElementTree as ET
import imgaug.augmenters as iaa
import imageio
from imgaug.augmentables.bbs import BoundingBox, BoundingBoxesOnImage
import glob
import os
import ntpath
import math
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from pytorch_object_detection import PyTorchObjectDetection
from detected_object import DetectedObject

class VOCBoundingBox:
    """Represents a bounding box in a Pascal VOC file."""

    def __init__(self, name, xmin, ymin, xmax, ymax) -> None:
        self.name = name
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax


class VOCAnnotation:
    """Represents an annotation in a Pascal VOC file."""
    def __init__(self, filename, width, height):
        self.filename = filename
        self.width = width
        self.height = height
        self.bounding_boxes: List[VOCBoundingBox] = []

    def add_bounding_box(self, bb: VOCBoundingBox) -> None:
        self.bounding_boxes.append(bb)

class VOCFile:
    """Represents a Pascal VOC file."""

    def __init__(self, filepath) -> None:
        self.filepath = filepath

    def load(self) -> VOCAnnotation:
        tree = self.__load_file()
        root = tree.getroot()
        annotation = VOCAnnotation(root.find('filename').text, int(root.find('size')[0].text), int(root.find('size')[1].text))
        for member in tree.getroot().findall("object"):
            bb = VOCBoundingBox(
                member[0].text,
                float(member[4][0].text),
                float(member[4][1].text),
                float(member[4][2].text),
                float(member[4][3].text),
            )
            annotation.add_bounding_box(bb)
        return annotation

    def save(self, annotation: VOCAnnotation, save_filepath: str) -> None:
        root = ET.Element("annotation")
        ET.SubElement(root, "folder").text = "my-project-name"
        ET.SubElement(root, "filename").text = annotation.filename
        ET.SubElement(root, "path").text = "my-project-name/" + annotation.filename
        source = ET.SubElement(root, "source")
        ET.SubElement(source, "database").text = "Unspecified"
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(annotation.width)
        ET.SubElement(size, "height").text = str(annotation.height)
        ET.SubElement(size, "depth").text = "3"
        for bb in annotation.bounding_boxes:
            obj = self.__create_object(bb)
            root.append(obj)
        if save_filepath is None:
            save_filepath = self.filepath
        self.filepath = save_filepath
        tree = ET.ElementTree(root)
        tree.write(save_filepath, encoding="UTF-8")

    def __load_file(self) -> ET.ElementTree:
        return ET.parse(self.filepath)

    def __create_object(self, bb: VOCBoundingBox) -> ET.Element:
        obj = ET.Element("object")
        ET.SubElement(obj, "name").text = bb.name
        ET.SubElement(obj, "pose").text = "Unspecified"
        ET.SubElement(obj, "truncated").text = "Unspecified"
        ET.SubElement(obj, "difficult").text = "Unspecified"
        bndbox = ET.SubElement(obj, "bndbox")
        ET.SubElement(bndbox, "xmin").text = str(bb.xmin)
        ET.SubElement(bndbox, "ymin").text = str(bb.ymin)
        ET.SubElement(bndbox, "xmax").text = str(bb.xmax)
        ET.SubElement(bndbox, "ymax").text = str(bb.ymax)
        return obj


def get_steps(image):
    od = PyTorchObjectDetection(r"..\models\yolov5-v4.0", "../../tensorrt/latest_weights/weights.pt")
    img = cv2.imread(image)
    result = od.detect(img, confidence=0.6)
    for r in result:
        if r.detected_object == DetectedObject.steps:
            return r
    return None

dataset_dir = r"C:\Projects\pren\jetson-training\data\annotated_jetson"
output_dir = dataset_dir
image_suffix = "jetson-steps-june-"
all_data = glob.glob(os.path.join(dataset_dir, "*.jpg"))
counter = 0
for datum in all_data:
    steps = get_steps(datum)
    if steps is None:
        continue
    filename_no_ext = os.path.splitext(ntpath.basename(datum))[0]
    bb_filepath = os.path.join(dataset_dir, filename_no_ext + ".xml")
    image = Image.open(datum)    
    if steps.y1 < 0 or (image.width - steps.x2) < 0 or steps.x1 < 0 or (image.height - steps.y2) < 0:
        continue
    arr = np.array(image)
    vocfile = VOCFile(bb_filepath)
    annotation = vocfile.load()
    bbs = []
    for vocbb in annotation.bounding_boxes:
        bbs.append(
            BoundingBox(x1=vocbb.xmin, y1=vocbb.ymin, x2=vocbb.xmax, y2=vocbb.ymax)
        )
    bbimage = BoundingBoxesOnImage(bbs, shape=(image.height, image.width))
    seq = iaa.Sequential(iaa.Crop(px=(int(steps.y1), int(image.width - steps.x2), int(image.height - steps.y2), int(steps.x1))))
    img_aug, bbs_aug = seq(image=arr, bounding_boxes=bbimage)
    output_image_filename = image_suffix + str(counter) + ".jpg"
    output_image_filepath = os.path.join(output_dir, output_image_filename)
    output_bb_filename = image_suffix + str(counter) + ".xml"
    output_bb_filepath = os.path.join(output_dir, output_bb_filename)
    imageio.imwrite(output_image_filepath, img_aug)
    bbs = []
    i = 0
    for bb_aug in bbs_aug:        
        if bb_aug.x1 > 0 and bb_aug.y1 > 0 and bb_aug.x2 > 0 and bb_aug.y2 > 0:
            bbs.append(
                    VOCBoundingBox(
                        annotation.bounding_boxes[i].name,
                        math.floor(bb_aug.x1),
                        math.floor(bb_aug.y1),
                        math.floor(bb_aug.x2),
                        math.floor(bb_aug.y2),
                    )
            )
        i = i + 1
    annotation.bounding_boxes = []
    for bb in bbs:
        annotation.add_bounding_box(bb)
    annotation.width = steps.width()
    annotation.height = steps.height()
    annotation.filename = output_image_filename
    vocfile.save(annotation, output_bb_filepath)
    counter = counter + 1
