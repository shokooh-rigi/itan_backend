import re
from difflib import SequenceMatcher
from io import StringIO
from typing import List, Tuple

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

from . import image_extractor


# import tesserocr


def extract_text_from_page_image(pdf_path: str, page_number: int) -> str:
    images = image_extractor.convert_to_images(pdf_path, indexes=[page_number], grayscale=True)
    text = tesserocr.image_to_text(images[page_number])
    return text.strip()


def extract_text_from_page(pdf_path: str, page_number: int) -> str:
    input_file = open(pdf_path, 'rb')
    output_string = StringIO()
    extract_text_to_fp(input_file, output_string, laparams=LAParams(), page_numbers=[page_number])
    input_file.close()
    text = output_string.getvalue()
    return text.strip()


def create_map(original_text: str, transformed_text: str) -> List[Tuple[int, str]]:
    len_t = len(transformed_text)
    spaces_map: List[Tuple[int, str]] = []
    i, j = 0, 0

    if transformed_text[i] != original_text[j]:
        spaces = ''
        while transformed_text[i] != original_text[j]:
            spaces = spaces + original_text[j]
            j = j + 1
        spaces_map.append((i - 1, spaces))

    while i < len_t:
        if transformed_text[i] == ' ':
            i = i + 1
            spaces = ''
            while transformed_text[i] != original_text[j]:
                spaces = spaces + original_text[j]
                j = j + 1
            spaces_map.append((i - 1, spaces))
        else:
            i = i + 1
            j = j + 1

    if j < len(original_text):
        spaces = ''
        while j < len(original_text):
            spaces = spaces + original_text[j]
            j = j + 1
        spaces_map.append((i, spaces))

    if len(spaces_map) == 0 or spaces_map[0][0] != -1:
        spaces_map.insert(0, (-1, ''))

    if spaces_map[-1][0] != len_t:
        spaces_map.append((len_t, ''))

    return spaces_map


def get_index(index: int, spaces_map: List[Tuple[int, str]]):
    j = index
    k = 0
    space = spaces_map[k]
    while index >= space[0]:
        j += len(space[1])
        if space[0] != -1:
            j -= 1
        k += 1
        space = spaces_map[k]
    return j


def get_address(pdf_path: str, project_name: str, initial_ratio: float = 1, ratio_limit: float = 0.79,
                ratio_decrease_step: float = 0.02) -> str:
    page_text = extract_text_from_page(pdf_path, 0)

    if len(page_text) == 0:
        page_text = extract_text_from_page_image(pdf_path, 0)

    if len(page_text) == 0:
        raise Exception('Page 0 is empty.')

    text = page_text.lower()
    project_name = project_name.lower()

    text_without_spaces = re.sub(r'\s+', ' ', text).strip()
    project_name = re.sub(r'\s+', ' ', project_name).strip()
    spaces_map = create_map(text, text_without_spaces)

    address_line_1_reg_ex = r"(\d{2,5}\s+)(?![a|p]m\b)(([a-zA-Z|\s+]{1,5}){1,2})?([\s|\,|.]+)?(([a-zA-Z|\s+]{1,30}){1,4})(court|ct|street|st|drive|dr|lane|ln|road|rd|blvd|way)([\s|\,|.|\;]+)?"
    address_line_3_reg_ex = r"(([a-zA-Z|\s+]{1,30}){1,2})([\s|\,|.]+)?\b(AK|AL|AR|AZ|CA|CO|CT|DC|DE|FL|GA|GU|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VI|VT|WA|WI|WV|WY)([\s|\,|.]+)?(\s+\d{5})?([\s|\,|.]+)"

    len_project_name = len(project_name)
    end_i = len(text_without_spaces) - len_project_name + 1
    addresses = []
    temp_addresses = []

    while initial_ratio > ratio_limit:
        # print('check %f' % min_ratio)

        highests = []
        for i in range(end_i):
            substr = text_without_spaces[i: i + len_project_name]
            ratio = SequenceMatcher(None, project_name, substr).ratio()
            if ratio >= initial_ratio:
                highests.append({
                    'ratio': ratio,
                    'substr': substr,
                    'index': i,
                })

        highests.sort(key=lambda item: item['ratio'], reverse=True)
        # print(highests)

        for item in highests:
            index_in_text = get_index(item['index'], spaces_map)
            text_for_search = page_text[index_in_text:]

            search_lines = text_for_search.splitlines()

            address_line_1_index = None
            address_line_3_index = None

            search_lines = [line.strip() for line in search_lines if line.strip()]

            i = 0
            for search_line in search_lines:
                address_line_3 = re.search(
                    address_line_3_reg_ex, search_line, flags=re.IGNORECASE)
                if address_line_3 is not None:
                    address_line_3_index = i
                    break
                i += 1

            if address_line_3_index is not None:
                for j in range(address_line_3_index + 1):
                    search_line = search_lines[j]
                    address_line_1 = re.search(
                        address_line_1_reg_ex, search_line, flags=re.IGNORECASE)
                    if address_line_1 is not None:
                        address_line_1_index = j
                        break

            if address_line_1_index is not None and address_line_3_index is not None:
                if address_line_3_index - 2 <= address_line_1_index:
                    address_arr = search_lines[address_line_1_index: address_line_3_index + 1]
                    new_address = '\n'.join(address_arr)
                    try:
                        ind = temp_addresses.index(new_address)
                        addresses[ind]['count'] += 1
                    except ValueError:
                        temp_addresses.append(new_address)
                        addresses.append({'value': new_address, 'count': 1})
                    # print(item)
                    # print('Address is:\n%s' % '\n'.join(address_arr))
                    # print('-------------------------------------------------------------\n')

        if addresses:
            break
        else:
            initial_ratio -= ratio_decrease_step

    if addresses:
        # print('Addresses:')
        # for add in addresses:
        #     print('-------------------------------------------------')
        #     print('Value:\n%s\nCount: %d' % (add['value'], add['count']))
        return addresses[0]['value']
    else:
        # print('Not found.')
        return ''
