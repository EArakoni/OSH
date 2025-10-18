#!/usr/bin/env python3
"""
Download LKML archives from lore.kernel.org

Supports both mbox.gz and Atom feed formats.

Usage:
    python download_lkml.py 2024-10-17          # Download mbox
    python download_lkml.py --atom              # Download latest Atom feed
"""

import requests
import sys
import gzip
import shutil
from pathlib import Path

def download_atom_feed(output_file='lkml-new.atom'):
    """
    Download the latest LKML Atom feed
    
    Args:
        output_file: Where to save the feed
    """
    url = "http://lore.kernel.org/lkml/new.atom"
    
    print(f"📥 Downloading latest LKML Atom feed...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def download_lkml_day(date: str):
    """
    Download LKML mbox for a specific day
    
    Args:
        date: Date in format YYYY-MM-DD
    """
    url = f"https://lore.kernel.org/lkml/{date}/mbox.gz"
    output_gz = f"lkml-{date}.mbox.gz"
    output_mbox = f"lkml-{date}.mbox"
    
    print(f"📥 Downloading LKML archive for {date}...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_gz, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded {output_gz}")
        
        print(f"📦 Decompressing...")
        with gzip.open(output_gz, 'rb') as f_in:
            with open(output_mbox, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"✅ Created {output_mbox}")
        
        Path(output_gz).unlink()
        
        return output_mbox
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Archive for {date} might not exist yet")
        print(f"   Try using --atom to download the latest feed instead")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python download_lkml.py YYYY-MM-DD       # Download specific day")
        print("  python download_lkml.py --atom           # Download latest Atom feed")
        print("\nExamples:")
        print("  python download_lkml.py 2024-10-15")
        print("  python download_lkml.py --atom")
        sys.exit(1)
    
    if sys.argv[1] == '--atom':
        download_atom_feed()
    else:
        date = sys.argv[1]
        download_lkml_day(date)
