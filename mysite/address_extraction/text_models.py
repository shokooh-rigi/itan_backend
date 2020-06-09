"""
Definition of required types.
"""

from typing import List
from enum import Enum

from .final import Final
from .image_models import Box


class TextOrientation(Enum):
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4


class Text(Final):
    id: str
    boundary_box: Box
    orientation: TextOrientation
    confidence: int
    text: str

    def __init__(self, identity: str, boundary_box: Box):
        """
        Abstracts any text segment in the page

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        """

        super().__init__()
        self.id = identity
        self.boundary_box = boundary_box

    def _re_assign(self, key, value) -> None:
        self.__dict__[key] = value

    def calc_orientation(self) -> None:
        raise NotImplementedError()

    def calc_confidence(self) -> None:
        raise NotImplementedError()

    def calc_text(self) -> None:
        raise NotImplementedError()

    def calc_props(self) -> None:
        self.calc_orientation()
        self.calc_confidence()
        self.calc_text()


def _calc_orientation(children: List[Text]) -> TextOrientation:
    up = left = down = right = 0
    for child in children:
        if child.orientation is TextOrientation.UP:
            up += 1
        elif child.orientation is TextOrientation.LEFT:
            left += 1
        elif child.orientation is TextOrientation.DOWN:
            down += 1
        else:
            right += 1

    mx = max(up, left, down, right)
    if mx == up:
        return TextOrientation.UP
    elif mx == left:
        return TextOrientation.LEFT
    elif mx == down:
        return TextOrientation.DOWN
    else:
        return TextOrientation.RIGHT


class Word(Text):

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents a word object

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the line (see :class:`Line`) that this word belongs to it.
        """

        super().__init__(identity, boundary_box)
        self.parent: Line = parent
        self.parent.words.append(self)

    def calc_orientation(self) -> None:
        pass

    def calc_confidence(self) -> None:
        pass

    def calc_text(self) -> None:
        pass


class Line(Text):
    angle: int
    font_size: float

    words: List[Word]

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents a line object

        contains several words (see :class:`Word`)

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the paragraph (see :class:`Paragraph`) that this line belongs to it.
        """

        super().__init__(identity, boundary_box)
        self.parent: Paragraph = parent
        self.parent.lines.append(self)
        self.words = []

    def calc_orientation(self) -> None:
        assert self.angle is not None, 'The angle must have value.'
        self._re_assign('angle', self.angle % 360)
        if 0 <= self.angle <= 45 or 315 <= self.angle <= 360:
            self.orientation = TextOrientation.UP
        elif 45 < self.angle <= 135:
            self.orientation = TextOrientation.LEFT
        elif 135 < self.angle <= 225:
            self.orientation = TextOrientation.DOWN
        else:
            self.orientation = TextOrientation.RIGHT

        for word in self.words:
            word.orientation = self.orientation

    def calc_confidence(self) -> None:
        if self.words:
            self.confidence = sum([word.confidence for word in self.words]) // len(self.words)
        else:
            self.confidence = 0

    def calc_text(self) -> None:
        self.text = ' '.join([word.text for word in self.words])


class Paragraph(Text):
    language: str

    lines: List[Line]

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents a paragraph object

        contains several lines (see :class:`Line`)

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the block (see :class:`Block`) that this paragraph belongs to it.
        """

        super().__init__(identity, boundary_box)
        self.parent: Block = parent
        self.parent.paragraphs.append(self)
        self.lines = []

    def calc_orientation(self) -> None:
        self.orientation = _calc_orientation(self.lines)

    def calc_confidence(self) -> None:
        sum_conf = sum_len = 0
        for line in self.lines:
            words_conf = [word.confidence for word in line.words]
            sum_conf += sum(words_conf)
            sum_len += len(words_conf)

        if sum_len == 0:
            self.confidence = 0
        else:
            self.confidence = sum_conf // sum_len

    def calc_text(self) -> None:
        self.text = '\n'.join([line.text for line in self.lines])


class Block(Text):
    paragraphs: List[Paragraph]

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents a block object

        contains several paragraphs (see :class:`Paragraph`)

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the page section (see :class:`PageSection`) that this block belongs to it.
        """

        super().__init__(identity, boundary_box)
        self.parent: PageSection = parent
        self.parent.blocks.append(self)
        self.paragraphs = []

    def calc_orientation(self) -> None:
        self.orientation = _calc_orientation(self.paragraphs)

    def calc_confidence(self) -> None:
        sum_conf = sum_len = 0
        for paragraph in self.paragraphs:
            for line in paragraph.lines:
                words_conf = [word.confidence for word in line.words]
                sum_conf += sum(words_conf)
                sum_len += len(words_conf)

        if sum_len == 0:
            self.confidence = 0
        else:
            self.confidence = sum_conf // sum_len

    def calc_text(self) -> None:
        self.text = '\n\n'.join([paragraph.text for paragraph in self.paragraphs])


class PageSection(Text):
    blocks: List[Block]

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents part of the page

        contains several blocks (see :class:`Block`)

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the page (see :class:`Page`) that this section belongs to it.
        """

        identity = 'page_section_%s' % identity.split('_')[1]
        super().__init__(identity, boundary_box)
        self.parent: Page = parent
        self.parent.page_sections.append(self)
        self.blocks = []

    def calc_orientation(self) -> None:
        self.orientation = _calc_orientation(self.blocks)

    def calc_confidence(self) -> None:
        sum_conf = sum_len = 0
        for block in self.blocks:
            for paragraph in block.paragraphs:
                for line in paragraph.lines:
                    words_conf = [word.confidence for word in line.words]
                    sum_conf += sum(words_conf)
                    sum_len += len(words_conf)

        if sum_len == 0:
            self.confidence = 0
        else:
            self.confidence = sum_conf // sum_len

    def calc_text(self) -> None:
        self.text = '\n\n'.join([block.text for block in self.blocks])


class Page(Text):
    page_sections: List[PageSection]

    def __init__(self, identity: str, boundary_box: Box, parent):
        """
        Represents a page object

        contains several page sections (see :class:`PageSection`)

        **note**: the page sections may overlap

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        :param parent: the pdf (see :class:`PDFText`) that this page belongs to it.
        """

        super().__init__(identity, boundary_box)
        self.parent: PDFText = parent
        self.parent.pages.append(self)
        self.page_sections = []

    def calc_orientation(self) -> None:
        pass

    def calc_confidence(self) -> None:
        pass

    def calc_text(self) -> None:
        pass


class PDFText(Text):
    pages: List[Page]

    def __init__(self, identity: str, boundary_box: Box):
        """
        Represents a pdf file converted to text

        contains several pages (see :class:`Page`)

        :param identity: an id for this text object
        :param boundary_box: where this text object located (x_start, y_start, width, height)
        """

        super().__init__(identity, boundary_box)
        self.pages = []

    def calc_orientation(self) -> None:
        pass

    def calc_confidence(self) -> None:
        pass

    def calc_text(self) -> None:
        pass
