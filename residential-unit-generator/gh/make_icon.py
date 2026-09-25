from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png_bytes(width: int, height: int, rgba_rows) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + row for row in rgba_rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    w = h = 24
    background = (22, 28, 36)
    panel = (57, 192, 128)
    line = (225, 245, 255)

    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            color = background
            if 2 <= x <= 21 and 2 <= y <= 21:
                color = panel
            if 2 <= x <= 21 and y in (2, 21):
                color = line
            if x in (2, 21) and 2 <= y <= 21:
                color = line
            if 9 <= x <= 14 and y in (9, 14):
                color = line
            if x in (9, 14) and 9 <= y <= 14:
                color = line
            row.extend(color)
        rows.append(bytes(row))

    out = Path(__file__).resolve().parent
    out.joinpath("icon.png").write_bytes(_png_bytes(w, h, rows))
    print("wrote icon.png")


if __name__ == "__main__":
    main()
