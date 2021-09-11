import os
from io import BytesIO

import xhtml2pdf.pisa as pisa
from django.http import HttpResponse
from django.template.loader import get_template

from .s3_file_manager import S3


class Render:

    @staticmethod
    def render(path: str, params: dict):
        template = get_template(path)
        html = template.render(params)
        response = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type='application/pdf')
        else:
            return HttpResponse("Error Rendering PDF", status=400)

    @staticmethod
    def render_to_file(path: str, params: dict, pdf_type: str, delete_file=True):
        template = get_template(path)
        html = template.render(params)
        file_name = "{0}.pdf".format(params.get('file_name'))
        file_path = os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/" + pdf_type, file_name)
        s3_path = os.path.join("media/pdfs/" + pdf_type, file_name)
        if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/" + pdf_type)):
            os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/" + pdf_type))
        with open(file_path, 'wb') as pdf:
            pisa.pisaDocument(BytesIO(html.encode("UTF-8")), pdf)
        s3 = S3()
        s3.upload_file_to_bucket(file_name=file_path, key=s3_path)
        if delete_file:
            os.remove(file_path)
        file_path = s3.get_bucket_object(s3_path)
        return [file_name, file_path]

    @staticmethod
    def delete_file(params: dict, pdf_type: str):
        file_name = "{0}.pdf".format(params.get('file_name'))
        file_path = "media/pdfs/" + pdf_type + '/' + file_name
        s3 = S3()
        s3.delete_file_from_bucket(key=file_path)
        return 1
