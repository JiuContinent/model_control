from pymavlink import mavutil

connection = mavutil.mavlink_connection('udp:127.0.0.1:14550')

# Read and print all received messages
while True:
    message = connection.recv_match()
    if message:
        print(message)