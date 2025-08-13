import re
import fitz
import pytesseract
from PIL import Image, ImageEnhance
import os
import time
import io
import streamlit as st

# Set tesseract path directly in your script
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Linux/macOS

def extract_key_value_pairs(full_text):
    
    processed_text = full_text.replace('Photo', '').replace('Available', '').strip()
    result = {}
    for row in processed_text.split("\n"):
        if "Father's Name" in row or "Father Name" in row or "Fathers Name" in row:
            father = row.split(":")[-1].strip()
            result["Father's Name"] = father
        elif "Husband's Name" in row or "Husband Name" in row or "Husbands Name" in row:
            husband = row.split(":")[-1].strip()
            result["Husband's Name"] = husband
        elif "Mother's Name" in row or "Mother Name" in row or "Mothers Name" in row:
            mother = row.split(":")[-1].strip()
            result["Mother's Name"] = mother
        elif "Name" in row and "Husband's Name" not in row and "Name" not in result:
            name = row.split(":")[-1].strip()
            result["Name"] = name
        elif "House Number" in row:
            house_number = row.split(":")[-1].strip()
            result["House Number"] = house_number if house_number else None
        elif "Age" in row and "Gender" in row:
            age = re.findall(r"\d+", row)
            result["Age"] = age[0] if age else None
            
            gender ='Male' if 'Male' in row.split("Gender")[-1].strip() else 'Female'
            result["Gender"] = gender
        elif "Age" in row:
            age = re.findall(r"\d+", row)
            # age = [int(s) for s in row.split() if s.isdigit()]
            result["Age"] = age
        elif "Gender" in row:
            gender ='Male' if 'Male' in row.split("Gender")[-1].strip() else 'Female'
            result["Gender"] = gender
    return result
   

def extract_block(image):

    crop_box = (400, 0, 566, 50)  # Example coordinates; adjust based on your image
    number_image = image.crop(crop_box)

    number_image = number_image.convert('L')

    number_text = pytesseract.image_to_string(
        number_image,
        config='--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' )

    image = image.convert('L')

    full_text = pytesseract.image_to_string(image, config='--psm 6 --oem 3').strip()


    result = extract_key_value_pairs(full_text)
    result["id"] = number_text
    result['text'] = full_text  

    
    return result


def crop_image_grid(image, output_dir="cropped_images", rows=5, cols=3, 
                   crop_area=None):
  
    voter_list =[]
    
    # Open the image
    img = image
    

    # First, crop to working area if specified
    if crop_area:
        left, top, right, bottom = crop_area
        working_img = img.crop((left, top, right, bottom))
        
    else:
        working_img = img
        
    
    # Get working image dimensions
    work_width, work_height = working_img.size
    
    
    # Calculate the size of each rectangle
    rect_width = work_width // cols
    rect_height = work_height // rows
    
    
    # Crop the working image into rectangles
    for row in range(rows):
        for col in range(cols):
            # Calculate coordinates for the rectangle within working image
            left = col * rect_width
            top = row * rect_height
            right = left + rect_width
            bottom = top + rect_height
            
            # Crop the rectangle from working image
            cropped_img = working_img.crop((left, top, right, bottom))
            enhancer = ImageEnhance.Contrast(cropped_img)
            enhanced_img = enhancer.enhance(3.0)
            result = extract_block(enhanced_img)
            # if result is None:
            #     return None # Skip if no number was extracted
            if result['id']:
                voter_list.append(result)
            # print(result['id'])
    
    # print(f"\nAll {rows * cols} images saved to '{output_dir}' directory")

    return voter_list


def preview_crop_area(image_path, crop_area):
    """
    Helper function to preview the working area before cropping
    Saves a preview image showing what will be used as working area
    """
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    print(f"Original image size: {img_width} x {img_height}")

    if crop_area:
        left, top, right, bottom = crop_area
        preview_img = img.crop((left, top, right, bottom))
        preview_img.save("preview_working_area.png")
        print(f"Preview saved as 'preview_working_area.png'")
        print(f"Working area dimensions: {right-left} x {bottom-top}")
    else:
        print("No crop area specified - will use entire image")



def extract_pdf_blocks(pdf_path):
    strat_time = time.time()
    doc = fitz.open(pdf_path)
    voters_data = []
    for page_num in range(2,len(doc)-2):
        page = doc[page_num]
        
        # High resolution conversion
        mat = fitz.Matrix(3, 3)  # 3x scaling for better OCR
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        voters = crop_image_grid(img, rows=10, cols=3, crop_area=(40, 80, 1740, 2455))
        
        if not voters:
            print(f"No voters found on page {page_num + 1}, skipping...")
            continue
        # Append results to the list
        voters_data.extend(voters)
        st.write(f"Processed page {page_num + 1}/{len(doc)-2}: {len(voters)} records extracted")
        

        
    doc.close()

    end_time = time.time()
    st.write(f"Extracted {len(voters_data)} voter records in {end_time - strat_time:.2f} seconds")
    return voters_data