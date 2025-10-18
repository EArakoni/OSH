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
import time
from pathlib import Path

# Headers to avoid 403 Forbidden errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Referer': 'https://lore.kernel.org/lkml/',
}

def download_with_retry(url, max_retries=3, timeout=30):
    """
    Download with retry logic and exponential backoff
    
    Args:
        url: URL to download
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        Response object or None if failed
    """
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}...")
            response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"   ⚠️  403 Forbidden - Server is blocking the request")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                    print(f"   ⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ All retry attempts failed")
                    return None
            elif e.response.status_code == 404:
                print(f"   ❌ 404 Not Found - Archive doesn't exist for this date")
                return None
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Request error: {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                print(f"   ⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                return None
    
    return None

def download_atom_feed(output_file='lkml-new.atom'):
    """
    Download the latest LKML Atom feed
    
    Args:
        output_file: Where to save the feed
    """
    url = "https://lore.kernel.org/lkml/new.atom"  # Changed to https
    
    print(f"📥 Downloading latest LKML Atom feed...")
    print(f"   URL: {url}")
    
    try:
        response = download_with_retry(url)
        if not response:
            return None
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        file_size = Path(output_file).stat().st_size
        print(f"✅ Downloaded {output_file} ({file_size:,} bytes)")
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
        response = download_with_retry(url)
        if not response:
            print(f"\n💡 Troubleshooting tips:")
            print(f"   1. Check if the date is valid and not in the future")
            print(f"   2. Try a more recent date (e.g., yesterday or today)")
            print(f"   3. Use --atom to download the latest feed instead")
            print(f"   4. Visit https://lore.kernel.org/lkml/{date}/ in a browser to verify")
            return None
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_gz, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r   Progress: {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='')
        
        print()  # New line after progress
        print(f"✅ Downloaded {output_gz}")
        
        # Check if the file is actually gzipped or if we got an HTML error page
        is_gzip = False
        error_content = None
        
        with open(output_gz, 'rb') as f:
            magic = f.read(2)
            
            # Gzip files start with 0x1f 0x8b
            if magic != b'\x1f\x8b':
                # Not a gzip file - probably an HTML error page
                f.seek(0)
                error_content = f.read(1000).decode('utf-8', errors='ignore')
            else:
                is_gzip = True
        
        if not is_gzip:
            print(f"\n❌ Downloaded file is not a valid gzip archive")
            
            # Check for specific error patterns
            if "bot" in error_content.lower() or "captcha" in error_content.lower():
                print(f"   🤖 Bot detection triggered!")
                print(f"   The server is using anti-bot protection (likely CloudFlare).")
                print(f"\n   💡 Solutions:")
                print(f"   1. Try downloading individual mailing list archives instead:")
                print(f"      https://lore.kernel.org/batman/ (for batman list)")
                print(f"   2. Use the --atom option for latest emails")
                print(f"   3. Access through a browser first to solve CAPTCHA")
                print(f"   4. Use alternative archives like marc.info")
            else:
                print(f"   Server returned: {error_content[:200]}...")
                print(f"\n   This archive might not be available.")
            
            # Close file handle before deleting (Windows fix)
            try:
                Path(output_gz).unlink()
            except PermissionError:
                print(f"   ⚠️  Could not delete temporary file {output_gz}")
                print(f"      You can manually delete it later")
            
            return None
        
        print(f"📦 Decompressing...")
        try:
            with gzip.open(output_gz, 'rb') as f_in:
                with open(output_mbox, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except gzip.BadGzipFile as e:
            print(f"❌ Error: {e}")
            print(f"   The downloaded file is not a valid gzip archive")
            Path(output_gz).unlink()
            return None
        
        mbox_size = Path(output_mbox).stat().st_size
        print(f"✅ Created {output_mbox} ({mbox_size:,} bytes)")
        
        # Clean up compressed file
        Path(output_gz).unlink()
        print(f"🗑️  Removed {output_gz}")
        
        return output_mbox
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Archive for {date} might not exist")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python download_lkml.py YYYY-MM-DD       # Download specific day from main LKML")
        print("  python download_lkml.py --atom           # Download latest Atom feed")
        print("  python download_lkml.py --list <name>    # Download from specific mailing list")
        print("\nExamples:")
        print("  python download_lkml.py 2024-10-17")
        print("  python download_lkml.py --atom")
        print("  python download_lkml.py --list batman")
        print("\n⚠️  Note: Due to bot protection, you may need to:")
        print("  - Use a browser to access lore.kernel.org first")
        print("  - Try the --atom option for latest emails")
        print("  - Use alternative sources like marc.info")
        sys.exit(1)
    
    if sys.argv[1] == '--atom':
        download_atom_feed()
    elif sys.argv[1] == '--list' and len(sys.argv) > 2:
        list_name = sys.argv[2]
        url = f"https://lore.kernel.org/{list_name}/new.atom"
        output_file = f"{list_name}-new.atom"
        print(f"📥 Downloading latest from {list_name} mailing list...")
        print(f"   URL: {url}")
        try:
            response = download_with_retry(url)
            if response:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        date = sys.argv[1]
        download_lkml_day(date)