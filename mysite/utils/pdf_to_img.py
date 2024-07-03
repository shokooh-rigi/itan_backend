import requests
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

def pdf_to_image_bytes(s3_url):
    """
    Download a PDF from an S3 link, convert it to images, and return image bytes.
    
    :param s3_url: URL to the PDF file on S3
    :return: List of image bytes
    """
    # Download the PDF file
    response = requests.get(s3_url)
    response.raise_for_status()  # Raise an error for bad status codes

    # Convert the PDF bytes to images
    pdf_bytes = response.content
    images = convert_from_bytes(pdf_bytes)

    image_bytes_list = []

    # Save the images as bytes
    for image in images:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes_list.append(img_byte_arr.getvalue())
    
    return image_bytes_list
