"""
生成应用图标。
用 Pillow + Bezier 离散采样画出水滴形态,渐变填充,导出多尺寸 .ico。
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

W = 1024  # 大画布,最后下采样

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
os.makedirs(OUT_DIR, exist_ok=True)


def cubic(p0, p1, p2, p3, n=120):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u ** 2 * t * p1[0] + 3 * u * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u ** 2 * t * p1[1] + 3 * u * t ** 2 * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def droplet_path(W):
    top = (W * 0.5, W * 0.10)
    bottom = (W * 0.5, W * 0.93)

    right_c1 = (W * 0.92, W * 0.32)
    right_c2 = (W * 0.92, W * 0.78)
    left_c1 = (W * 0.08, W * 0.32)
    left_c2 = (W * 0.08, W * 0.78)

    right = cubic(top, right_c1, right_c2, bottom)
    left = cubic(top, left_c1, left_c2, bottom)
    left = left[::-1]

    return right + left[1:-1]


def vertical_gradient(size, color_top, color_bottom):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    top_arr = [color_top[i] for i in range(4)]
    bot_arr = [color_bottom[i] for i in range(4)]
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(top_arr[i] * (1 - t) + bot_arr[i] * t) for i in range(4))
        for x in range(size):
            px[x, y] = c
    return img


def build_icon():
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).polygon(droplet_path(W), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.2))

    gradient = vertical_gradient(W, (79, 183, 224, 255), (95, 217, 203, 255))

    base = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    base.paste(gradient, (0, 0), mask=mask)

    hi = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    hi_draw = ImageDraw.Draw(hi)
    hi_draw.ellipse(
        [int(W * 0.30), int(W * 0.24), int(W * 0.50), int(W * 0.52)],
        fill=(255, 255, 255, 95)
    )
    hi = hi.filter(ImageFilter.GaussianBlur(radius=W / 60))
    base.alpha_composite(hi)

    glow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.polygon(droplet_path(W), fill=(79, 183, 224, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=W / 20))

    canvas = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(base)

    return canvas


def main():
    big = build_icon()

    master = big.resize((256, 256), Image.LANCZOS)
    sizes_ico = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    ico_path = os.path.join(OUT_DIR, 'icon.ico')
    master.save(ico_path, format='ICO', sizes=sizes_ico)
    print(f'wrote {ico_path}')

    png_path = os.path.join(OUT_DIR, 'icon.png')
    big.resize((512, 512), Image.LANCZOS).save(png_path, format='PNG')
    print(f'wrote {png_path}')


if __name__ == '__main__':
    main()
