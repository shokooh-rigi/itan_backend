from .address_extraction import address_extractor


def pdfminer(pdf_path, project_name):
    project_address = address_extractor.get_address(pdf_path, project_name)
    result = {
        'project_name': project_name,
        'project_address': project_address,
    }
    return result
