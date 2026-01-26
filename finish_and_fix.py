import os
import re
import time
import requests
from PIL import Image
from io import BytesIO

# Configuration
HTML_FILE = 'index.html'
IMG_DIR = 'img'
MAX_SIZE_KB = 300
MAX_DIMENSION = 800
QUALITY = 80
DELAY_SECONDS = 12

def extract_styles(html_path):
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

def optimize_image(img_path):
    try:
        size_kb = os.path.getsize(img_path) / 1024
        if size_kb <= MAX_SIZE_KB:
            return False # No optimization needed based on size check

        print(f"  Optimizing {os.path.basename(img_path)} ({size_kb:.1f} KB)...")
        
        with Image.open(img_path) as img:
            # Convert to RGB (in case of RGBA from verify source, though JPEGs are usually RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize if needed
            width, height = img.size
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                ratio = min(MAX_DIMENSION / width, MAX_DIMENSION / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            # Save with optimization
            img.save(img_path, 'JPEG', optimize=True, quality=QUALITY)
            
        new_size_kb = os.path.getsize(img_path) / 1024
        print(f"  -> Reduced to {new_size_kb:.1f} KB")
        return True
            
    except Exception as e:
        print(f"  Error optimizing {img_path}: {e}")
        return False

def generate_and_optimize(prompt, output_path):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            with Image.open(image_data) as img:
                 if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                 width, height = img.size
                 if width > MAX_DIMENSION or height > MAX_DIMENSION:
                    ratio = min(MAX_DIMENSION / width, MAX_DIMENSION / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                 
                 img.save(output_path, 'JPEG', optimize=True, quality=QUALITY)
            return True
        else:
            print(f"Failed to generate: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception during generation: {e}")
        return False

def main():
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    # FASE 1: REPARACIÓN
    print("=== PHASE 1: REPAIR ===")
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Scanning {len(files)} files for size > {MAX_SIZE_KB}KB...")
    
    optimized_count = 0
    for filename in files:
        file_path = os.path.join(IMG_DIR, filename)
        if optimize_image(file_path):
            optimized_count += 1
            
    print(f"Phase 1 complete. Optimized {optimized_count} images.")
    print("-" * 30)

    # FASE 2: COMPLETAR
    print("=== PHASE 2: COMPLETE ===")
    styles = extract_styles(HTML_FILE)
    print(f"Found {len(styles)} styles defined in HTML.")
    
    missing = []
    for style in styles:
        img_path = os.path.join(IMG_DIR, f"{style['id']}.jpg")
        if not os.path.exists(img_path):
            missing.append(style)
            
    if not missing:
        print("All images exist. Catalog complete.")
        return

    print(f"Found {len(missing)} missing images. Generating...")
    
    for i, item in enumerate(missing):
        print(f"[{i+1}/{len(missing)}] Generating {item['id']}...")
        success = generate_and_optimize(item['prompt'], os.path.join(IMG_DIR, f"{item['id']}.jpg"))
        
        if success:
            print(f"  -> Saved and optimized.")
        else:
            print(f"  -> FAILED")
            
        if i < len(missing) - 1:
            print(f"Waiting {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)

    print("Phase 2 complete.")

if __name__ == "__main__":
    main()
