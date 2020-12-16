import serial
import time

ser = serial.Serial('COM7', 115200)

file = open("g_code_Mittelkreuz.txt", "r")
time.sleep(2)

ser.flushInput()

for line in file:
    l = line.strip()
    ser.write(str.encode(l + "\n"))
    output = ser.readline()

print("GCODE SENT")
time.sleep(1)
file.close()
ser.close()
