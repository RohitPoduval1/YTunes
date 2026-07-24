import json
import os
import socket
import subprocess
from typing import List, Optional


class MpvService:
    """Manages the mpv subprocess and handles IPC communication."""
    
    def __init__(self, ipc_socket_path: str = "/tmp/ytunes_mpv.sock"):
        self.ipc_socket_path = ipc_socket_path
        self.player_process: Optional[subprocess.Popen] = None

    def play_urls(self, urls: List[str]) -> None:
        """Kills any existing player and starts a new one with a batch of URLs."""
        self.quit()  # Clean up existing process if something is already playing
        
        command = [
            "mpv",
            "--no-video",
            f"--input-ipc-server={self.ipc_socket_path}",
            "--ytdl-raw-options=cookies-from-browser=safari",
        ] + urls

        self.player_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def toggle_play(self) -> None:
        self._send_ipc_command(["cycle", "pause"])

    def skip_next(self) -> None:
        self._send_ipc_command(["playlist-next"])

    def skip_prev(self) -> None:
        self._send_ipc_command(["playlist-prev"])

    def get_current_title(self) -> str:
        """Fetches the title of the active track from mpv."""
        title = self._send_ipc_command(["get_property", "media-title"])
        return title if title else "None"

    def get_time_info(self) -> str:
        """Fetches and formats the current playback position and duration."""
        pos = self._send_ipc_command(["get_property", "time-pos"])
        dur = self._send_ipc_command(["get_property", "duration"])

        def fmt(seconds: Optional[float]) -> str:
            if not seconds: 
                return "00:00"
            m, s = divmod(int(seconds), 60)
            return f"{m:02d}:{s:02d}"

        return f"{fmt(pos)} / {fmt(dur)}"

    def quit(self) -> None:
        """Terminates the mpv process and cleans up the socket."""
        if self.player_process:
            self._send_ipc_command(["quit"])
            self.player_process.terminate()
            self.player_process = None
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except OSError:
                pass

    def _send_ipc_command(self, command: list):
        """Sends a command to the mpv socket and returns the result."""
        if not os.path.exists(self.ipc_socket_path):
            print("Socket path does not exist")
            return None

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.ipc_socket_path)
        message = json.dumps({"command": command}) + "\n"
        client.sendall(message.encode('utf-8'))
        
        response = client.recv(4096).decode('utf-8')
        client.close()
        
        if response:
            print("Received response")
            data = json.loads(response.split('\n')[0])
            return data.get("data")

        print("No response received")
        return None

if __name__ == "__main__":
    import time
    
    mpv_serv = MpvService()
    print("Starting mpv...")
    mpv_serv.play_urls(["https://youtu.be/HvKTPDg0IW0"])
    
    print("Waiting for yt-dlp to resolve the audio (this takes a few seconds)...")
    
    try:
        while True:
            # Sleep for 1 second, simulating our Textual polling timer
            time.sleep(1)
            
            # Query the IPC socket
            title = mpv_serv.get_current_title()
            time_info = mpv_serv.get_time_info()
            
            print(f"Now Playing: {title} | {time_info}")
            
    except KeyboardInterrupt:
        # Catch Ctrl+C to cleanly shut down the player and socket
        print("\nQuitting and cleaning up...")
        mpv_serv.quit()
