# -*- coding: utf-8 -*-
r"""
Startup banner for apply_localization.py -- solid pixel-block "BFME"
wordmark (Impact font -> 1-bit mask -> Unicode half-block characters at
2x vertical density), painted with a left-to-right gold -> fiery-red
gradient (same palette as before, gradient direction now horizontal to
match a chunky pixel-art CLI-banner look), evoking the game's own
gold-on-dark-leather title screen.

The art is a one-time render hardcoded here as plain text so the toolkit
keeps its zero-pip-dependency rule at runtime -- no imaging library
needed to just print a banner.
"""
import os

BFME_ROWS = [
    "  ▄▄▄▄▄▄▄▄▄▄      ▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄  ",
    "  ████████████▄   █████████  ███████  ▄███████  ██████████  ",
    "  ██████▀▀█████   █████████  ████████ ████████  ██████████  ",
    "  ██████  █████   █████      ████████ ████████  ██████      ",
    "  ██████▄▄█████   █████▄     ████████▄████████  ██████▄     ",
    "  ████████████    █████████  █████████████████  ██████████  ",
    "  ██████▀▀█████   █████████  █████████████████  ██████████  ",
    "  ██████  ██████  █████      █████ █████ █████  ██████      ",
    "  ██████  ██████  █████      █████ █████ █████  ██████      ",
    "  ██████▄▄██████  █████      █████ █████ █████  ██████████  ",
    "  █████████████   █████      █████ █████ █████  ██████████  ",
    "  ▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀▀▀      ▀▀▀▀▀  ▀▀▀  ▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀  ",
]

# gold (left) -> deep fire-red (right), matching the game's embossed
# gold-lettering-on-dark-leather title/credits screens
GRADIENT_LEFT = (232, 191, 115)   # warm antique gold
GRADIENT_RIGHT = (150, 40, 20)    # deep ember red


def _lerp(a, b, t):
    return round(a + (b - a) * t)


def _col_color(col_idx, total_cols):
    t = col_idx / max(1, total_cols - 1)
    r = _lerp(GRADIENT_LEFT[0], GRADIENT_RIGHT[0], t)
    g = _lerp(GRADIENT_LEFT[1], GRADIENT_RIGHT[1], t)
    b = _lerp(GRADIENT_LEFT[2], GRADIENT_RIGHT[2], t)
    return r, g, b


def _enable_windows_ansi():
    if os.name != 'nt':
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass


def _print_gradient_block(rows, indent=0):
    width = max(len(r) for r in rows)
    pad = ' ' * indent
    for line in rows:
        out = [pad]
        for x, ch in enumerate(line):
            if ch == ' ':
                out.append(' ')
                continue
            r, g, b = _col_color(x, width)
            out.append(f'\033[38;2;{r};{g};{b}m{ch}\033[0m')
        print(''.join(out))


def print_info_table(rows):
    """Prints a bordered label/value table (Unicode box-drawing chars),
    horizontally centered under the BFME wordmark above it -- rows is a
    list of (label, value) string pairs."""
    label_w = max(len(l) for l, _ in rows)
    value_w = max(len(v) for _, v in rows)
    content_w = label_w + 3 + value_w  # "label : value"
    box_w = content_w + 4              # "| " + content + " |"

    banner_w = len(BFME_ROWS[0]) + 2  # +2 for print_banner()'s own indent=2
    indent = max(0, (banner_w - box_w) // 2)
    pad = ' ' * indent

    dim = '\033[2m'
    reset = '\033[0m'
    print(f'{pad}{dim}┌{"─" * (box_w - 2)}┐{reset}')
    for label, value in rows:
        line = f'{label.ljust(label_w)} : {value.ljust(value_w)}'
        print(f'{pad}{dim}│{reset} {line} {dim}│{reset}')
    print(f'{pad}{dim}└{"─" * (box_w - 2)}┘{reset}')


def print_banner():
    _enable_windows_ansi()
    print()
    _print_gradient_block(BFME_ROWS, indent=2)
    print()
    ua_blue = '\033[38;2;0;87;183m'    # Ukrainian flag blue
    ua_yellow = '\033[38;2;255;213;0m'  # Ukrainian flag yellow
    reset = '\033[0m'
    tagline = (
        f'  \033[2m~ LOCALIZATION MANAGER BY CLEVER PLAY {reset}'
        f'{ua_blue}U{reset}{ua_yellow}A{reset}\033[2m ~{reset}'
    )
    print(tagline)
    print()


if __name__ == '__main__':
    print_banner()
