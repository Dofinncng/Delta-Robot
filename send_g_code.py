import serial
import time
import pathfinder_xi

class send:

    def __init__(self):
        try:
            self.ser = serial.Serial('COM7', 115200)
            time.sleep(2)
            self.ser.flushInput()
            print('Serielle Verbindung erfolgreich aufgebau')
        except:
            print('ERROR: Serielle Verbindung konnte nicht hergestellt werden')


    def txt(self):
        file = open("g_code.txt", "r")
        state=True

        for line in file:
            if pathfinder_xi.trigger_laser:
                l = line.strip()
                self.ser.write(str.encode(l + "\n"))
                output = self.ser.readline()
            else:
                self.ser.write(str.encode('M107' + "\n"))
                print('G-CODE senden abgebrochen')
                state=False
                break

        print("GCODE SENT")
        time.sleep(1)
        file.close()
        self.ser.close()
        return state

    def execude(self, order):
        self.ser.write(str.encode(order + "\n"))
        output = self.ser.readline()
        print("DONE",order)
        #return output

    def serClose(self):
        time.sleep(1)
        self.ser.close()



