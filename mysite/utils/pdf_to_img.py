# utils.py
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image

def pdf_to_image_bytes(pdf_path):
    """
    Convert a PDF file to images and return image bytes.
    
    :param pdf_path: Path to the PDF file
    :return: List of image bytes
    """
    images = convert_from_path(pdf_path)
    image_bytes_list = []

    for image in images:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes_list.append(img_byte_arr.getvalue())
    
    return image_bytes_list
