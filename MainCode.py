from colorthief import ColorThief
import os
import RPi.GPIO as GPIO
import time
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

kit.servo[0].angle = 0
kit.servo[1].angle = 0
kit.servo[2].angle = 0

KNOWN_COLORS = {"Red": (255, 0, 0), "Yellow": (255, 255, 0)}

def main():
    print("Main")
    StartGame()

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
    Move = input()
    print(bin(int(Move)))
    MakeMove(Move)

def TheirMove():
    print("Their move")
    Move = input()
    if Move in ("W","w","L","l"):
        EndGame(Move)
        return False
    else:
        print(Move)
        print(bin(int(Move)))
        MakeMove(Move)
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
        kit.servo[0].angle = 180
    else:
        print("Top Motors in Pos 0")
        kit.servo[0].angle = 0

    if int(Pos[1]) == 1:
        print("Mid Motors in Pos 1")
        kit.servo[1].angle = 180
    else:
        print("Mid Motors in Pos 0")
        kit.servo[1].angle = 0

    if int(Pos[2]) == 1:
        print("Bot Motors in Pos 1")
        kit.servo[2].angle = 180
    else:
        print("Bot Motors in Pos 0")
        kit.servo[2].angle = 90
    time.sleep(10)

def EndGame(Move):
    print("Game ending")
    if Move in ("W","w"):
        print("You Win")
    else:
        print("You Lose")
    ColourPicker()
    Reset()

def Reset():
    print("Reseting Board")
    main()
            
def ColourPicker():
    for filename in os.listdir('Images'):
        print(filename)
        Image_Colour = ColourTest(filename)
        print(Image_Colour)
        print(get_color_name(Image_Colour))
        
        
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

def ColourTest(ImageName):
    color_thief = ColorThief("Images/" + ImageName)
    dominant_color = color_thief.get_color(quality=1)
    return dominant_color

if __name__ == '__main__':
    main()
