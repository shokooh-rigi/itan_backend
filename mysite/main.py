from typing import List, Tuple
import sys

from address_extraction.address import find_project_addresses


def main(pdf: str, project: str) -> List[Tuple[float, int, str]]:
    return find_project_addresses(pdf, project)


if __name__ == '__main__':
    pdf_path = sys.argv[1]
    project_name = sys.argv[2]
    addresses = main(pdf_path, project_name)
    print(addresses)
