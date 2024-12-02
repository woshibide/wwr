import logging
import json
from mpg123_controller import MPG123Controller
from flask import current_app
from config import NOW_PLAYING_PATH

logger = logging.getLogger(__name__)

class AudioPlayer:
    def __init__(self):
        self.player = MPG123Controller()
        self.current_volume = 25
        self.current_stream_url = None

    def play_stream(self, stream_url, volume=None):
        logger.info(f"starting stream: {stream_url} with volume: {volume if volume else self.current_volume}")
        self.current_stream_url = stream_url
        
        if volume is not None:
            self.current_volume = volume

        try:
            if self.player.start_stream(stream_url, self.current_volume):
                self.update_now_playing(is_playing=True, stream_url=stream_url)
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
                self.player.set_volume(volume)
                self.update_now_playing(volume=volume)
            except Exception as e:
                logger.error(f"failed to update volume: {e}")

    def stop_stream(self):
        self.player.stop_stream()
        self.update_now_playing(is_playing=False)

    def update_now_playing(self, is_playing=None, stream_url=None, volume=None):
        try:
            with open(NOW_PLAYING_PATH, 'r', encoding='utf-8') as f:
                now_playing = json.load(f)
            
            if is_playing is not None:
                now_playing['current_station']['is_playing'] = is_playing
            if stream_url:
                now_playing['current_station']['url'] = stream_url
            if volume is not None:
                now_playing['current_station']['volume'] = volume

            with open(NOW_PLAYING_PATH, 'w', encoding='utf-8') as f:
                json.dump(now_playing, f, indent=4)
            
            logger.info(f"updated now_playing.json: {now_playing}")
        except Exception as e:
            logger.error(f"failed to update now playing: {e}")