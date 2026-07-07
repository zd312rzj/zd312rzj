"""
生成原创像素水龟 PNG。
64x64 网格,每个像素都精确控制,no antialiasing。
"""

import os
from PIL import Image, ImageDraw

W = 64
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'assets')
os.makedirs(OUT, exist_ok=True)

C = {
    'outline':       (12, 28, 48, 255),
    'outline_soft':  (28, 56, 82, 255),
    'blue_dark':     (38, 88, 138, 255),
    'blue_mid':      (68, 138, 196, 255),
    'blue_light':    (118, 190, 226, 255),
    'blue_hilite':   (195, 235, 250, 255),
    'cream_dark':    (181, 132, 92, 255),
    'cream_mid':     (232, 181, 126, 255),
    'cream_light':   (255, 220, 164, 255),
    'shell_dark':    (88, 55, 42, 255),
    'shell_mid':     (142, 82, 55, 255),
    'shell_light':   (190, 112, 70, 255),
    'rim':           (231, 238, 220, 255),
    'metal_dark':    (48, 58, 70, 255),
    'metal_mid':     (118, 132, 145, 255),
    'metal_light':   (190, 204, 213, 255),
    'white':         (255, 255, 255, 255),
    'black':         (14, 20, 28, 255),
    'mouth':         (95, 34, 48, 255),
}


def make_canvas():
    return Image.new('RGBA', (W, W), (0, 0, 0, 0))


def draw():
    img = make_canvas()
    d = ImageDraw.Draw(img)

    def ellipse(box, color):
        d.ellipse(box, fill=color)

    def rect(box, color):
        d.rectangle(box, fill=color)

    def poly(points, color):
        d.polygon(points, fill=color)

    def line(points, color, width=1):
        d.line(points, fill=color, width=width)

    def px(x, y, color):
        if 0 <= x < W and 0 <= y < W:
            img.putpixel((x, y), color)

    ellipse((14, 55, 50, 60), (20, 72, 105, 85))

    poly([(12, 25), (24, 18), (40, 18), (52, 25), (56, 41), (48, 54), (16, 54), (8, 41)], C['outline'])
    poly([(15, 26), (25, 21), (39, 21), (49, 26), (52, 40), (45, 50), (19, 50), (12, 40)], C['shell_dark'])
    poly([(17, 27), (26, 23), (38, 23), (47, 27), (49, 39), (43, 47), (21, 47), (15, 39)], C['shell_mid'])
    poly([(22, 26), (30, 23), (38, 26), (42, 36), (38, 44), (26, 44), (22, 36)], C['shell_light'])
    line([(23, 35), (41, 35)], C['shell_dark'], 2)
    line([(31, 24), (31, 44)], C['shell_dark'], 2)
    line([(19, 29), (25, 35), (19, 42)], C['shell_dark'], 2)
    line([(45, 29), (39, 35), (45, 42)], C['shell_dark'], 2)
    line([(15, 26), (25, 21), (39, 21), (49, 26)], C['rim'], 3)

    poly([(14, 24), (10, 10), (20, 7), (27, 22)], C['outline'])
    poly([(50, 24), (54, 10), (44, 7), (37, 22)], C['outline'])
    poly([(16, 22), (12, 11), (20, 9), (24, 22)], C['metal_dark'])
    poly([(48, 22), (52, 11), (44, 9), (40, 22)], C['metal_dark'])
    line([(15, 13), (20, 22)], C['metal_mid'], 3)
    line([(49, 13), (44, 22)], C['metal_mid'], 3)
    ellipse((8, 5, 22, 17), C['outline'])
    ellipse((42, 5, 56, 17), C['outline'])
    ellipse((10, 7, 20, 15), C['metal_mid'])
    ellipse((44, 7, 54, 15), C['metal_mid'])
    rect((12, 7, 17, 9), C['metal_light'])
    rect((46, 7, 51, 9), C['metal_light'])
    ellipse((13, 9, 18, 14), C['black'])
    ellipse((46, 9, 51, 14), C['black'])
    for x, y in [(6, 3), (5, 8), (7, 14), (58, 3), (59, 8), (57, 14)]:
        rect((x, y, x + 1, y + 1), C['blue_hilite'])

    ellipse((17, 10, 47, 34), C['outline'])
    ellipse((19, 11, 45, 32), C['blue_dark'])
    ellipse((21, 12, 43, 30), C['blue_mid'])
    ellipse((23, 13, 33, 21), C['blue_light'])
    rect((25, 13, 29, 15), C['blue_hilite'])
    poly([(20, 12), (17, 7), (25, 10)], C['outline'])
    poly([(44, 12), (47, 7), (39, 10)], C['outline'])
    poly([(21, 12), (19, 9), (24, 11)], C['blue_dark'])
    poly([(43, 12), (45, 9), (40, 11)], C['blue_dark'])

    ellipse((17, 31, 31, 49), C['outline'])
    ellipse((33, 31, 47, 49), C['outline'])
    ellipse((10, 35, 24, 48), C['outline'])
    ellipse((40, 35, 54, 48), C['outline'])
    ellipse((14, 36, 23, 46), C['blue_dark'])
    ellipse((41, 36, 50, 46), C['blue_dark'])
    ellipse((18, 32, 46, 55), C['outline'])
    ellipse((20, 32, 44, 54), C['blue_dark'])
    ellipse((23, 33, 41, 54), C['cream_dark'])
    ellipse((24, 32, 40, 52), C['cream_mid'])
    ellipse((26, 33, 38, 49), C['cream_light'])
    line([(25, 39), (39, 39)], C['cream_dark'], 2)
    line([(26, 45), (38, 45)], C['cream_dark'], 2)
    line([(32, 33), (32, 52)], C['cream_dark'], 1)

    ellipse((17, 49, 30, 62), C['outline'])
    ellipse((34, 49, 47, 62), C['outline'])
    ellipse((19, 50, 29, 59), C['blue_dark'])
    ellipse((35, 50, 45, 59), C['blue_dark'])
    for x in [17, 21, 26, 36, 41, 46]:
        ellipse((x, 58, x + 4, 62), C['cream_light'])

    ellipse((22, 19, 30, 28), C['white'])
    ellipse((34, 19, 42, 28), C['white'])
    ellipse((25, 21, 29, 26), C['black'])
    ellipse((35, 21, 39, 26), C['black'])
    rect((26, 21, 27, 22), C['white'])
    rect((36, 21, 37, 22), C['white'])
    line([(28, 31), (31, 33), (36, 31)], C['mouth'], 2)
    rect((32, 33, 34, 35), (244, 95, 116, 255))
    rect((19, 29, 22, 31), (233, 126, 156, 255))
    rect((42, 29, 45, 31), (233, 126, 156, 255))

    line([(19, 14), (24, 12), (29, 12)], C['blue_hilite'], 1)
    line([(21, 34), (15, 38)], C['blue_light'], 1)
    line([(43, 34), (49, 38)], C['blue_light'], 1)

    return img


def main():
    img = draw()
    out_path = os.path.join(OUT, 'turtle.png')
    img.save(out_path, format='PNG')
    print(f'wrote {out_path}')

    preview = img.resize((256, 256), Image.NEAREST)
    preview_path = os.path.join(OUT, 'turtle-preview.png')
    preview.save(preview_path, format='PNG')
    print(f'wrote {preview_path}')


if __name__ == '__main__':
    main()
