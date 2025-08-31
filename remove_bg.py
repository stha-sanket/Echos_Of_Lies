from rembg import remove
from PIL import Image
import os

def remove_background(input_path, output_path):
    """
    Removes the background from an image and saves the result.

    Args:
        input_path (str): The path to the input image file.
        output_path (str): The path where the output image will be saved.
    """
    try:
        # Open the input image
        input_image = Image.open(input_path)

        # Remove the background
        output_image = remove(input_image)

        # Save the output image
        output_image.save(output_path)
        print(f"Background removed successfully! Output saved to: {output_path}")
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'remove_bg')
    output_dir = os.path.join(script_dir, 'remove_bg_output')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_image_path = os.path.join(input_dir, filename)
            output_image_path = os.path.join(output_dir, filename)
            remove_background(input_image_path, output_image_path)