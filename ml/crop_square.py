import os
import cv2
import argparse

def crop_to_square(image_path, output_path):
    """
    Crops an image to a square by keeping the top and left side and saves the cropped image.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read image: {image_path}")
        return

    height, width, _ = img.shape
    crop_size = min(height, width)
    cropped_img = img[0:crop_size, 0:crop_size]
    cv2.imwrite(output_path, cropped_img)

def process_folder(input_folder, output_folder):
    """
    Processes all images in the input folder by cropping them to a square
    and saving them to the output folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            crop_to_square(input_path, output_path)
            print(f"Cropped and saved: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Crop images in a folder to squares and save to a new folder.")
    parser.add_argument("input_folder", type=str, help="Path to the folder containing input images.")
    parser.add_argument("output_folder", type=str, help="Path to the folder where cropped images will be saved.")

    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder

    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return

    process_folder(input_folder, output_folder)
    print("All images have been processed and saved.")

if __name__ == "__main__":
    main()