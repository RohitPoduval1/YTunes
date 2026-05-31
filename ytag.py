import argparse
import csv
import re
import sys
import subprocess
import yt_dlp

from tag_app import YTag


def play_playlist(playlist_path, tag_to_play) -> None:
    ids = []
    with open(playlist_path, mode="r") as f:
        csv_reader = csv.reader(f)
        for (_, id, tags) in csv_reader:
            if not tag_to_play:
                ids.append(id)
                continue

            if tag_to_play in tags:
                ids.append(id)

    urls = [f"https://youtu.be/{id}" for id in ids]
    command = "mpv --no-video --script-opts=ytdl_hook-ytdl_path=yt-dlp --ytdl-format=bestaudio".split(" ")
    command.extend(urls)
    subprocess.run(command)


def create_csv_from_playlist(playlist_url, csv_filename):
    ydl_opts = {
        'extract_flat': True, 
        'quiet': True
    }

    num_valid_songs = 0
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("Fetching playlist data. This may take a moment...")
        match = re.match(r"((?:https://)?.+/)(.+)", playlist_url)
        if not match:
            raise Exception("Regex failed")
        playlist_id = match.group(2)
        playlist_id = playlist_id.replace("\\", "")
        cleaned_playlist_url = match.group(1) + playlist_id

        info_dict = ydl.extract_info(cleaned_playlist_url, download=False)

        entries = info_dict.get('entries', [])

        # Open a new CSV file to write the data
        with open(csv_filename, mode='w+', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Loop through the playlist and write each video's title and URL
            for entry in entries:
                # yt-dlp flat extraction usually returns just the url, title, and id
                url = entry.get('url')
                title = entry.get('title')
                if re.match(r"\[\w+ video\]", title):
                    continue

                writer.writerow([title.strip(), url, ""])
                num_valid_songs += 1

    print(f"✅ {num_valid_songs} videos saved to {csv_filename}!")
    if num_valid_songs != len(entries):
        print(f"❌ {len(entries) - num_valid_songs} songs in the playlist are invalid")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="YTag",
        description="Tag songs in YouTube playlists and play songs based on those tags",
    )
    parser.add_argument("-c", "--create", help="Create YTag compatible playlist from YouTube URL")
    parser.add_argument("-o", "--output", help="The name of the CSV file to create from the URL")

    parser.add_argument("-e", "--edit", help="Edit the tags of the given file")

    parser.add_argument("-p", "--playlist", help="Which playlist to play")

    # TODO: Multi-tag support
    parser.add_argument("-t", "--tag", help="Filter tag to play")

    # TODO: Add updating a playlist given the URL while keeping existing tags

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.create and args.output:
        create_csv_from_playlist(playlist_url=args.create, csv_filename=args.output)

    if args.edit:
        app = YTag(args.edit)
        app.run()

    if args.playlist:
        play_playlist(playlist_path=args.playlist, tag_to_play=args.tag)


if __name__ == "__main__":
    main()

