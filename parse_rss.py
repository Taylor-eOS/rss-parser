import os
import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import urllib.request
import threading
from datetime import datetime

SETTINGS_FILE = 'settings.json'
WINDOW_DIMENSIONS = "965x920"

def load_settings():
    default_settings = {"rss_feed_url": "", "downloaded_files": []}
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings
    with open(SETTINGS_FILE, "r") as f:
        try:
            settings = json.load(f)
            return settings
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid format in settings file.")
            return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def download_mp3(url, title, progress, button, pub_day, hour_info):
    filename = f"{pub_day.replace(' ', '')}_{hour_info.replace(' ', '').lower() if hour_info else 'o'}.mp3"
    if os.path.exists(filename):
        button.config(text="Downloaded", state=tk.DISABLED, style="Downloaded.TButton")
        return
    try:
        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            total_length = response.getheader('Content-Length')
            if total_length is None:
                out_file.write(response.read())
                progress['value'] = 100
            else:
                total_length = int(total_length)
                downloaded = 0
                block_size = 8192
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)
                    progress_value = int(downloaded / total_length * 100)
                    progress['value'] = progress_value
                    root_window.update_idletasks()
        progress['value'] = 100
        button.config(text="Downloaded", state=tk.DISABLED, style="Downloaded.TButton")
        settings['downloaded_files'].append(filename)
        save_settings(settings)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download '{title}': {str(e)}")
        progress['value'] = 0
settings = load_settings()
rss_feed_url = settings.get("rss_feed_url", "")
if not rss_feed_url:
    messagebox.showerror("Error", "RSS feed URL not found in settings file.")
    exit(1)
try:
    response = requests.get(rss_feed_url)
    response.raise_for_status()
    root = ET.fromstring(response.content)
except Exception as e:
    messagebox.showerror("Error", f"Failed to fetch RSS feed: {str(e)}")
    exit(1)
root_window = tk.Tk()
root_window.title("Podcast Feed")
root_window.geometry(WINDOW_DIMENSIONS)
root_window.resizable(False, False)
style = ttk.Style(root_window)
style.theme_use('clam')
style.configure("TFrame", background="#2E3440")
style.configure("Header.TLabel", background="#2E3440", foreground="#D8DEE9", font=("Helvetica", 18, "bold"))
style.configure("Episode.TFrame", background="#3B4252", relief="groove", borderwidth=2)
style.configure("TLabel", background="#3B4252", foreground="#D8DEE9", font=("Helvetica", 12))
style.configure("Date.TLabel", background="#3B4252", foreground="#808080", font=("Helvetica", 12))
style.configure("Download.TButton", foreground="#2E3440", background="#A3BE8C", font=("Helvetica", 10, "bold"))
style.map("Download.TButton",
          background=[('active', '#88C0D0')],
          foreground=[('active', '#2E3440')])
style.configure("Downloaded.TButton", foreground="#2E3440", background="#81A1C1", font=("Helvetica", 10, "bold"))
style.map("Downloaded.TButton",
          background=[('active', '#5E81AC')],
          foreground=[('active', '#2E3440')])
style.configure("TProgressbar", troughcolor="#3B4252", background="#88C0D0", bordercolor="#3B4252", lightcolor="#88C0D0", darkcolor="#88C0D0")
main_frame = ttk.Frame(root_window, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)
title_label = ttk.Label(main_frame, text="Podcast Feed", style="Header.TLabel")
title_label.pack(pady=(0, 20))
episodes_frame = ttk.Frame(main_frame, style="TFrame")
episodes_frame.pack(side="left")
columns = 2
current_row = 0
current_column = 0
max_episodes = 8
episode_count = 0
for item in root.findall(".//item"):
    if episode_count >= max_episodes:
        break
    title = item.find("title").text
    pub_date = item.find("pubDate").text
    #Check for 'Hour X' in description or content:encoded
    hour_info = ""
    description = item.find("description")
    content_encoded = item.find("content:encoded")
    text_to_search = (description.text if description is not None else "") + (content_encoded.text if content_encoded is not None else "")
    for hour in ["Hour 1", "Hour 2", "Hour 3", "Hour 4"]:
        if hour in text_to_search:
            hour_info = hour
            break
    media_content = item.findall("media:content", namespaces={'media': 'http://search.yahoo.com/mrss/'})
    mp3_url = None
    for media in media_content:
        url = media.get("url")
        if "mp3" in url:
            mp3_url = url
            break
    if not mp3_url:
        continue
    pub_day = ""
    if pub_date:
        pub_datetime = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
        pub_day = pub_datetime.strftime("%d %b")  
    filename = f"{pub_day.replace(' ', '')}_{hour_info.replace(' ', '').lower() if hour_info else 'o'}.mp3"
    episode_frame = ttk.Frame(episodes_frame, style="Episode.TFrame", padding="10")
    episode_frame.grid(row=current_row, column=current_column, padx=10, pady=10, sticky="nsew")
    #Display the hour info before the date if found
    ep_label = ttk.Label(episode_frame, text=title, wraplength=400)
    ep_label.pack(anchor="w", pady=(0, 5))
    if hour_info:
        hour_label = ttk.Label(episode_frame, text=hour_info, style="TLabel")
        hour_label.pack(anchor="e", pady=(0, 5))
    date_label = ttk.Label(episode_frame, text=pub_day, style="Date.TLabel")
    date_label.pack(anchor="e", pady=(0, 10))
    progress = ttk.Progressbar(episode_frame, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
    progress.pack(pady=(0, 10))
    if filename in settings['downloaded_files']:
        button_text = "Downloaded"
        button_state = tk.DISABLED
        button_style = "Downloaded.TButton"
    else:
        button_text = "Download"
        button_state = tk.NORMAL
        button_style = "Download.TButton"
    download_button = ttk.Button(
        episode_frame,
        text=button_text,
        state=button_state,
        style=button_style
    )
    download_button.pack()
    if button_state == tk.NORMAL:
        download_button.config(command=lambda url=mp3_url, title=title, prog=progress, btn=download_button, day=pub_day, hour=hour_info: threading.Thread(target=download_mp3, args=(url, title, prog, btn, day, hour)).start())
    episode_count += 1
    current_column += 1
    if current_column >= columns:
        current_column = 0
        current_row += 1

def next_page():
    global episode_count, current_row, current_column, episodes_frame
    episode_count = 0
    current_row = 0
    current_column = 0
    for widget in episodes_frame.winfo_children():
        widget.destroy()
    start_index = (page_number * max_episodes)
    end_index = start_index + max_episodes
    for item in root.findall(".//item")[start_index:end_index]:
        if episode_count >= max_episodes:
            break
        title = item.find("title").text
        pub_date = item.find("pubDate").text
        #Check for 'Hour X' in description or content:encoded
        hour_info = ""
        description = item.find("description")
        content_encoded = item.find("content:encoded")
        text_to_search = (description.text if description is not None else "") + (content_encoded.text if content_encoded is not None else "")
        for hour in ["Hour 1", "Hour 2", "Hour 3", "Hour 4"]:
            if hour in text_to_search:
                hour_info = hour
                break
        media_content = item.findall("media:content", namespaces={'media': 'http://search.yahoo.com/mrss/'})
        mp3_url = None
        for media in media_content:
            url = media.get("url")
            if "mp3" in url:
                mp3_url = url
                break
        if not mp3_url:
            continue
        pub_day = ""
        if pub_date:
            pub_datetime = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            pub_day = pub_datetime.strftime("%d %b")  
        filename = f"{pub_day.replace(' ', '')}_{hour_info.replace(' ', '').lower() if hour_info else 'o'}.mp3"
        episode_frame = ttk.Frame(episodes_frame, style="Episode.TFrame", padding="10")
        episode_frame.grid(row=current_row, column=current_column, padx=10, pady=10, sticky="nsew")
        #Display the hour info before the date if found
        ep_label = ttk.Label(episode_frame, text=title, wraplength=400)
        ep_label.pack(anchor="w", pady=(0, 5))
        if hour_info:
            hour_label = ttk.Label(episode_frame, text=hour_info, style="TLabel")
            hour_label.pack(anchor="e", pady=(0, 5))
        date_label = ttk.Label(episode_frame, text=pub_day, style="Date.TLabel")
        date_label.pack(anchor="e", pady=(0, 10))
        progress = ttk.Progressbar(episode_frame, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
        progress.pack(pady=(0, 10))
        if filename in settings['downloaded_files']:
            button_text = "Downloaded"
            button_state = tk.DISABLED
            button_style = "Downloaded.TButton"
        else:
            button_text = "Download"
            button_state = tk.NORMAL
            button_style = "Download.TButton"
        download_button = ttk.Button(
            episode_frame,
            text=button_text,
            state=button_state,
            style=button_style
        )
        download_button.pack()
        if button_state == tk.NORMAL:
            download_button.config(command=lambda url=mp3_url, title=title, prog=progress, btn=download_button, day=pub_day, hour=hour_info: threading.Thread(target=download_mp3, args=(url, title, prog, btn, day, hour)).start())
        episode_count += 1
        current_column += 1
        if current_column >= columns:
            current_column = 0
            current_row += 1

def next_page_handler():
    global page_number
    page_number += 1
    next_page()
page_number = 0
next_button = ttk.Button(main_frame, text=">", command=next_page_handler)
next_button.pack(side="right", padx=10, pady=10, anchor="ne")
root_window.mainloop()

