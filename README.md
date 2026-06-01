# YTag

YTag is a command-line application to assign tags to songs in a YouTube playlist and play subsets of songs based on those tags.

## Usage
1. Create your CSV
```bash
python ytag.py [-c CREATE] "youtube_url" [-o OUTPUT] "classical.csv"
```
The created CSV serves as the backend for YTag to operate on with tagging

2. Once you have the CSV file, you can begin tagging
```bash
python ytag.py [-e EDIT] "classical.csv"
```

3. Finally, play a playlist, optionally with a tag
```bash
python ytag.py [-p PLAYLIST] "classical.csv" [-t TAG] "bach"
```

## Background 
I primarily listen to music via YouTube (no, I do not use Spotify) due to the variety of classical music recordings available (e.g., artists other than Hilary Hahn or Itzhak Perlman).
There are a variety of types of "Classical Music" such as Baroque, Romantic, and even more granular, Bach, Vivaldi, Beethoven, etc. This same idea applies to Indian music.

I have different music-listening moods, so why not create an app to fill this (what I believe to be) very real need.
