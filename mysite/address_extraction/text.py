from typing import Tuple
from tesserocr import PyTessBaseAPI, PSM

from .image_models import PILImage, Box
from .text_models import Page, PageSection
from .hocr_models import HOCRParser


def get_best_orientation(image: PILImage, sub_image_number: int) -> Tuple[int, int, PILImage, str]:
    """
    Checks image to text confidence when image rotates 0, 90, 180, 270 degrees
    and returns the best result.

    :param image: a :class:`PILImage` object
    :param sub_image_number: a number that used for assign an id for the PageSection (e.g. index of sub_image)
    :return: a tuple contains (max_confidence, best_rotation_angle, best_image, best_image_hocr_text)
    """

    angles = [0, 90, 180, 270]
    max_confidence = -1
    best_image = None
    best_rotation_angle = None
    hocr_text = None

    with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
        for angle in angles:
            img = image if angle == 0 else image.rotate(angle, expand=True)
            api.SetImage(img)
            mean_conf = api.MeanTextConf()
            if mean_conf > max_confidence:
                max_confidence = mean_conf
                best_image = img
                best_rotation_angle = angle
                hocr_text = api.GetHOCRText(sub_image_number)
    return max_confidence, best_rotation_angle, best_image, hocr_text


def sub_image_to_text(sub_image: PILImage, location_box: Box, sub_image_number: int, parent: Page) -> PageSection:
    """
    Creates a :class:`PageSection` object related to the sub_image.

    :param sub_image: the sub image
    :param location_box: location of the sub_image in the actual image
    :param sub_image_number: a number that used for assign an id for the PageSection (e.g. index of sub_image)
    :param parent: the Page object related to the actual image
    :return: the PageSection object if created else None
    """

    assert parent is not None, "The parent page (:class:`Page`) object can not be None."
    page_sections_len = len(parent.page_sections)

    max_confidence, best_rotation_angle, best_image, hocr_text = get_best_orientation(sub_image, sub_image_number)

    hocr_parser = HOCRParser(parent, location_box, best_rotation_angle)
    hocr_parser.feed(hocr_text)
    hocr_parser.close()

    new_page_sections_len = len(parent.page_sections)
    return parent.page_sections[-1] if page_sections_len != new_page_sections_len else None
