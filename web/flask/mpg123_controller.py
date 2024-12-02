import os
import subprocess
import logging
import threading
import time
from queue import Queue, Empty

logger = logging.getLogger(__name__)

class MPG123Controller:
    def __init__(self):
        self.fifo_path = "/tmp/mpg123_fifo"
        self.current_process = None
        self.output_queue = Queue()
        self.error_queue = Queue()
        self.monitor_thread = None
        self.is_running = False
        
        if not os.path.exists(self.fifo_path):
            os.mkfifo(self.fifo_path)
            
    def _monitor_output(self, stream, queue):
        """monitor output streams for errors and debugging"""
        for line in iter(stream.readline, b''):
            queue.put(line.decode().strip())
            
    def _monitor_process(self):
        """monitor the mpg123 process and its output"""
        while self.is_running and self.current_process:
            # check stdout
            try:
                while True:
                    line = self.output_queue.get_nowait()
                    # logger.debug(f"mpg123 output: {line}")
            except Empty:
                pass
                
            # check stderr
            try:
                while True:
                    line = self.error_queue.get_nowait()
                    logger.error(f"mpg123 error: {line}")
            except Empty:
                pass
                
            # check if process is still alive
            if self.current_process.poll() is not None:
                logger.error(f"mpg123 process died with return code {self.current_process.returncode}")
                self.is_running = False
                break
                
            time.sleep(0.1)

    def start_stream(self, stream_url, volume=25):
        self.stop_stream()
        try:
            # start mpg123 with more robust buffering options
            self.current_process = subprocess.Popen([
                'mpg123',
                '--keep-open',  # keep the process running even if stream ends
                #'-b', '4096',   # larger buffer size
                '--timeout', '10',  # longer network timeout
                '-R',          # remote control mode
                'v',           # verbose output
                '--fifo', self.fifo_path,
            ], stdin=subprocess.PIPE, 
               stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE,
               bufsize=1)  # line buffered
            
            # start output monitoring threads
            self.is_running = True
            threading.Thread(target=self._monitor_output, 
                           args=(self.current_process.stdout, self.output_queue),
                           daemon=True).start()
            threading.Thread(target=self._monitor_output, 
                           args=(self.current_process.stderr, self.error_queue),
                           daemon=True).start()
            
            # start process monitor thread
            self.monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            self.monitor_thread.start()
            
            logger.info(f"starting stream: {stream_url}")
            self.set_volume(volume)  # set initial volume
            
            # send load command to mpg123
            self.current_process.stdin.write(f"LOAD {stream_url}\n".encode())
            self.current_process.stdin.flush()
            
            return True
        except Exception as e:
            logger.exception(f"failed to start stream: {e}")
            return False

    def set_volume(self, volume):
        try:
            scale_factor = int((volume / 100) * 128)
            self.change_volume(scale_factor)
            logger.info(f"volume set to {volume}% (scale factor: {scale_factor})")
        except Exception as e:
            logger.exception(f"failed to set volume: {e}")

    def change_volume(self, scale_factor):
        try:
            if self.current_process and self.current_process.stdin:
                volume_cmd = f"VOLUME {scale_factor}\n"
                self.current_process.stdin.write(volume_cmd.encode())
                self.current_process.stdin.flush()
                logger.debug(f"volume command sent: {volume_cmd.strip()}")
        except Exception as e:
            logger.exception(f"failed to change volume: {e}")

    def stop_stream(self):
        if self.current_process:
            try:
                self.is_running = False
                # send quit command first
                try:
                    self.current_process.stdin.write(b"QUIT\n")
                    self.current_process.stdin.flush()
                except:
                    pass
                
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    
                self.current_process = None
                logger.info("stream stopped")
            except Exception as e:
                logger.exception(f"failed to stop stream: {e}")

    def __del__(self):
        self.stop_stream()
        if os.path.exists(self.fifo_path):
            try:
                os.remove(self.fifo_path)
            except Exception as e:
                logger.error(f"failed to remove fifo: {e}")