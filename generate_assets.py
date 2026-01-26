import re
import os
import time
import requests
import sys

# Configuration
HTML_FILE = 'index.html'
IMG_DIR = 'img'
DELAY_SECONDS = 2  # Rate limiting

def extract_styles(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Locate the styles array
    # Looking for: const styles = [ ... ];
    # We will use a regex to find all objects inside the array
    
    styles = []
    
    # Regex to match object literals roughly: { id: "...", ... prompt: "...", ... }
    # We'll iterate over the content to find the 'styles' block first if possible, 
    # but a global search for the pattern might be enough if unique.
    
    # Let's find the content between "const styles = [" and "];"
    match = re.search(r'const styles = \[(.*?)\];', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const styles' array in HTML.")
        return []
    
    array_content = match.group(1)
    
    # Now extract each object. Assuming they are well enclosed in braces.
    # Pattern: { id: "value", ... }
    # We specifically need 'id' and 'prompt'.
    
    # This regex looks for:
    # id: "MATCH",
    # ...
    # prompt: "MATCH"
    
    # We iterate over 'matches' of objects
    object_pattern = re.compile(r'\{\s*id:\s*"(.*?)".*?prompt:\s*"(.*?)".*?\}', re.DOTALL)
    
    for obj_match in object_pattern.finditer(array_content):
        style_id = obj_match.group(1)
        prompt = obj_match.group(2)
        styles.append({'id': style_id, 'prompt': prompt})
        
    return styles

def generate_image(prompt, output_path):
    # Using Pollinations.ai (no API key required, good for demos)
    # URL encoded prompt
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Failed to generate: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"Exception during generation: {e}")
        return False

def main():
    print(f"Scanning {HTML_FILE}...")
    if not os.path.exists(HTML_FILE):
        print(f"File {HTML_FILE} not found.")
        return

    styles = extract_styles(HTML_FILE)
    print(f"Found {len(styles)} styles defined.")
    
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
        print(f"Created directory {IMG_DIR}")
        
    missing = []
    for style in styles:
        img_path = os.path.join(IMG_DIR, f"{style['id']}.jpg")
        if not os.path.exists(img_path):
            missing.append(style)
            
    if not missing:
        print("All images already exist! Nothing to do.")
        return

    print(f"Found {len(missing)} missing images.")
    print("Example missing:", missing[0]['id'])
    
    # Confirmation step
    print(f"Ready to generate {len(missing)} images.")
    # In an automated environment, we might checking for a flag, 
    # but the requirement was 'confirmation step'.
    # We will assume if running interactively we ask.
    
    confirm = input("Do you want to proceed with generation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return

    print("Starting generation...")
    for i, item in enumerate(missing):
        print(f"[{i+1}/{len(missing)}] Generating {item['id']}...")
        success = generate_image(item['prompt'], os.path.join(IMG_DIR, f"{item['id']}.jpg"))
        
        if success:
            print(f"  -> Saved to img/{item['id']}.jpg")
        else:
            print(f"  -> FAILED")
            
        if i < len(missing) - 1:
            time.sleep(DELAY_SECONDS)

    print("Done!")

if __name__ == "__main__":
    main()
