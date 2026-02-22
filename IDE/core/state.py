from dataclasses import dataclass
from typing import Optional

@dataclass
class IDEState:
    current_file: Optional[str] = None
    is_dirty: bool = False