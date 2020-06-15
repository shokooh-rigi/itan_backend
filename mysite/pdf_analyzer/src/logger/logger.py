from typing import Dict, List, Tuple, Any, Optional
import os
import time
import uuid
import pickle
import json
from shutil import copyfile
from pathlib import Path

from mysite.ibfm.models import iBidFile

from ...models import AddressExtractionRun

from ..address_extraction.image_models import Box, BoxSize
from ..address_extraction.text_models import Page, Line
from ..address_extraction.address_models import LineSimilarity


class AddressLogger:
    __logger_dir: str
    __is_active: bool
    __run: AddressExtractionRun
    __process_images: Dict[int, Dict[str, Any]] = {}
    __process_variables: Dict[int, Dict[str, Any]] = {}

    def __init__(self, bidfile: iBidFile, project_name: str, logger_is_active: bool = True):
        self.__is_active = logger_is_active
        if self.__is_active:
            self.__run = AddressExtractionRun(file=bidfile, project_name=project_name)
            self.__run.save()

            logger_base_dir = self.__run.get_path(self.__run.save_files_to)
            Path(logger_base_dir).mkdir(parents=True, exist_ok=True)
            self.__logger_dir = os.path.join(self.__run.save_files_to, '%d' % self.__run.pk)
            logger_abs_dir = self.__run.get_path(self.__logger_dir)
            Path(logger_abs_dir).mkdir()

    def get_run_id(self) -> int:
        if self.__is_active:
            return self.__run.pk

    def save_object_in_log_directory(self, file_name: str, data: Any) -> str:
        if self.__is_active:
            file_path = os.path.join(self.__logger_dir, file_name)
            file_abs_path = self.__run.get_path(file_path)
            with open(file_abs_path, 'wb') as f_out:
                pickle.dump(data, f_out)
            return file_abs_path

    def copy_file_to_log_directory(self, file_path: str) -> str:
        if self.__is_active:
            dir_name, file_name = os.path.split(file_path)
            dest_file_path = os.path.join(self.__logger_dir, file_name)
            dest_file_abs_path = self.__run.get_path(dest_file_path)
            copyfile(file_path, dest_file_abs_path)
            return dest_file_path.replace("\\", "/")

    def log_run_step(self, step: int, step_progress: int = -1) -> None:
        if self.__is_active:
            self.__run.run_step = step
            self.__run.run_step_progress = step_progress
            self.__run.save()

    def log_processed_image(self, page_number: int, images_path: str, size: BoxSize) -> None:
        if self.__is_active:
            path = self.copy_file_to_log_directory(images_path)
            self.__process_images[page_number + 1] = {
                'width': size[0],
                'height': size[1],
                'url': path
            }

    def log_process_variables(self, page_number: int, all_boxes: List[Box], filtered_boxes: List[Box],
                              page_boxes: List[Box], page: Page, line_similarities: List[LineSimilarity],
                              project_name_similarity_limit: float) -> None:
        if self.__is_active:
            text_boxes = self.generate_text_boxes(page, page_boxes)
            filtered_line_similarities = self.generate_line_similarities(page, line_similarities,
                                                                         project_name_similarity_limit)
            self.__process_variables[page_number + 1] = dict(all_boxes=all_boxes,
                                                             filtered_boxes=filtered_boxes,
                                                             text_boxes=text_boxes,
                                                             line_similarities=filtered_line_similarities,
                                                             related_boxes_to_project_names=[])

    def log_related_boxes_to_project_name(self, page_number: int, line_1: Line, line_2: Optional[Line],
                                          is_horizontal: bool, page_section_indexes: List[int],
                                          bottom_lines: List[Line], blocks: List[List[Line]]) -> None:
        if self.__is_active:
            related_boxes: Dict[str, Any] = dict(
                lines=[dict(boundary_box=line_1.boundary_box, text=line_1.text)],
                is_horizontal=is_horizontal,
                text_boxes=page_section_indexes,
                bottom_lines=[],
                recognized_text_blocks=[]
            )

            if line_2 is not None:
                related_boxes['lines'].append(dict(boundary_box=line_2.boundary_box, text=line_2.text))

            for line in bottom_lines:
                related_boxes['bottom_lines'].append(dict(boundary_box=line.boundary_box, text=line.text))

            for block in blocks:
                text_block = []
                for line in block:
                    text_block.append(dict(boundary_box=line.boundary_box, text=line.text))
                related_boxes['recognized_text_blocks'].append(text_block)

            self.__process_variables[page_number + 1]['related_boxes_to_project_names'].append(related_boxes)

    def log_addresses(self, addresses: List[Tuple[float, int, str]]) -> None:
        if self.__is_active:
            self.__run.addresses = json.dumps(addresses)
            self.__run.save()

    def log_finish_run(self) -> None:
        if self.__is_active:
            self.__run.processed_images = json.dumps(self.__process_images)
            variables_path = self.save_object_in_log_directory(str(uuid.uuid4()) + '.pkl', self.__process_variables)
            self.__run.process_variables = variables_path
            self.__run.execution_time = int(time.time() - self.__run.created_on.timestamp())
            self.__run.is_finished = True
            self.__run.save()

    @staticmethod
    def generate_text_boxes(page: Page, page_boxes: List[Box]) -> List[Dict]:
        text_boxes = []
        i = 0
        for ps in page.page_sections:
            text_box = {
                'bbox': page_boxes[i],
                'boundary_box': ps.boundary_box,
                'text': ps.text,
                'lines': [],
            }
            for blk in ps.blocks:
                for par in blk.paragraphs:
                    for li in par.lines:
                        text_box['lines'].append({
                            'boundary_box': li.boundary_box,
                            'text': li.text
                        })
            text_boxes.append(text_box)
            i += 1
        return text_boxes

    @staticmethod
    def generate_line_similarities(page: Page, line_similarities: List[LineSimilarity],
                                   project_name_similarity_limit: float) -> List[Dict]:
        s_limit = project_name_similarity_limit - 0.2
        logger_line_similarities = []
        count = 0
        for s_ratio, s_line_1, s_line_2 in line_similarities:
            ps_a, b_a, pa_a, l_a = s_line_1
            line_1 = page.page_sections[ps_a].blocks[b_a].paragraphs[pa_a].lines[l_a].text
            line_2 = None
            if s_line_2:
                ps_a, b_a, pa_a, l_a = s_line_2
                line_2 = page.page_sections[ps_a].blocks[b_a].paragraphs[pa_a].lines[l_a].text
            logger_line_similarities.append({
                'ratio': '%s%f' % ('-' if s_ratio < project_name_similarity_limit else '+', s_ratio),
                'line_1': line_1,
                'line_2': line_2,
            })
            count += 1
            if s_ratio < s_limit and 9 < count:
                break
        return logger_line_similarities
