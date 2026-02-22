#!/usr/bin/env python3
import sys
import zlib
import base64
import urllib.request
import os

def generate_png(mmd_file, png_file):
    """Generate PNG from Mermaid file using mermaid.ink API with pako compression"""
    with open(mmd_file, 'r') as f:
        content = f.read()
    
    # Compress using zlib (pako compatible)
    compressed = zlib.compress(content.encode('utf-8'), 9)
    
    # Base64url encode
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')
    
    # Create URL
    url = f"https://mermaid.ink/img/pako:{encoded}"
    
    print(f"Fetching: {mmd_file} -> {png_file}")
    
    try:
        # Download image
        with urllib.request.urlopen(url) as response:
            data = response.read()
            
        # Save to file
        with open(png_file, 'wb') as f:
            f.write(data)
            
        file_size = len(data)
        if file_size < 500:
            print(f"  ⚠️  Warning: File size is only {file_size} bytes - might be error")
            with open(png_file, 'r') as f:
                print(f"  Content: {f.read()}")
            return False
        else:
            print(f"  ✓ Success! ({file_size:,} bytes)")
            return True
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

if __name__ == "__main__":
    mmd_files = [
        "leader-election-sequence.mmd",
        "queue-based-architecture.mmd",
        "decision-tree.mmd",
        "idempotency-pattern.mmd"
    ]
    
    success_count = 0
    for mmd_file in mmd_files:
        png_file = mmd_file.replace('.mmd', '.png')
        if generate_png(mmd_file, png_file):
            success_count += 1
    
    print(f"\n✓ Successfully generated {success_count}/{len(mmd_files)} PNG files")
