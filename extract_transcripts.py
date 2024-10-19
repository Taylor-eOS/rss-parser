import os
import requests
import xml.etree.ElementTree as ET
import json

with open('settings.json', 'r') as f:
    settings = json.load(f)

RSS_FEED_URL = settings['rss_feed_url']
OUTPUT_DIR = 'transcripts'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

def fetch_transcript(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch transcript from {url}: {e}")
        return None

def main():
    try:
        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()
        rss_content = response.content
    except requests.RequestException as e:
        print(f"Failed to fetch RSS feed: {e}")
        return

    try:
        root = ET.fromstring(rss_content)
    except ET.ParseError as e:
        print(f"Failed to parse RSS feed XML: {e}")
        return

    for item in root.findall(".//item"):
        title = item.find("title").text if item.find("title") is not None else "untitled_episode"
        print(f"Processing episode: {title}")

        transcripts = [elem for elem in item.iter() if 'transcript' in elem.tag]
        if not transcripts:
            print(f"No transcripts found for episode: {title}")
            continue

        text_plain_transcripts = [t for t in transcripts if t.get("type") == "text/plain"]
        if not text_plain_transcripts:
            print(f"No text/plain transcript found for episode: {title}")
            continue

        desired_transcript = text_plain_transcripts[-1]
        transcript_url = desired_transcript.get("url")
        if not transcript_url:
            print(f"No URL found for the transcript of episode: {title}")
            continue

        transcript_content = fetch_transcript(transcript_url)
        if not transcript_content:
            print(f"Transcript content could not be fetched for episode: {title}")
            continue

        sanitized_title = sanitize_filename(title)
        filename = f"{sanitized_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(transcript_content)
            print(f"Saved transcript for '{title}' to '{filepath}'")
        except IOError as e:
            print(f"Failed to write transcript to file '{filepath}': {e}")

if __name__ == "__main__":
    main()

