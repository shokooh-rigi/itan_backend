from typing import List, Tuple
import os
from pathlib import Path
from shutil import rmtree
from difflib import SequenceMatcher
import re
from PIL import Image

from .address_models import LineAddress, LineSimilarity, SideBoxIndex, SideBoxes, AddressResult
from .text_models import PDFText, Page, PageSection, Line, TextOrientation
from .image_models import Box, Rectangle
from .text import sub_image_to_text
from .image import pdf_to_images, get_text_boxes_from_image, get_image_size


def box_to_rectangle(box: Box) -> Rectangle:
    return box[0], box[1], box[0] + box[2], box[1] + box[3]


def rectangle_to_box(rectangle: Rectangle) -> Box:
    return rectangle[0], rectangle[1], rectangle[2] - rectangle[0], rectangle[3] - rectangle[1]


def find_side_box(boxes: List[Box], index: int, side: str) -> SideBoxIndex:
    """
    Finds right or bottom box of given box index.

    :param boxes: list of boxes
    :param index: index of the box
    :param side: box in which side is needed (values: 'right', 'bottom')
    :return: the box number found or None if no box exists in this side for given box
    """

    assert side == 'bottom' or side == 'right', "Valid values for side argument are 'bottom' and 'right'"

    x_start, y_start, x_end, y_end = box_to_rectangle(boxes[index])
    side_is_bottom = side == 'bottom'
    side_is_right = side == 'right'
    result = []
    j = 0
    if side_is_bottom or side_is_right:
        for box in boxes:
            if j != index:
                x_start_j, y_start_j, x_end_j, y_end_j = box_to_rectangle(box)
                if side_is_bottom:
                    if x_start < x_end_j and x_start_j < x_end and y_start < y_start_j and y_end < y_end_j:
                        result.append((y_start_j, j))
                elif side_is_right:
                    if y_start < y_end_j and y_start_j < y_end and x_start < x_start_j and x_end < x_end_j:
                        result.append((x_start_j, j))
            j += 1
    result.sort(key=lambda item: item[0])
    return result[0][1] if result else None


def prepare_to_compare(phrase: str) -> str:
    if phrase:
        return re.sub(r'\s+', ' ', phrase.lower().strip())
    else:
        return ''


def is_horizontal_line(line: Line) -> bool:
    if 1 < len(line.text):
        return line.boundary_box[3] <= line.boundary_box[2]
    else:
        return line.orientation == TextOrientation.UP or line.orientation == TextOrientation.DOWN


def is_vertical_line(line: Line) -> bool:
    if 1 < len(line.text):
        return line.boundary_box[2] < line.boundary_box[3]
    else:
        return line.orientation == TextOrientation.LEFT or line.orientation == TextOrientation.RIGHT


def get_similarity_ratio(project_name: str, phrase: str) -> float:
    phrase = prepare_to_compare(phrase)
    return SequenceMatcher(a=project_name, b=phrase).ratio()


def page_section_to_line_address_list(page_section: PageSection, page_section_index: int) -> List[LineAddress]:
    line_address_list = []
    block_index = 0
    for block in page_section.blocks:
        paragraph_index = 0
        for paragraph in block.paragraphs:
            for line_index in range(len(paragraph.lines)):
                line_address_list.append((page_section_index, block_index, paragraph_index, line_index))
            paragraph_index += 1
        block_index += 1
    return line_address_list


def create_temp_directory() -> str:
    temp_dir = os.path.dirname(os.path.realpath(__file__)) + '/temp'
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return temp_dir


def remove_temp_directory(temp_dir) -> None:
    rmtree(temp_dir, ignore_errors=True)


def filter_boxes(image_path: str, boxes: List[Tuple[Box, int]]) -> List[Box]:
    """
    Filters the boxes list for increase performance and accuracy

    :param image_path: path to the image of the page
    :param boxes: list of recognized boxes List[(box, hierarchy_level)]
    :return: list of filtered boxes
    """

    size = get_image_size(image_path)
    image_area = size[0] * size[1]
    max_area = image_area // 20
    min_area = image_area * 5 // 10000
    result = []
    for box, _ in boxes:
        box_area = box[2] * box[3]
        # only boxes with area < 5% of image area
        if min_area <= box_area <= max_area:
            result.append(box)
    return result


def page_boxes_to_text(pdf_text: PDFText, page_number: int, image_path: str,
                       boxes: List[Box]) -> Tuple[List[Box], Page]:
    """
    Converts boxes of pdf page image to Text objects

    :param pdf_text: the parent PDFText object
    :param page_number: the page number that this boxes belongs to
    :param image_path: the image of the pdf page
    :param boxes: recognized boxes of image
    :return: a tuple that contains (non-empty boxes, Page object)
    """

    image = Image.open(image_path)
    page = Page('page_%d' % (page_number + 1), (0, 0, image.size[0], image.size[1]), pdf_text)

    page_section_id = 0
    non_empty_boxes = []
    for box in boxes:
        sub_image = image.crop(box_to_rectangle(box))
        page_section = sub_image_to_text(sub_image, box, page_section_id, page)
        # ignore empty boxes
        if page_section is not None:
            non_empty_boxes.append(box)
            page_section_id += 1
    return non_empty_boxes, page


def calculate_similarity_of_lines_to_project_name(page: Page, side_boxes: List[SideBoxes],
                                                  project_name: str) -> List[LineSimilarity]:
    """
    Calculates similarity of each line to the project name and
    similarity of each two consecutive lines to the project name

    :param page: the page object
    :param side_boxes: list of side boxes fo each box (page section)
    :param project_name: the project name
    :return: list of line similarities
    """

    def get_top_line(g_page_section_i: SideBoxIndex) -> List[Tuple[Line, LineAddress]]:
        result = []
        if g_page_section_i is not None:
            first_line_y = page.boundary_box[3] + 1
            lnx = None
            lnx_address = None
            b_i = 0
            for block in page.page_sections[g_page_section_i].blocks:
                p_i = 0
                for par in block.paragraphs:
                    li_i = 0
                    for lin in par.lines:
                        if lin.boundary_box[1] < first_line_y and is_horizontal_line(lin):
                            first_line_y = lin.boundary_box[1]
                            lnx = lin
                            lnx_address = g_page_section_i, b_i, p_i, li_i
                        li_i += 1
                    p_i += 1
                b_i += 1
            if lnx is not None:
                result.append((lnx, lnx_address))
        return result

    def get_left_line(g_page_section_i: SideBoxIndex) -> List[Tuple[Line, LineAddress]]:
        result = []
        if g_page_section_i is not None:
            first_line_x = page.boundary_box[2] + 1
            lnx = None
            lnx_address = None
            b_i = 0
            for block in page.page_sections[g_page_section_i].blocks:
                p_i = 0
                for par in block.paragraphs:
                    li_i = 0
                    for lin in par.lines:
                        if lin.boundary_box[0] < first_line_x and is_vertical_line(lin):
                            first_line_x = lin.boundary_box[0]
                            lnx = lin
                            lnx_address = g_page_section_i, b_i, p_i, li_i
                        li_i += 1
                    p_i += 1
                b_i += 1
            if lnx is not None:
                result.append((lnx, lnx_address))
        return result

    def add_line_similarities(lines: List[Tuple[Line, LineAddress]]) -> None:
        for a_line, a_line_address in lines:
            line_similarities.append((
                get_similarity_ratio(project_name, a_line.text),
                a_line_address, None
            ))

        len_lines = len(lines)
        for index in range(len_lines - 1):
            l1, l1_address = lines[index]
            l2, l2_address = lines[index + 1]
            line_similarities.append((
                get_similarity_ratio(project_name, l1.text + ' ' + l2.text),
                l1_address, l2_address
            ))

    project_name = prepare_to_compare(project_name)
    line_similarities: List[LineSimilarity] = []

    for i in range(len(page.page_sections)):
        page_section = page.page_sections[i]
        page_section_lines = page_section_to_line_address_list(page_section, i)
        horizontal_lines: List[Tuple[Line, LineAddress]] = []
        vertical_lines: List[Tuple[Line, LineAddress]] = []
        bottom_index, right_index = side_boxes[i]

        for line_address in page_section_lines:
            _, bi, pi, li = line_address
            line = page_section.blocks[bi].paragraphs[pi].lines[li]
            if is_horizontal_line(line):
                horizontal_lines.append((line, line_address))
            elif is_vertical_line(line):
                vertical_lines.append((line, line_address))

        if horizontal_lines:
            horizontal_lines.extend(get_top_line(bottom_index))
            horizontal_lines.sort(key=lambda item: item[0].boundary_box[1])
            add_line_similarities(horizontal_lines)

        if vertical_lines:
            vertical_lines.extend(get_left_line(right_index))
            vertical_lines.sort(key=lambda item: item[0].boundary_box[0])
            add_line_similarities(vertical_lines)

    # remove duplicated line similarities
    i = 0
    length = len(line_similarities) - 1
    while i < length:
        current_ls = line_similarities[i]
        if current_ls[2] is None:
            j = i + 1
            while j <= length:
                ls_j = line_similarities[j]
                if ls_j[2] is None and ls_j[1] == current_ls[1]:
                    line_similarities.pop(j)
                    j -= 1
                    length -= 1
                j += 1
        i += 1

    # sort with ratio
    line_similarities.sort(key=lambda item: item[0], reverse=True)
    return line_similarities


def find_near_addresses(page: Page, side_boxes: List[SideBoxes], project_name_similarity_limit: float,
                        line_similarities: List[LineSimilarity]) -> List[AddressResult]:
    """

    :param page:
    :param side_boxes:
    :param project_name_similarity_limit:
    :param line_similarities:
    :return:
    """

    def get_horizontal_lines(page_section_indexes: List[int], y_start: int) -> List[Line]:
        lines: List[Line] = []
        for j in page_section_indexes:
            ps = page.page_sections[j]
            for blk in ps.blocks:
                for par in blk.paragraphs:
                    for li in par.lines:
                        if is_horizontal_line(li) and y_start < li.boundary_box[1]:
                            lines.append(li)
        lines.sort(key=lambda lin: lin.boundary_box[1])
        return lines

    def get_vertical_lines(page_section_indexes: List[int], x_start: int) -> List[Line]:
        lines: List[Line] = []
        for j in page_section_indexes:
            ps = page.page_sections[j]
            for blk in ps.blocks:
                for par in blk.paragraphs:
                    for li in par.lines:
                        if is_vertical_line(li) and x_start < li.boundary_box[0]:
                            lines.append(li)
        lines.sort(key=lambda lin: lin.boundary_box[0])
        return lines

    def recognize_horizontal_blocks(lines: List[Line]) -> List[List[Line]]:
        if not lines:
            return []
        if len(lines) == 1:
            return [[lines[0]]]
        blocks = []
        block = []
        for i in range(0, len(lines) - 1):
            block.append(lines[i])
            dist = lines[i + 1].boundary_box[1] - lines[i].boundary_box[1] - lines[i].boundary_box[3]
            if min(lines[i].boundary_box[3], lines[i + 1].boundary_box[3]) <= dist:
                blocks.append(block)
                block = []
        block.append(lines[-1])
        blocks.append(block)
        return blocks

    def recognize_vertical_blocks(lines: List[Line]) -> List[List[Line]]:
        if not lines:
            return []
        if len(lines) == 1:
            return [[lines[0]]]
        blocks = []
        block = []
        for i in range(0, len(lines) - 1):
            block.append(lines[i])
            dist = lines[i + 1].boundary_box[0] - lines[i].boundary_box[0] - lines[i].boundary_box[2]
            if min(lines[i].boundary_box[2], lines[i + 1].boundary_box[2]) <= dist:
                blocks.append(block)
                block = []
        block.append(lines[-1])
        blocks.append(block)
        return blocks

    # perform the rest of the process only for the first 5 lines, which are more similar than the similarity limit.
    line_to_check = []
    count = 0
    for ls in line_similarities:
        if project_name_similarity_limit <= ls[0] and count < 5:
            line_to_check.append(ls)
            count += 1
        else:
            break

    addresses: List[AddressResult] = []
    for line_similarity in line_to_check:
        similarity, line_1_add, line_2_add = line_similarity
        l1_ps_i, l1_bl_i, l1_pa_i, l1_li_i = line_1_add
        line_1 = page.page_sections[l1_ps_i].blocks[l1_bl_i].paragraphs[l1_pa_i].lines[l1_li_i]

        if is_horizontal_line(line_1):
            y_s = line_1.boundary_box[1]
            ps_indexes = [l1_ps_i]
            if side_boxes[l1_ps_i][0] is not None:
                ps_indexes.append(side_boxes[l1_ps_i][0])

            if line_2_add is not None:
                l2_ps_i, l2_bl_i, l2_pa_i, l2_li_i = line_2_add
                line_2 = page.page_sections[l2_ps_i].blocks[l2_bl_i].paragraphs[l2_pa_i].lines[l2_li_i]
                y_s = line_2.boundary_box[1]
                if l2_ps_i not in ps_indexes:
                    ps_indexes.append(l2_ps_i)
                if side_boxes[l2_ps_i][0] is not None and side_boxes[l2_ps_i][0] not in ps_indexes:
                    ps_indexes.append(side_boxes[l2_ps_i][0])

            bottom_lines = get_horizontal_lines(ps_indexes, y_s)
            blocks = recognize_horizontal_blocks(bottom_lines)
            if blocks:
                blk = blocks[0]
                conf = sum([ln.confidence for ln in blk]) // len(blk)
                address = '\n'.join([ln.text for ln in blk])
                addresses.append((similarity, conf, address))

        elif is_vertical_line(line_1):
            x_s = line_1.boundary_box[0]
            ps_indexes = [l1_ps_i]
            if side_boxes[l1_ps_i][1] is not None:
                ps_indexes.append(side_boxes[l1_ps_i][1])

            if line_2_add is not None:
                l2_ps_i, l2_bl_i, l2_pa_i, l2_li_i = line_2_add
                line_2 = page.page_sections[l2_ps_i].blocks[l2_bl_i].paragraphs[l2_pa_i].lines[l2_li_i]
                x_s = line_2.boundary_box[0]
                if l2_ps_i not in ps_indexes:
                    ps_indexes.append(l2_ps_i)
                if side_boxes[l2_ps_i][1] is not None and side_boxes[l2_ps_i][1] not in ps_indexes:
                    ps_indexes.append(side_boxes[l2_ps_i][1])

            right_lines = get_vertical_lines(ps_indexes, x_s)
            blocks = recognize_vertical_blocks(right_lines)
            if blocks:
                blk = blocks[0]
                conf = sum([ln.confidence for ln in blk]) // len(blk)
                address = '\n'.join([ln.text for ln in blk])
                addresses.append((similarity, conf, address))

    return addresses


def find_project_addresses(pdf_path: str, project_name: str,
                           pages_to_check: List[int] = None,
                           project_name_similarity_limit: float = 0.7) -> List[AddressResult]:
    """
    Searches the pdf file for given project name and tries to find project address.

    :param pdf_path: the pdf file path
    :param project_name: project name to search
    :param pages_to_check: zero-based page numbers to process for finding project addresses (default [0])
    :param project_name_similarity_limit: minimum value of similarity to the project name (default 0.7)
    :return: a list of founded addresses ordered by (similarity + confidence)
    """

    import time
    ________TTTTTT0 = time.time()

    if pages_to_check is None:
        pages_to_check = [0]

    temp_dir = create_temp_directory()
    pdf_text = None
    addresses: List[AddressResult] = []

    for page_number in pages_to_check:
        image_path = pdf_to_images(pdf_path, [page_number], size=4000,
                                   output_folder=temp_dir, paths_only=True)[page_number]
        boxes = filter_boxes(image_path, get_text_boxes_from_image(image_path))

        if pdf_text is None:
            image_width, image_height = get_image_size(image_path)
            pdf_text = PDFText('pdf_1', (0, 0, image_width, image_height))

        boxes, page = page_boxes_to_text(pdf_text, page_number, image_path, boxes)

        side_boxes: List[SideBoxes] = []
        for i in range(len(boxes)):
            bottom = find_side_box(boxes, i, 'bottom')
            right = find_side_box(boxes, i, 'right')
            side_boxes.append((bottom, right))

        line_similarities = calculate_similarity_of_lines_to_project_name(page, side_boxes, project_name)
        addresses.extend(find_near_addresses(page, side_boxes, project_name_similarity_limit, line_similarities))

    remove_temp_directory(temp_dir)
    addresses.sort(key=lambda item: item[0] * 1000 + item[1], reverse=True)
    print('time => %.3f' % (time.time() - ________TTTTTT0))
    return addresses
