import pyperclip
import time
import subprocess
import re
import json
import os
import shutil
import string

def is_url(text):
    return re.match(r'^https?://[^\s]+$', text.strip()) is not None

def extract_urls(text):
    # Find all http/https URLs in the clipboard text
    return re.findall(r'https?://[^\s<>"\'()]+', text)

def sanitize_filename(name):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return ''.join(c for c in name if c in valid_chars).strip()[:100]

def run_readability_scrape(url):
    readability_cmd = shutil.which("readability-scrape")
    if not readability_cmd:
        print("Error: 'readability-scrape' not found in PATH.")
        return

    print(f"Scraping: {url}")
    result = subprocess.run(
        [readability_cmd, '--json', url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )

    stdout_decoded = result.stdout.decode('utf-8', errors='replace')

    if result.returncode != 0:
        stderr_decoded = result.stderr.decode('utf-8', errors='replace')
        print(f"Error running readability-scrape:\n{stderr_decoded}")
        return

    try:
        data = json.loads(stdout_decoded)
        title = data.get("title") or "article"
        html_content = data.get("content", "")
        safe_name = sanitize_filename(title) or "article"
        filename = f"{safe_name}.html"

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: system-ui, sans-serif;
            background: #f7f7f7;
            color: #222;
            padding: 2rem;
            max-width: 800px;
            margin: auto;
            line-height: 1.6;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        table th, table td {{
            border: 1px solid #ccc;
            padding: 0.5em;
        }}
        table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        pre {{
            background: #eee;
            padding: 1em;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"Saved: {filename}")
    except json.JSONDecodeError:
        print("Failed to parse JSON from readability-scrape.")
        print(stdout_decoded)

def main():
    print("Monitoring clipboard for URLs...")
    last_clip = ""
    seen_urls = set()
    url_queue = []

    while True:
        try:
            clip = pyperclip.paste().strip()
            if clip != last_clip:
                last_clip = clip
                urls = extract_urls(clip)
                new_urls = [u for u in urls if u not in seen_urls]
                if new_urls:
                    print(f"Found {len(new_urls)} new URL(s):")
                    for url in new_urls:
                        print(f" - {url}")
                        seen_urls.add(url)
                        url_queue.append(url)

            # Process one URL per loop
            if url_queue:
                next_url = url_queue.pop(0)
                run_readability_scrape(next_url)

        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

        time.sleep(1)

if __name__ == '__main__':
    main()
