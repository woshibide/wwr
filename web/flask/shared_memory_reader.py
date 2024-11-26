from multiprocessing.shared_memory import SharedMemory
import struct
import time

while True:
    try:
        # Attempt to connect to the shared memory block
        shm = SharedMemory(name="encoder_position")
        break
    except FileNotFoundError:
        print("Shared memory 'encoder_position' not found. Waiting...")
        time.sleep(1)  # Wait and retry

try:
    while True:
        # Read and unpack the 4-byte integer from shared memory
        position = struct.unpack("i", shm.buf[:4])[0]
        print(f"Shared memory position: {position}")
        time.sleep(0.1)  # Slow down the output for readability
except KeyboardInterrupt:
    pass
finally:
    shm.close()  # Clean up shared memory access

