"""Extract a photo from the .3mf and annotate with dimension lines."""
import zipfile
from PIL import Image, ImageDraw, ImageFont
import io

# Extract a photo from the .3mf
zf = zipfile.ZipFile('Bowl_Stacker_John Lewis bowls.3mf')

# Try to get IMG_4170 (front view of bowls in stacker)
img_data = zf.read('Auxiliaries/Model Pictures/IMG_4170.webp')
img = Image.open(io.BytesIO(img_data)).convert('RGB')
print(f"Image size: {img.size}")

# Save it so we can view it first
img.save('_photo_original.png')
print("Saved _photo_original.png")
