import os
import subprocess

# Create a named pipe (FIFO) if it doesn't already exist
fifo_path = "/tmp/mpg123_fifo"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# Start mpg123 with a subprocess and open the FIFO for writing commands
mpg123_process = subprocess.Popen(['mpg123', '-C', 'your_stream_url'], stdin=subprocess.PIPE)

try:
    while True:
        # Open the FIFO for reading
        with open(fifo_path, 'r') as fifo:
            while True:
                # Read a volume command from the FIFO
                command = fifo.readline().strip()
                if command in ('+', '-'):
                    # Send the command to mpg123's stdin
                    mpg123_process.stdin.write(command.encode())
                    mpg123_process.stdin.flush()
except KeyboardInterrupt:
    pass
finally:
    mpg123_process.terminate()
    os.remove(fifo_path)