from typing import List, Dict

from PIL import Image
from pdf2image import convert_from_path

PILImage = Image.Image
Result = Dict[int, PILImage]


def convert_to_images(pdf_path: str, indexes: List[int], resolution: int = 500, image_format: str = 'jpg',
                      grayscale: bool = False) -> Result:
    """
    Description: Convert specific pages of PDF to Image

    :param pdf_path: Path to the PDF that you want to convert
    :param indexes: Pages indexes that you want to convert
    :param resolution: Image resolution in DPI (default 500)
    :param image_format: Output image format (default 'jpg')
    :param grayscale: Output grayscale images (default False)
    :return: a Dict from [page_number, image]
    """

    result: Result = {}
    for i in indexes:
        images = convert_from_path(pdf_path, dpi=resolution, fmt=image_format, first_page=i + 1, last_page=i + 1,
                                   grayscale=grayscale)
        result[i] = images[0]
    return result
