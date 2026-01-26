import os
import re
import time
import requests
from PIL import Image
from io import BytesIO

# Configuration
HTML_FILE = 'index.html'
IMG_DIR = 'img'
MAX_DIMENSION = 800
QUALITY = 80
DELAY_SECONDS = 45

def extract_styles(html_path):
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        match = re.search(r'const styles = \[(.*?)\];', content, re.DOTALL)
        if not match:
            print("Error: Could not find 'const styles' array in HTML.")
            return []
        
        array_content = match.group(1)
        styles = []
        object_pattern = re.compile(r'\{\s*id:\s*"(.*?)".*?prompt:\s*"(.*?)".*?\}', re.DOTALL)
        
        for obj_match in object_pattern.finditer(array_content):
            styles.append({'id': obj_match.group(1), 'prompt': obj_match.group(2)})
            
        return styles
    except Exception as e:
        print(f"Error reading HTML: {e}")
        return []

def generate_and_save_optimized(prompt, output_path):
    try:
        print(f"  Requesting generation for prompt: {prompt[:30]}...")
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        response = requests.get(url, timeout=120)
        
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            with Image.open(image_data) as img:
                 if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                 # Resize logic
                 width, height = img.size
                 if width > MAX_DIMENSION or height > MAX_DIMENSION:
                    ratio = min(MAX_DIMENSION / width, MAX_DIMENSION / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    print(f"  Resized from {width}x{height} to {new_size}")
                 
                 # Save optimized
                 img.save(output_path, 'JPEG', optimize=True, quality=QUALITY)
                 size_kb = os.path.getsize(output_path) / 1024
                 print(f"  Saved to {output_path} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"  FAILED to generate: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  Exception during generation: {e}")
        return False

def countdown(seconds):
    print(f"Waiting {seconds} seconds...", end='', flush=True)
    for i in range(seconds, 0, -1):
        if i % 5 == 0:
             print(f" {i}...", end='', flush=True)
        time.sleep(1)
    print(" Ready.")

def main():
    if not os.path.exists(IMG_DIR):
        print(f"Directory {IMG_DIR} does not exist. Creating...")
        os.makedirs(IMG_DIR)

    styles = extract_styles(HTML_FILE)
    print(f"Found {len(styles)} styles defined in HTML.")
    
    missing_count = 0
    generated_count = 0
    
    # Identify missing first to know total
    missing_styles = []
    for style in styles:
        img_path = os.path.join(IMG_DIR, f"{style['id']}.jpg")
        if not os.path.exists(img_path):
            missing_styles.append(style)

    print(f"Found {len(missing_styles)} missing images to generate.")
    print("-" * 40)

    for i, item in enumerate(missing_styles):
        img_path = os.path.join(IMG_DIR, f"{item['id']}.jpg")
        
        print(f"[{i+1}/{len(missing_styles)}] Processing {item['id']}...")
        
        success = generate_and_save_optimized(item['prompt'], img_path)
        
        if success:
            generated_count += 1
        
        # Determine if we need to sleep (if not the very last item)
        if i < len(missing_styles) - 1:
            countdown(DELAY_SECONDS)
        
    print("-" * 40)
    print(f"Process complete. Generated {generated_count} of {len(missing_styles)} missing images.")

if __name__ == "__main__":
    main()
