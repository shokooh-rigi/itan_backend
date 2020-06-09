"""
Definition of required types.
"""

from typing import Tuple, Union, List
from numpy import ndarray
from PIL.Image import Image

Box = Tuple[int, int, int, int]
"""
Definition of a box
**(x_start, y_start, width, height)**
"""

BoxSize = Tuple[int, int]
"""
Standard **(width, height)**
"""

Rectangle = Tuple[int, int, int, int]
"""
Definition of a rectangle
**(x_start, y_start, x_end, y_end)**
"""

Point = Tuple[int, int]
"""
Point contains **(x, y)**
"""

Line = List[int]
"""
Line contains **[x_start, y_start, x_end, y_end]**
"""

TranslationVector = Tuple[int, int]
"""
Translation vector (x_translate, y_translate)
"""

PILImage = Image
CV2Image = ndarray
XImage = Union[Image, CV2Image]
"""
The type that can refer to `PILImage` or `CV2Image`
"""
