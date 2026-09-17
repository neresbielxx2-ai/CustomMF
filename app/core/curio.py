"""Leitura e escrita de arquivos de cursor do Windows (.cur / .ico) sem dependências extras.

- write_cur(): converte uma PIL.Image em um .cur válido (32bpp ARGB + hotspot).
- read_cursor_file(): abre .cur/.ico (incluindo comprimidos em PNG), .png, .jpg, .bmp, .gif.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------- escrita

def _dib_from_image(img: Image.Image) -> bytes:
    """Gera o DIB (BITMAPINFOHEADER + pixels BGRA + máscara AND) de um .cur."""
    w, h = img.size
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, w * h * 4, 0, 0, 0, 0)
    rgba = img.convert("RGBA").tobytes()  # topo->baixo, RGBA
    px = bytearray(w * h * 4)
    for y in range(h):
        src = (h - 1 - y) * w * 4  # .cur guarda de baixo para cima
        row = rgba[src:src + w * 4]
        dst = y * w * 4
        for x in range(w):
            o = dst + x * 4
            r, g, b, a = row[x * 4:x * 4 + 4]
            px[o] = b
            px[o + 1] = g
            px[o + 2] = r
            px[o + 3] = a
    mask_row = ((w + 31) // 32) * 4
    and_mask = bytes(mask_row * h)  # tudo 0 → canal alpha é quem manda
    return header + bytes(px) + and_mask


def write_cur(img: Image.Image, path, hotspot: tuple[int, int] = (0, 0)) -> Path:
    """Salva a imagem como .cur de 32bpp. Hotspot em pixels (canto = ponta)."""
    img = img.convert("RGBA")
    if img.width > 256 or img.height > 256:
        img.thumbnail((256, 256), Image.LANCZOS)
    w, h = img.size
    hx = max(0, min(w - 1, int(hotspot[0])))
    hy = max(0, min(h - 1, int(hotspot[1])))
    dib = _dib_from_image(img)
    entry = struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, hx, hy, len(dib), 22)
    out = struct.pack("<HHH", 0, 2, 1) + entry + dib
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)
    return path


# ---------------------------------------------------------------- leitura

def _read_dib(blob: bytes, w: int, h: int) -> Image.Image:
    """Decodifica o DIB (BMP sem file-header) de um .cur/.ico."""
    if len(blob) < 40:
        raise ValueError("DIB truncado")
    hdr_size = struct.unpack("<I", blob[:4])[0]
    dib_w, dib_h = struct.unpack("<ii", blob[4:12])
    bpp = struct.unpack("<H", blob[14:16])[0]
    w = dib_w if w is None else w
    if dib_h > 0:
        h = dib_h // 2
    elif w is None:
        raise ValueError("altura inválida")
    px_off = hdr_size + ((4 * (1 << bpp)) if bpp <= 8 else 0)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask_row = ((w + 31) // 32) * 4
    mask_start = px_off + ((w * ((bpp + 7) // 8) + 3) // 4) * 4 * h
    px = img.load()
    for y in range(h):
        src_y = h - 1 - y
        row_off = px_off + src_y * ((w * ((bpp + 7) // 8) + 3) // 4) * 4
        for x in range(w):
            o = row_off + x * ((bpp + 7) // 8)
            if o + 4 <= len(blob) and bpp == 32:
                b, g, r, a = blob[o], blob[o + 1], blob[o + 2], blob[o + 3]
            elif o + 3 <= len(blob) and bpp == 24:
                b, g, r = blob[o], blob[o + 1], blob[o + 2]
                a = 255
            else:
                b, g, r, a = 0, 0, 0, 255
            if a == 0:
                # consulta a máscara AND: bit 1 = transparente
                mo = mask_start + src_y * mask_row + (x >> 3)
                if mo < len(blob) and (blob[mo] >> (7 - (x & 7))) & 1:
                    a = 0
                else:
                    a = 255
            px[x, y] = (r, g, b, a)
    return img


def read_cur(path) -> tuple[Image.Image, tuple[int, int]]:
    """Lê .cur/.ico retornando (imagem RGBA, hotspot). Pega o maior frame."""
    data = Path(path).read_bytes()
    if len(data) < 22:
        raise ValueError("arquivo de cursor inválido")
    res, typ, count = struct.unpack("<HHH", data[:6])
    if typ not in (1, 2) or count == 0:
        raise ValueError("formato de cursor não reconhecido")
    best = None
    for i in range(count):
        off = 6 + i * 16
        b = data[off:off + 16]
        if len(b) < 16:
            break
        w = b[0] or 256
        h = b[1] or 256
        hx, hy = struct.unpack("<HH", b[4:8])
        size, offset = struct.unpack("<II", b[8:16])
        if best is None or w * h > best[0] * best[1]:
            best = (w, h, hx, hy, size, offset)
    if best is None:
        raise ValueError("cursor vazio")
    w, h, hx, hy, size, offset = best
    blob = data[offset:offset + size]
    if blob[:8] == _PNG_SIG:
        img = Image.open(io.BytesIO(blob)).convert("RGBA")
        if img.size != (w, h) and w and h:
            img = img.resize((w, h), Image.LANCZOS)
    else:
        img = _read_dib(blob, w, h)
    return img, (hx, hy)


def read_cursor_file(path) -> tuple[Image.Image, tuple[int, int]]:
    """Abre qualquer imagem suportada (.cur/.ico/.png/.jpg/.bmp/.gif) → (RGBA, hotspot)."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".cur", ".ico"):
        return read_cur(p)
    img = Image.open(p)
    if getattr(img, "is_animated", False):
        img.seek(0)
    img = img.convert("RGBA")
    return img, (0, 0)
