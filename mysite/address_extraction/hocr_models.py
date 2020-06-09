"""
Definition of required types.
"""

from typing import List, Tuple, Union
from html.parser import HTMLParser
from enum import Enum
import math

from .final import Final
from .image_models import Box, BoxSize, Point, TranslationVector
from .text_models import Text, PageSection, Block, Paragraph, Line, Word


def rotate(point: Point, angle: float) -> Point:
    """
    Rotate a point counterclockwise by a given angle around (0, 0).

    The angle should be given in radians.

    Translation & Rotation around (0,0)

    | cos(a)    -sin(a)     tx |        | x |       | xp |
    | sin(a)     cos(a)     ty |    ×   | y |   =   | yp |
    | 0          0          1  |        | 1 |       | 1  |
    """

    # transfer the coordinates origin from bottom-left to top-left of the image
    px, py = point[0], -point[1]

    qx = math.cos(angle) * px - math.sin(angle) * py
    qy = math.sin(angle) * px + math.cos(angle) * py
    return int(qx), int(-qy)


def rotate_around_a_center(point: Point, center: Point, angle: float) -> Point:
    """
    Rotate a point counterclockwise by a given angle around a given center.

    The angle should be given in radians.
    """

    cx, cy = center
    px, py = point

    # transfer the coordinates origin from bottom-left to top-left of the image
    cy = -cy
    py = -py

    # translation of the origin
    tx = px - cx
    ty = py - cy

    qx = math.cos(angle) * tx - math.sin(angle) * ty + cx
    qy = math.sin(angle) * tx + math.cos(angle) * ty + cy
    return int(qx), int(-qy)


def translate(point: Point, translation_vector: TranslationVector) -> Point:
    """
    Translates given point with t_value

    :param point: the point
    :param translation_vector: the translation vector
    :return: translated point
    """

    return point[0] + translation_vector[0], point[1] + translation_vector[1]


def get_reverse_translate(image_size: BoxSize, angle_rad: float) -> TranslationVector:
    """
    Calculates translation vector from rotated image to source image

    :param image_size: the source image size
    :param angle_rad: the rotation angle in radians
    :return: reverse translation vector
    """

    # corners
    # 0 => top     -  left
    # 1 => top     -  right
    # 2 => bottom  -  left
    # 3 => bottom  -  right

    # image corners
    i0 = (0, 0)
    i1 = (image_size[0], 0)
    i2 = (0, image_size[1])
    i3 = (image_size[0], image_size[1])

    # Step 1
    # rotated image corners
    ri0 = rotate(i0, angle_rad)
    ri1 = rotate(i1, angle_rad)
    ri2 = rotate(i2, angle_rad)
    ri3 = rotate(i3, angle_rad)

    # Step 2
    # reverse translation from <rotated and translated image> to <rotated image>
    # (actually the result of image.rotate(angle, expand=True) to just rotated image)
    return min(ri0[0], ri1[0], ri2[0], ri3[0]), min(ri0[1], ri1[1], ri2[1], ri3[1])


def reverse_rotate(rev_translate: TranslationVector, rev_angle_rad: float, boundary_box: Box) -> Box:
    """
    Reverse translate and reverse rotate to get boundary_box in sub_image without rotation.

    :param rev_translate: a vector reverse translates from rotated image to sub_image
    :param rev_angle_rad: an angle to reverse rotate from rotated image to sub_image
    :param boundary_box: a box in rotated image
    :return: a box in sub_image
    """

    # Step 3
    # reverse translate
    rt_bbox = boundary_box[0], boundary_box[1], boundary_box[0] + boundary_box[2], boundary_box[1] + boundary_box[3]
    rev_trans_rt_bb0 = translate((rt_bbox[0], rt_bbox[1]), rev_translate)
    rev_trans_rt_bb1 = translate((rt_bbox[2], rt_bbox[1]), rev_translate)
    rev_trans_rt_bb2 = translate((rt_bbox[0], rt_bbox[3]), rev_translate)
    rev_trans_rt_bb3 = translate((rt_bbox[2], rt_bbox[3]), rev_translate)

    # Step 4
    # reverse rotate the reverse translated points
    rev_rot_rev_trans_rt_bb0 = rotate(rev_trans_rt_bb0, rev_angle_rad)
    rev_rot_rev_trans_rt_bb1 = rotate(rev_trans_rt_bb1, rev_angle_rad)
    rev_rot_rev_trans_rt_bb2 = rotate(rev_trans_rt_bb2, rev_angle_rad)
    rev_rot_rev_trans_rt_bb3 = rotate(rev_trans_rt_bb3, rev_angle_rad)

    # reverse rotated and reverse translated rt_bbox
    rev_rt_bbox = rev_rot_rev_trans_rt_bb0, rev_rot_rev_trans_rt_bb1, rev_rot_rev_trans_rt_bb2, rev_rot_rev_trans_rt_bb3
    rev_rt_bbox_expanded = (min(rev_rt_bbox[0][0], rev_rt_bbox[1][0], rev_rt_bbox[2][0], rev_rt_bbox[3][0]),
                            min(rev_rt_bbox[0][1], rev_rt_bbox[1][1], rev_rt_bbox[2][1], rev_rt_bbox[3][1]),
                            max(rev_rt_bbox[0][0], rev_rt_bbox[1][0], rev_rt_bbox[2][0], rev_rt_bbox[3][0]),
                            max(rev_rt_bbox[0][1], rev_rt_bbox[1][1], rev_rt_bbox[2][1], rev_rt_bbox[3][1]))

    return (rev_rt_bbox_expanded[0],
            rev_rt_bbox_expanded[1],
            rev_rt_bbox_expanded[2] - rev_rt_bbox_expanded[0],
            rev_rt_bbox_expanded[3] - rev_rt_bbox_expanded[1])


class HOCRConstants(Enum):
    """
    HTML and HOCR constants
    """

    # html tag attributes names
    HTML_ATR_CLASS = "class"
    HTML_ATR_ID = "id"
    HTML_ATR_LANG = "lang"
    HTML_ATR_TITLE = "title"

    # hocr classes
    OCR_CLS_PAGE = "ocr_page"
    OCR_CLS_BLOCK = "ocr_carea"
    OCR_CLS_PARAGRAPH = "ocr_par"
    OCR_CLS_LINE = "ocr_line"
    OCR_CLS_WORD = "ocrx_word"

    # hocr attributes
    OCR_ATR_BBOX = "bbox"
    OCR_ATR_ANGLE = "textangle"
    OCR_ATR_SIZE = "x_size"
    OCR_ATR_CONFIDENCE = "x_wconf"


class HOCRAttributes:
    id: str = None
    klass: HOCRConstants = None
    boundary_box: Box = None
    confidence: int = None
    angle: int = 0
    font_size: float = None
    language: str = None

    def __init__(self, attributes: List[Tuple[str, str]]):
        self._calc_attributes(attributes)

    def _calc_attributes(self, attributes: List[Tuple[str, str]]):
        def safe_int(value: str) -> int:
            return int(float(value))

        for key, val in attributes:
            key = key.strip()
            val = val.strip()

            if key == HOCRConstants.HTML_ATR_ID.value:
                self.id = val

                if val.startswith('page'):
                    self.klass = HOCRConstants.OCR_CLS_PAGE
                elif val.startswith('block'):
                    self.klass = HOCRConstants.OCR_CLS_BLOCK
                elif val.startswith('par'):
                    self.klass = HOCRConstants.OCR_CLS_PARAGRAPH
                elif val.startswith('line'):
                    self.klass = HOCRConstants.OCR_CLS_LINE
                elif val.startswith('word'):
                    self.klass = HOCRConstants.OCR_CLS_WORD

            elif key == HOCRConstants.HTML_ATR_LANG.value:
                self.language = val

            elif key == HOCRConstants.HTML_ATR_TITLE.value:
                temp = val.split(';')
                for item in temp:
                    ocr_attrs = (item.strip()).split(' ')
                    ocr_key = ocr_attrs[0]

                    if ocr_key == HOCRConstants.OCR_ATR_BBOX.value:
                        x_start, y_start = safe_int(ocr_attrs[1]), safe_int(ocr_attrs[2])
                        x_end, y_end = safe_int(ocr_attrs[3]), safe_int(ocr_attrs[4])
                        self.boundary_box = x_start, y_start, (x_end - x_start), (y_end - y_start)

                    elif ocr_key == HOCRConstants.OCR_ATR_ANGLE.value:
                        self.angle = safe_int(ocr_attrs[1])

                    elif ocr_key == HOCRConstants.OCR_ATR_SIZE.value:
                        self.font_size = float(ocr_attrs[1])

                    elif ocr_key == HOCRConstants.OCR_ATR_CONFIDENCE.value:
                        self.confidence = safe_int(ocr_attrs[1])


class HOCRParserState(Final):
    node: Text = None
    attributes: HOCRAttributes = None
    data: str = ''

    def __init__(self, node: Union[Text, None], attributes: HOCRAttributes, parent):
        """
        This class holds the state of each hocr tag.

        :param node: the text object related to the hocr tag
        :param attributes: attributes of this hocr tag
        :param parent: the parent state
        """

        super().__init__(['node', 'attributes', 'parent'])
        self.node = node
        self.attributes = attributes
        self.parent: HOCRParserState = parent


class HOCRParser(HTMLParser):
    __OCR_TO_TEXT = {
        HOCRConstants.OCR_CLS_PAGE: PageSection,
        HOCRConstants.OCR_CLS_BLOCK: Block,
        HOCRConstants.OCR_CLS_PARAGRAPH: Paragraph,
        HOCRConstants.OCR_CLS_LINE: Line,
        HOCRConstants.OCR_CLS_WORD: Word,
    }

    __sub_image_location: Tuple[int, int] = None
    __rotation: float = None
    __reverse_rotation: float = None
    __reverse_t_vector: TranslationVector = None

    __parent_state: HOCRParserState = None
    __current_state: HOCRParserState = None

    def __init__(self, parent_text: Text, sub_image_box: Box, rotation_angle: int):
        """
        Parses HOCR string from tesserocr and convert it to :class:`Text` classes
        (e.g. :class:`Word`, :class:`Line`, ...)

        :param parent_text: the parent text object that the converted HOCR belongs to it.
        :param sub_image_box: location of the sub_image in actual image
        :param rotation_angle: The amount (in degrees) that the sub_image (and hocr result) was rotated.
        """

        super().__init__()
        self.__current_state = HOCRParserState(parent_text, HOCRAttributes([]), None)

        self.__sub_image_location = sub_image_box[0], sub_image_box[1]
        sub_image_size = sub_image_box[2], sub_image_box[3]
        self.__rotation = rotation_angle
        self.__reverse_rotation = math.radians(-rotation_angle)
        self.__reverse_t_vector = get_reverse_translate(sub_image_size, math.radians(rotation_angle))

    # HTMLParser hooks =================================================================================================
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        # set the parent node equal to the old node (__current_node)
        self.__parent_state = self.__current_state

        attributes = HOCRAttributes(attrs)
        if attributes.klass is not None:
            # do some transformations to get boundary_box in actual image (not in sub_image!)
            attributes.boundary_box = reverse_rotate(self.__reverse_t_vector, self.__reverse_rotation,
                                                     attributes.boundary_box)
            point = attributes.boundary_box[0], attributes.boundary_box[1]
            tr_point = translate(point, self.__sub_image_location)
            attributes.boundary_box = tr_point[0], tr_point[1], attributes.boundary_box[2], attributes.boundary_box[3]

            # correct the angle value
            attributes.angle = attributes.angle - self.__rotation

            # create the new node and set it's parent
            klass = self.__OCR_TO_TEXT[attributes.klass]
            node = klass(attributes.id, attributes.boundary_box, self.__parent_state.node)
        else:
            node = None

        # create the new state and set it's parent
        self.__current_state = HOCRParserState(node, attributes, self.__parent_state)

    def handle_endtag(self, tag: str) -> None:
        cs = self.__current_state
        if cs.node is not None:
            if isinstance(cs.node, Word):
                cs.node.confidence = cs.attributes.confidence
                cs.node.text = cs.data
            else:
                if isinstance(cs.node, Line):
                    cs.node.angle = cs.attributes.angle
                    cs.node.font_size = cs.attributes.font_size
                elif isinstance(cs.node, Paragraph):
                    cs.node.language = cs.attributes.language
                cs.node.calc_props()

            # if node has no text remove it from parent node
            if not cs.node.text:
                if isinstance(cs.node, Word):
                    cs.node.parent.words.pop()
                elif isinstance(cs.node, Line):
                    cs.node.parent.lines.pop()
                elif isinstance(cs.node, Paragraph):
                    cs.node.parent.paragraphs.pop()
                elif isinstance(cs.node, Block):
                    cs.node.parent.blocks.pop()
                elif isinstance(cs.node, PageSection):
                    cs.node.parent.page_sections.pop()
        else:
            self.__parent_state.data = self.__parent_state.data + self.__current_state.data

        # back to the parent node
        self.__current_state = self.__parent_state
        self.__parent_state = self.__current_state.parent

    def handle_data(self, data: str) -> None:
        data = data.strip()
        if data:
            self.__current_state.data = self.__current_state.data + data

    def error(self, message: str) -> None:
        raise Exception(message)

    # end of hooks =====================================================================================================
