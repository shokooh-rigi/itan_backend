import requests
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image


def pdf_to_image_bytes(url):
    """
    Download a PDF from an S3 link, convert it to images, and return image bytes.
    
    :param s3_url: URL to the PDF file on S3
    :return: List of image bytes
    """
    # Download the PDF file
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes

    # Convert the PDF bytes to images
    pdf_bytes = response.content
    # for windows users who wish not to use chocolatey or conda
    # images = convert_from_bytes(pdf_bytes, poppler_path = r'D:\poppler-24.08.0\Library\bin')
    images = convert_from_bytes(pdf_bytes)

    image_bytes_list = []

    # Save the images as bytes
    for image in images:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes_list.append(img_byte_arr.getvalue())
    
    return image_bytes_list
