#!/usr/bin/python

from colorthief import ColorThief
import os
import RPi.GPIO as GPIO
import time
from adafruit_servokit import ServoKit
from picamera2 import Picamera2, Preview
import board
from adafruit_neokey.neokey1x4 import NeoKey1x4
from signal import signal, SIGTERM, SIGHUP, pause
import qwiic_serlcd
import socket

lcd = qwiic_serlcd.QwiicSerlcd()

lcd.setBacklight(255, 255, 255) # Set backlight to bright white
lcd.setContrast(5) # set contrast. Lower to 0 for higher contrast.
lcd.clearScreen()

# use default I2C bus
i2c_bus = board.I2C()

# Create a NeoKey object
neokey = NeoKey1x4(i2c_bus, addr=0x30)

kit = ServoKit(channels=16)

kit.servo[0].angle = 90
kit.servo[1].angle = 0
kit.servo[2].angle = 0
kit.servo[3].angle = 0
kit.servo[4].angle = 0
kit.servo[5].angle = 0
kit.servo[6].angle = 0
kit.servo[7].angle = 0
kit.servo[8].angle = 90

KNOWN_COLORS = {"Red": (255, 0, 0), "Yellow": (255, 255, 0)}

picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
picam2.configure(camera_config)
picam2.start()
time.sleep(2)


def main():
    print("Main")
    StartGame()
    
def safe_exit(signum, frame):
    exit(1)

def StartGame():
    print("Starting Game")
    Game()
    
def Game():
    print("In Game")
    GameOn = True
    while GameOn:
        MyMove()
        GameOn = TheirMove()

def MyMove():
    print("My move")
    lcd.setCursor(0,0)
    lcd.print("Your Move")
    kit.servo[0].angle = 90
    # ~ Move = input()
    # ~ print(bin(int(Move)))
    Move = MakeSelection()
    if Move == 4:
        Move = 3
    elif Move < 4:
        Move = Move - 1
    else:
        Move = Move
    MakeMove(Move)
    kit.servo[0].angle = 180
    time.sleep(0.2)
    kit.servo[0].angle = 90
    
def MakeSelection():
    column=1
    signal(SIGTERM, safe_exit)
    signal(SIGHUP, safe_exit)
    while True:
        if neokey[0]:
            print("Button A")
            if column < 7:
                column=column+1
            else:
                column = column
            print(column)
            time.sleep(0.1)
            neokey.pixels[0] = 0xFF0000
            lcd.clearScreen()
            lcd.setCursor(0,0)
            lcd.print("Column")
            lcd.setCursor(0,1)
            lcd.print(str(column))
        else:
            neokey.pixels[0] = 0x0

        if neokey[1]:
            print("Button B")
            return column
            neokey.pixels[1] = 0xFFFF00
        else:
            neokey.pixels[1] = 0x0

        if neokey[2]:
            print("Button C")
            return column
            neokey.pixels[2] = 0x00FF00
        else:
            neokey.pixels[2] = 0x0

        if neokey[3]:
            print("Button D")
            if column > 1:
                column=column-1
            else:
                column = column
            print(column)
            time.sleep(0.1)
            neokey.pixels[3] = 0x00FFFF
            lcd.clearScreen()
            lcd.setCursor(0,0)
            lcd.print("Column")
            lcd.setCursor(0,1)
            lcd.print(str(column))
        else:
            neokey.pixels[3] = 0x0

def TheirMove():
    print("Their move")
    kit.servo[0].angle = 90
    Move = input()
    if Move in ("W","w","L","l"):
        EndGame(Move)
        return False
    else:
        print(Move)
        print(bin(int(Move)))
        MakeMove(Move)
        kit.servo[0].angle = 0
        time.sleep(0.15)
        kit.servo[0].angle = 90
        return True
    
def MakeMove(Move):
    print("Making Move")
    print(Move)
    Pos = ('{0:03b}'.format(int(Move)))
    print(Pos)
    print(type(Pos))
    print(Pos[0])
    print(Pos[1])
    print(Pos[2])
    
    if int(Pos[0]) == 1:
        print("Top Motors in Pos 1")
        kit.servo[1].angle = 0
    else:
        print("Top Motors in Pos 0")
        kit.servo[1].angle = 175

    if int(Pos[1]) == 1:
        print("Mid Motors in Pos 1")
        kit.servo[2].angle = 0
        kit.servo[3].angle = 0
    else:
        print("Mid Motors in Pos 0")
        kit.servo[2].angle = 90
        kit.servo[3].angle = 90

    if int(Pos[2]) == 1:
        print("Bot Motors in Pos 1")
        kit.servo[4].angle = 0
        kit.servo[5].angle = 0
        kit.servo[6].angle = 0
        kit.servo[7].angle = 0
    else:
        print("Bot Motors in Pos 0")
        kit.servo[4].angle = 175
        kit.servo[5].angle = 140
        kit.servo[6].angle = 140
        kit.servo[7].angle = 180
    time.sleep(1)

def EndGame(Move):
    print("Game ending")
    if Move in ("W","w"):
        print("You Win")
        lcd.print("You Win")
    else:
        print("You Lose")
        lcd.print("You Lose")
    ColourPicker()
    Reset()

def Reset():
    print("Reseting Board")
    main()
            
def ColourPicker():
#     for filename in os.listdir('Images'):
#         kit.servo[8].angle = 90
#         time.sleep(10)
#         print(filename)
#         Image_Colour = ColourTest(filename)
#         print(Image_Colour)
#         PieceColour = get_color_name(Image_Colour)
#         print(PieceColour)
#         if PieceColour == "Red":
#             kit.servo[8].angle = 0
#             time.sleep(2)
#         else:
#             kit.servo[8].angle = 180
#             time.sleep(2)
    
    
    for i in range(50):
        picam2.capture_file("token.jpg")
        kit.servo[8].angle = 90
        time.sleep(1)
        #print(filename)
        Image_Colour = ColourTest()
        print(Image_Colour)
        PieceColour = get_color_name(Image_Colour)
        print(PieceColour)
        if PieceColour == "Red":
            kit.servo[8].angle = 0
            time.sleep(2)
        else:
            kit.servo[8].angle = 180
            time.sleep(2)
        
        
def color_difference (color1, color2) -> int:
    """ calculate the difference between two colors as sum of per-channel differences """
    return sum([abs(component1-component2) for component1, component2 in zip(color1, color2)])


def get_color_name(color) -> str:
    """ guess color name using the closest match from KNOWN_COLORS """
    differences =[
        [color_difference(color, known_color), known_name]
        for known_name, known_color in KNOWN_COLORS.items()
    ]
    differences.sort()  # sorted by the first element of inner lists
    return differences[0][1]  # the second element is the name

def ColourTest():
    color_thief = ColorThief("token.jpg")
    dominant_color = color_thief.get_color(quality=1)
    return dominant_color

if __name__ == '__main__':
    main()

