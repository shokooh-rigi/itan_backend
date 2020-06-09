from typing import List, Dict, Tuple, Union
from contextlib import contextmanager
import numpy as np
import cv2
from PIL import Image as PILImageModule
from pdf2image import convert_from_path

from .image_models import BoxSize, Box, CV2Image, PILImage, XImage, Line


@contextmanager
def ignore_pil_max_image_pixels() -> None:
    """
    Implementing the Context Manager as a Generator for temporary ignore Image.DecompressionBombError

    usage:
        with ignore_pil_image_max_image_pixels():
            do some thing with large images
    """

    max_image_pixels = PILImageModule.MAX_IMAGE_PIXELS
    PILImageModule.MAX_IMAGE_PIXELS = None
    yield
    PILImageModule.MAX_IMAGE_PIXELS = max_image_pixels


def pdf_to_images(pdf_path: str, indexes: List[int], resolution: int = 200, image_format: str = 'jpg',
                  grayscale: bool = False, output_folder: str = None, paths_only: bool = False,
                  size: Union[BoxSize, int] = None) -> Dict[int, Union[PILImage, str]]:
    """
    Convert specific pages of a PDF file to Image

    :param pdf_path: path to the PDF that you want to convert
    :param indexes: zero based pages indexes that you want to convert
    :param resolution: image resolution in DPI (default 200)
    :param image_format: output image format (default 'jpg')
    :param grayscale: output grayscale images (default False)
    :param output_folder: write the resulting images to a folder (instead of directly in memory)
    :param paths_only: don't load image(s), return paths instead (requires output_folder)
    :param size: size of the resulting image(s), uses the Pillow (width, height) standard or max(width, height)
    :return: a Dict from [page_number, image] or [page_number, image_path]
    """

    result: Dict[int, PILImage] = {}
    for i in indexes:
        images = convert_from_path(pdf_path, dpi=resolution, fmt=image_format, first_page=i + 1, last_page=i + 1,
                                   grayscale=grayscale, output_folder=output_folder, paths_only=paths_only, size=size)
        result[i] = images[0]
    return result


def is_cv2_image(image: XImage) -> bool:
    return type(image) is CV2Image


def resize_image(image: XImage, size: BoxSize = None, ratio: float = None, max_dim: int = None,
                 min_dim: int = None) -> Union[Tuple[XImage, float], Tuple[XImage, float, float]]:
    """
    Resize the image.

    First checks `size` parameter, then `ratio`, then, `max_dim`, then `min_dim`. only one of them will be applied.
    the source image is not affected.

    :param image: the image to resize
    :param size: new size (width, height)
    :param ratio: the ratio of the new size to the old size
    :param max_dim: maximum of dimensions in pixels
    :param min_dim: minimum of dimensions in pixels
    :return: the new image with ratio (new_image, ratio) or
    the new image with two ratios (new_image, width_ratio, height_ratio) when aspect size is supplied
    """

    is_cv2image = is_cv2_image(image)
    old_width, old_height = (image.shape[1], image.shape[0]) if is_cv2image else image.size

    def _resize(_image, _size):
        return cv2.resize(_image, _size) if is_cv2image else _image.resize(_size)

    if size is not None:
        new_width, new_height = size
        w_ratio = new_width / old_width
        if new_width * old_height == new_height * old_width:
            h_ratio = w_ratio
        else:
            h_ratio = new_height / old_height
        new_image = _resize(image, (new_width, new_height))
        return new_image, w_ratio, h_ratio
    else:
        if ratio is not None:
            wh_ratio = ratio
        elif max_dim is not None:
            wh_ratio = max_dim / max(old_width, old_height)
        elif min_dim is not None:
            wh_ratio = min_dim / min(old_width, old_height)
        else:
            raise Exception("One of the size, ratio, max_dim or min_dim must be supplied.")

        new_width = int(old_width * wh_ratio)
        new_height = int(old_height * wh_ratio)
        new_image = _resize(image, (new_width, new_height))
        return new_image, wh_ratio


def is_box_in_area(box: Box, area: Box) -> bool:
    xb, yb, wb, hb = box
    xa, ya, wa, ha = area
    return xa <= xb and ya <= yb and (xb + wb <= xa + wa) and (yb + hb <= ya + ha)


def get_image_size(image_path: str) -> BoxSize:
    """
    Get image size without loading it in memory.

    :param image_path: path to the image
    :return: size of image (width, height)
    """

    with ignore_pil_max_image_pixels():
        image = PILImageModule.open(image_path)
        size = image.size
    return size


def imshow(window_name: str, image: CV2Image) -> None:
    print("Press 'c' on image preview to close..")
    cv2.imshow(window_name, image)
    char = 0
    while char != 99:
        char = cv2.waitKey()
    cv2.destroyWindow(window_name)


def is_up_2_down_line(line: Line) -> bool:
    return line[1] < line[3]


def is_left_2_right_line(line: Line) -> bool:
    return line[0] < line[2]


def is_vertical_line(line: Line) -> bool:
    return -2 < (line[0] - line[2]) < 2


def is_horizontal_line(line: Line) -> bool:
    return -2 < (line[1] - line[3]) < 2


def remove_straight_lines(image: CV2Image) -> CV2Image:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary_inv = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
    min_line_length = int(0.0525 * image.shape[0])
    fast_line_detector = cv2.ximgproc.createFastLineDetector(_length_threshold=min_line_length)
    lines = fast_line_detector.detect(binary_inv)
    _, labels = cv2.connectedComponents(binary_inv, connectivity=4)
    lines_filter = np.ones(labels.shape, 'uint8')
    checked_labels = []
    offset = 5
    cross_offset = 1

    def change_filter(_start_label: int, _end_label: int) -> None:
        nonlocal lines_filter
        if _start_label != 0 and _start_label not in checked_labels:
            lines_filter = lines_filter * (labels != _start_label)
            checked_labels.append(_start_label)
        if _end_label != 0 and _end_label != _start_label and _end_label not in checked_labels:
            lines_filter = lines_filter * (labels != _end_label)
            checked_labels.append(_end_label)

    for li in lines:
        line = li[0]
        start = (int(line[0]), int(line[1]))
        end = (int(line[2]), int(line[3]))

        if is_vertical_line(line):
            if is_up_2_down_line(line):
                start_label = labels[start[1] + offset][start[0] + cross_offset]
                end_label = labels[end[1] - offset][end[0] + cross_offset]
            else:
                start_label = labels[start[1] - offset][start[0] - cross_offset]
                end_label = labels[end[1] + offset][end[0] - cross_offset]
            change_filter(start_label, end_label)

        if is_horizontal_line(line):
            if is_left_2_right_line(line):
                start_label = labels[start[1] - cross_offset][start[0] + offset]
                end_label = labels[end[1] - cross_offset][end[0] - offset]
            else:
                start_label = labels[start[1] + cross_offset][start[0] - offset]
                end_label = labels[end[1] + cross_offset][end[0] + offset]
            change_filter(start_label, end_label)

    lines_filter_3 = cv2.cvtColor(lines_filter, cv2.COLOR_GRAY2BGR)
    return 255 - lines_filter_3 * (255 - image)


def get_text_boxes_from_image(image_path: str, gaussian_ksize: BoxSize = (31, 31), dilate_ksize: BoxSize = (8, 8)
                              ) -> List[Tuple[Box, int]]:
    """
    The idea is taken from `here <https://stackoverflow.com/a/57262099>`_.

    Steps:
        - Remove straight lines from the image
        - Convert image to grayscale and `Gaussian` blur
        - `Otsu`'s threshold
        - Dilate to connect adjacent words together
        - Find contours and draw bounding box

    **Note: default values works best for image with maximum (width, height) = 3000,
    for other images, you may need to adjust function arguments**

    :param image_path: path to the image
    :param gaussian_ksize: kernel size for the GaussianBlur filter (default (19, 19))
    :param dilate_ksize: kernel size for the dilate function (default (8, 8))
    :return: list of detected boxes, List[(box, hierarchy_level)]
    """

    original_image = cv2.imread(image_path)

    # detect and remove straight lines
    original_image = remove_straight_lines(original_image)

    gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, gaussian_ksize, 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Create rectangular structuring element and dilate
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilate_ksize)
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    # Find contours
    contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    boxes: List[Tuple[Box, int]] = []
    for i in range(len(contours)):
        boxes.append((cv2.boundingRect(contours[i]), 0))
    return boxes


def draw_boxes_on_image(image_path: str, boxes: List[Tuple[Box, int]], max_dim: int = 1500,
                        preview: bool = True, save: bool = False, colors: List[Tuple[int, int, int]] = None,
                        remove_lines: bool = True) -> None:
    """
    Draws boxes on given image and previews it.

    :param image_path: path to the image
    :param boxes: list of boxes, List[(box, hierarchy_level)]
    :param max_dim: maximum dimension of the preview image (default 1500), -1 for original size
    :param preview: preview the image or not (default True)
    :param save: save the image or not (default False)
    :param colors: list of colors for boxes in BGR format (default has 7 colors
                    [magenta, red, yellow, green, cyan, blue, white])
    :param remove_lines: if is True straight lines will be removed from preview image (default True)
    """

    if colors is None:
        colors = [
            (247, 132, 236),  # magenta
            (65, 66, 244),  # red
            (66, 226, 247),  # yellow
            (18, 219, 87),  # green
            (242, 242, 52),  # cyan
            (242, 118, 50),  # blue
            (255, 255, 255)  # white
        ]

    original_image = cv2.imread(image_path)

    if remove_lines:
        original_image = remove_straight_lines(original_image)

    if max_dim < 1:
        image, ratio = original_image, 1
    else:
        image, ratio = resize_image(original_image, max_dim=max_dim)
        del original_image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted = cv2.cvtColor(255 - gray, cv2.COLOR_GRAY2BGR)
    max_valid_level = len(colors) - 1
    for box, level in boxes:
        if level <= max_valid_level:
            x = int(box[0] * ratio)
            y = int(box[1] * ratio)
            w = int(box[2] * ratio)
            h = int(box[3] * ratio)
            cv2.rectangle(inverted, (x, y), (x + w, y + h), colors[level], 2)

    # save image
    if save:
        pth = image_path.split('.')
        cv2.imwrite('{}_boxes.{}'.format(pth[0], pth[1]), inverted)

    # preview image
    if preview:
        imshow(image_path.split('/')[-1], inverted)
