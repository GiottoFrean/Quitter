import os
from PIL import Image

# Create a new folder to store the compressed images
if not os.path.exists('dash_app/static/images_small'):
    os.mkdir('dash_app/static/images_small')

for filename in os.listdir('dash_app/static/images'):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        image = Image.open(os.path.join('dash_app/static/images', filename))
        width, height = image.size
        new_width = 300
        new_height = int((new_width / width) * height)
        resized_image = image.resize((new_width, new_height))
        resized_image.save(os.path.join('dash_app/static/images_small', filename))
        image.close()
