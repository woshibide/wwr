import subprocess
import os
import signal
import logging

class AudioPlayer:
    def __init__(self):
        self.current_process = None

    def play_stream(self, stream_url):
        self.stop_stream()

        try:
            # Split the mpg123 command and its arguments properly
            self.current_process = subprocess.Popen(['mpg123', '-a', 'hw:1,0', stream_url])
        except Exception as e:
            raise RuntimeError(f"Failed to start the stream: {e}")

    def stop_stream(self):
        if self.current_process:
            try:
                os.kill(self.current_process.pid, signal.SIGTERM)
                self.current_process.wait()  # to ensure the process is cleaned up
                self.current_process = None
            except Exception as e:
                raise RuntimeError(f"Failed to stop the stream: {e}")

