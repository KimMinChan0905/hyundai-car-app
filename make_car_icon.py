from PIL import Image, ImageDraw

sizes = [16, 24, 32, 48, 64, 128, 256]
images = []
for size in sizes:
    image = Image.new("RGBA", (size, size), (8, 54, 91, 255))
    draw = ImageDraw.Draw(image)
    s = size / 256
    # Rounded blue app tile and a simple white car silhouette.
    draw.rounded_rectangle((8*s, 8*s, 248*s, 248*s), radius=42*s, fill=(8, 120, 189, 255))
    body = [(38*s, 155*s), (55*s, 116*s), (84*s, 92*s), (171*s, 92*s),
            (204*s, 116*s), (220*s, 155*s), (220*s, 181*s), (38*s, 181*s)]
    draw.polygon(body, fill=(245, 250, 253, 255))
    draw.rounded_rectangle((72*s, 101*s, 171*s, 140*s), radius=10*s, fill=(33, 86, 118, 255))
    draw.polygon([(82*s, 104*s), (111*s, 104*s), (111*s, 137*s), (70*s, 137*s)], fill=(153, 214, 239, 255))
    draw.polygon([(116*s, 104*s), (163*s, 104*s), (185*s, 137*s), (116*s, 137*s)], fill=(153, 214, 239, 255))
    draw.rounded_rectangle((50*s, 145*s, 208*s, 173*s), radius=8*s, fill=(245, 250, 253, 255))
    draw.ellipse((55*s, 160*s, 88*s, 193*s), fill=(21, 42, 58, 255))
    draw.ellipse((170*s, 160*s, 203*s, 193*s), fill=(21, 42, 58, 255))
    draw.ellipse((65*s, 170*s, 78*s, 183*s), fill=(173, 203, 218, 255))
    draw.ellipse((180*s, 170*s, 193*s, 183*s), fill=(173, 203, 218, 255))
    images.append(image)
images[-1].save("car_icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
