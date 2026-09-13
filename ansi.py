from enum import Enum


class Ansi(str, Enum):
    CSI = "\033["


class Cursor(str, Enum):
    erase_display = Ansi.CSI + "2J"
    erase_line = Ansi.CSI + "2K"
    erase_line_right = Ansi.CSI + "K"
    home = Ansi.CSI + "H"
    line_start = Ansi.CSI + "G"
    prev_line = Ansi.CSI + "F"
    prev_line_2 = Ansi.CSI + "2F"
    next_line = Ansi.CSI + "E"


class Color(str, Enum):
    GREEN = Ansi.CSI + "32m"
    YELLOW = Ansi.CSI + "33m"
    RESET = Ansi.CSI + "0m"
