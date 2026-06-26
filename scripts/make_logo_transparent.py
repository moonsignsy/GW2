"""Remove background, defringe edges, trim and export transparent logo."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "logo.png"
OUT = ROOT / "assets" / "logo.png"
FAVICON = ROOT / "assets" / "favicon.png"


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def flood_remove_background(img: Image.Image, tolerance: int = 28) -> Image.Image:
    """Flood-fill from image edges to remove solid/near-black background."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()

    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not visited[y][x]:
            r, g, b, a = pixels[x, y]
            if a == 0 or (r < 40 and g < 40 and b < 40):
                visited[y][x] = True
                stack.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    while stack:
        x, y = stack.pop()
        r, g, b, _ = pixels[x, y]
        bg = (r, g, b)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                nr, ng, nb, na = pixels[nx, ny]
                if na == 0:
                    visited[ny][nx] = True
                    stack.append((nx, ny))
                elif nr < 40 and ng < 40 and nb < 40:
                    visited[ny][nx] = True
                    stack.append((nx, ny))
                elif color_distance(bg, (nr, ng, nb)) <= tolerance and max(nr, ng, nb) < 80:
                    visited[ny][nx] = True
                    stack.append((nx, ny))

    for y in range(h):
        for x in range(w):
            if visited[y][x]:
                pixels[x, y] = (0, 0, 0, 0)

    return rgba


def defringe(img: Image.Image) -> Image.Image:
    """Reduce dark halos on anti-aliased edges."""
    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 45 and a < 255:
                px[x, y] = (r, g, b, 0)
            elif a < 255 and lum < 90:
                factor = lum / 90
                px[x, y] = (r, g, b, int(a * factor))

    return rgba


def trim_with_padding(img: Image.Image, padding: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def make_favicon(logo: Image.Image) -> Image.Image:
    """Crop icon portion and resize for browser tab."""
    w, h = logo.size
    icon = logo.crop((0, 0, int(w * 0.28), h))
    icon = trim_with_padding(icon, padding=4)
    size = 64
    icon.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - icon.width) // 2
    oy = (size - icon.height) // 2
    canvas.paste(icon, (ox, oy), icon)
    return canvas


def main() -> None:
    img = Image.open(SRC)
    img = flood_remove_background(img)
    img = defringe(img)
    img = trim_with_padding(img, padding=10)
    img.save(OUT, format="PNG", optimize=True)

    favicon = make_favicon(img)
    favicon.save(FAVICON, format="PNG", optimize=True)

    print(f"Saved transparent logo: {OUT} ({img.size[0]}x{img.size[1]})")
    print(f"Saved favicon: {FAVICON}")


if __name__ == "__main__":
    main()
