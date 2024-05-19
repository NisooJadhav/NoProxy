import os
import cv2

# Set the directory containing the images you want to resize
image_dir = "Z:/NoProxy/Images"  # Replace this with your own directory

# Set the desired output dimensions
output_width = 216
output_height = 216

# Loop through all files in the directory
for filename in os.listdir(image_dir):
    # Check if the file is an image
    if filename.endswith((".jpg", ".png", ".jpeg")):
        # Construct the full file path
        file_path = os.path.join(image_dir, filename)
        
        # Read the image
        img = cv2.imread(file_path)
        
        # Resize the image
        resized_img = cv2.resize(img, (output_width, output_height), interpolation=cv2.INTER_AREA)
        
        # Save the resized image with the same name in the same directory
        output_path = os.path.join(image_dir, filename)
        cv2.imwrite(output_path, resized_img)
        
        print(f"Resized {filename} to {output_width}x{output_height} pixels.")

print("Image resizing completed.")