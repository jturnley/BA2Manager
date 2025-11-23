from PIL import Image
import os
import sys

def create_icon(source_file, output_file='app.ico'):
    """
    Converts a source image to an .ico file.
    """
    if not os.path.exists(source_file):
        print(f"Error: Source file '{source_file}' not found.")
        print("Please save your image to the project folder with this name.")
        return

    try:
        img = Image.open(source_file)
        # Convert to RGBA to handle transparency if present
        img = img.convert("RGBA")
        
        # Create the icon
        # We'll include multiple sizes for best quality in Windows
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(output_file, format='ICO', sizes=icon_sizes)
        print(f"Success! Created {output_file} from {source_file}")
        
    except Exception as e:
        print(f"Error converting image: {e}")

if __name__ == "__main__":
    # Check for common image formats
    possible_sources = ['source_icon.png', 'source_icon.jpg', 'source_icon.jpeg', 'source_icon.webp']
    
    found = False
    for src in possible_sources:
        if os.path.exists(src):
            create_icon(src)
            found = True
            break
            
    if not found:
        print("No source image found!")
        print("Please save your image as 'source_icon.png' (or .jpg/.webp) in this folder:")
        print(os.getcwd())
