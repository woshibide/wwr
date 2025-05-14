import rotary_encoder
import pigpio
#import neopixel
from gpiozero import Button, LED
from time import sleep
import logging 

# this is to share in virtual memory rotary position
from multiprocessing.shared_memory import SharedMemory
import struct  # For packing/unpacking binary data

logging.basicConfig(level=logging.INFO)

# These are the GPIO pin numbers for your encoder.
# Use the BCM numbers, not the Board number for these variables.
channel_A = 17 # Using GPIO17
channel_B = 18 # Using GPIO18

# Reading the button
button = Button(15)  # Using GPIO15
led = LED(21) # Using GPIO21

logging.info(f"reading the button")

def btn_pressed():
    logging.info(f"button pressed")
    led.on()

def btn_released():
    logging.info(f"button released")
    led.off()

button.when_pressed = btn_pressed
button.when_released = btn_released

position = 0 # The current position of the encoder - default to zero at program start.
old_position = 0 # The previous position of the encoder - used to skip writing to the console
# unless the position has changed.

def callback(way): # Updates the position with the direction the encoder was turned.
    global position
    position += way

pi = pigpio.pi() # Defines the specfic Raspberry Pi we are polling for information - defaults to the local device.
decoder = rotary_encoder.decoder(pi, channel_A, channel_B, callback) # Creates an object that automatically fires
# the callback function whenever a change on channel_A or channel_B is detected on the defined Raspberry Pi

while True: # Only prints the position of the encoder if a change has been made, refreshing every millisecond.
            # Helps reduce lag when moving a high resolution encoder extremely quickly.
            # Interstingly, the system didn't lose counts for me, but it did take an inordinate amount of time
            # to catch up when wiriting to the console.
    if position != old_position:
        # print("pos = {}".format(position))
        shm = SharedMemory(name="encoder_position", create=True, size=4)  # Allocate 4 bytes for an integer

        try:
            while True:
                if position != old_position:
                    print("pos = {}".format(position))
                    # write position to shared memory
                    shm.buf[:4] = struct.pack("i", position)  # pack as 4-byte integer
                    old_position = position
                    sleep(0.001)
        except KeyboardInterrupt:
            pass
        finally:
            shm.close()
            shm.unlink()  # clean up shared memory when the script exits

        old_position = position
        sleep(0.001)

