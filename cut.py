import os
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
from tqdm.auto import tqdm

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def slice_part(images, folder):
    print(f"cropping {folder}...")
    with tqdm(total=16*len(images)) as pbar:
        for page, image in enumerate(images):
            left, right = 438/2, 4202/2
            if folder == 'scientists' and page == 0:
                top, bottom = 439/2, 6086/2
            else:
                top, bottom = 232/2, 5880/2
            
            sx, sy = (right-left)/4, (bottom-top)/4

            for x in range(4):
                for y in range(4):
                    im = image.crop((
                        int(left + x*sx + 1),
                        int(top + y*sy + 1),
                        int(left + (x+1)*sx - 1),
                        int(top + (y+1)*sy - 1),
                    ))
                    n = page*16+y*4+x
                    add_corners(im, 40).save(f"tabletopia/{folder}/{n}.png")
                    pbar.update(1)

print('reading pdf...')
images = convert_from_path('pnp.pdf', dpi=300)

print('saving pages...')
for i, image in tqdm(enumerate(images), total=len(images)):
    image.save(f"tabletopia/pages/{i}.png")

slice_part(images[:8], 'scientists')
slice_part(images[8:24], 'inventions')

os.rename('tabletopia/scientists/126.png', 'tabletopia/inventions/bg.png')
os.rename('tabletopia/scientists/127.png', 'tabletopia/scientists/bg.png')