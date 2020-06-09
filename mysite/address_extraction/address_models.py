"""
Definition of required types.
"""

from typing import Tuple, Optional

LineAddress = Tuple[int, int, int, int]
"""
A tuple of **(page section index, block index, paragraph index, line index)**
"""

LineSimilarity = Tuple[float, LineAddress, Optional[LineAddress]]
"""
A tuple of **(similarity ratio, line 1 address, line 2 address or None)**
"""

SideBoxIndex = Optional[int]
"""
Index of side box can be None
"""

SideBoxes = Tuple[SideBoxIndex, SideBoxIndex]
"""
A tuple of **(bottom box index, right box index)**
"""

AddressResult = Tuple[float, int, str]
"""
A tuple of **(similarity to the project name, confidence from tesserocr, address string)**
"""
