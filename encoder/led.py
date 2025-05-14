# Datasheet https://cdn.sparkfun.com/assets/a/b/1/e/1/DS-12877-LED_-_RGB_Addressable__PTH__8mm_Diffused__5_Pack_.pdf

from rpi_ws281x import *

TOTAL_LED_COUNT = 1
LED_CHIP_NUMBER = 0
R = 255
G = 255
B = 0

strip = Adafruit_NeoPixel(TOTAL_LED_COUNT, 21, 800000, 5, False, 255)
strip.begin()
strip.setPixelColorRGB(LED_CHIP_NUMBER, R, G, B)
strip.show()
