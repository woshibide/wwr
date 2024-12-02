import logging
import os
import signal
from mpg123_controller import MPG123Controller

logger = logging.getLogger(__name__)

class AudioPlayer:
    def __init__(self):
        self.player = MPG123Controller()
        self.current_volume = 25  # default volume
        self.current_stream_url = None

    def play_stream(self, stream_url, volume=None):
        logger.info(f"starting stream: {stream_url} with volume: {volume if volume else self.current_volume}")
        self.current_stream_url = stream_url
        
        if volume is not None:
            self.current_volume = volume

        try:
            if self.player.start_stream(stream_url, self.current_volume):
                return True
            raise RuntimeError("failed to start stream")
        except Exception as e:
            logger.error(f"failed to start stream: {e}")
            raise RuntimeError(f"failed to start the stream: {e}")

    def set_volume(self, volume):
        logger.info(f"setting volume to: {volume}")
        self.current_volume = volume
        if self.current_stream_url:
            try:
                if not self.player.set_volume(volume):
                    # TODO: fix this behaviour
                    raise RuntimeError("says whatever but volume changes")
            except Exception as e:
                logger.error(f"failed to update volume: {e}")


    def stop_stream(self):
        if self.current_process:
            logger.info("stopping current stream")
            try:
                os.kill(self.current_process.pid, signal.SIGTERM)
                self.current_process.wait()  # ensure process is cleaned up
                self.current_process = None
            except Exception as e:
                logger.error(f"failed to stop stream: {e}", exc_info=True)
                raise RuntimeError(f"failed to stop the stream: {e}")

