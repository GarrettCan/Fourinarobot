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
lcd.clearScreen() #Clear LCD

# use default I2C bus
i2c_bus = board.I2C()

# Create a NeoKey object
neokey = NeoKey1x4(i2c_bus, addr=0x30)

#Setup Servo Control
kit = ServoKit(channels=16)

#Set initial Angles for all servos
kit.servo[0].angle = 90
kit.servo[1].angle = 0
kit.servo[2].angle = 0
kit.servo[3].angle = 0
kit.servo[4].angle = 0
kit.servo[5].angle = 0
kit.servo[6].angle = 0
kit.servo[7].angle = 0
kit.servo[8].angle = 90

#Define colours for colour detection
KNOWN_COLOURS = {"Red": (255, 0, 0), "Yellow": (255, 255, 0)}#Could add white as an option to detect if there is no piece found, would likely be "White": (255,255,255) would need to verify this doesn't interfere with yellow

#Start and set up the camera
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores") #Lowering the size/resolution could help speed up the camera, would need to test to see impact on colour detection 
picam2.configure(camera_config)
picam2.start()
time.sleep(2) #Delay to allow camera to start


def main():
    print("Main")
    StartGame()
    
def safe_exit(signum, frame):
    exit(1)

def StartGame():
    """
    Starting place for the connect 4 game. Makes any required API calls required to start the game
    """
    print("Starting Game")
    Game()
    
def Game():
    """
    First part of the game, checks that game is still running
    """
    print("In Game")
    GameOn = True
    while GameOn:
        MyMove() #Calls the physical player to make a move
        GameOn = TheirMove() # Calls the digital player to make a move. This approach should be reworked to allow the api to dictate what player should make a move

def MyMove():
    """
    Function that handles the player move
    """
    print("My move") #Debug
    lcd.setCursor(0,0) #sets lcd cursor to start of top line
    lcd.print("Your Move") #Prints a message to the user
    kit.servo[0].angle = 90 #Makes sure servo is in correct position, Can probably be removed because the servo should always be reset to this position anyway
    #Move = input()
    #print(bin(int(Move))) #These 2 lines are debug lines that allow the move to be controlled by the console, useful for testing
    Move = MakeSelection() #Calls the function to read the key presses, if pervious 2 lines are in use comment this out
    if Move == 4: #The input is adjusted to convert the index 1 player interface into the index 0 system used to control the servos. 3 and 4 represent the middle point so they are both set to 3.
        Move = 3
    elif Move < 4: #Everything below the mid point needs to be adjusted down by one value. i.e column 1 becomes column 0
        Move = Move - 1
    else:
        Move = Move
    MakeMove(Move) #Calls function to set the angle of the servos
    kit.servo[0].angle = 180 #Opens the gate
    time.sleep(0.2) #Short time for piece to fall through, adjust if pieces aren't able to get through or if more than one piece falls through
    kit.servo[0].angle = 90 #Set servo back to default position
    
def MakeSelection():
    """
    Function used to take user input using Neokey 1x4, returns an int between 1 and 7
    """
    #Function is currently set up to use one NeoKey board with oposite sides being used as left right arrows and the middle two buttons working as enter buttons, Ideally a second neokey board would be added to give 8 button options where 1 button represents 1 column.
    column=1 #Starting value for column
    signal(SIGTERM, safe_exit)
    signal(SIGHUP, safe_exit)
    while True: #While loop to allow the user enough button presses to make selection
        if neokey[0]: #Move column selection to the right
            print("Button A") #Debug
            if column < 7:
                column += 1 #Increment column by 1
            else:
                column = column
            print(column)
            time.sleep(0.1)
            neokey.pixels[0] = 0xFF0000 #Controls RGB LED in the key
            lcd.clearScreen()
            lcd.setCursor(0,0)
            lcd.print("Column")
            lcd.setCursor(0,1) 
            lcd.print(str(column)) #Upddate LCD to let user know what column is selected
        else:
            neokey.pixels[0] = 0x0

        if neokey[1]: #Enter Button
            print("Button B") #Debug
            return column
            neokey.pixels[1] = 0xFFFF00
        else:
            neokey.pixels[1] = 0x0

        if neokey[2]: #Enter Button
            print("Button C") #Debug
            return column
            neokey.pixels[2] = 0x00FF00
        else:
            neokey.pixels[2] = 0x0

        if neokey[3]: #Move column selection to the left
            print("Button D") #Debug
            if column > 1:
                column -= 1 #Decrement column by 1
            else:
                column = column
            print(column)
            time.sleep(0.1)
            neokey.pixels[3] = 0x00FFFF #Controls RGB LED in the key
            lcd.clearScreen()
            lcd.setCursor(0,0)
            lcd.print("Column")
            lcd.setCursor(0,1)
            lcd.print(str(column)) #Upddate LCD to let user know what column is selected
        else:
            neokey.pixels[3] = 0x0

def TheirMove():
    """
    Reads console input for the digital player
    """
    #Would need to be adapted to use the API
    print("Their move")
    kit.servo[0].angle = 90 #Resets servo
    Move = input()
    if Move in ("W","w","L","l"):#Looks for a key to represent a win or loss condition. This functionality should probably be moved to a seperate function that is called once after either player makes a move.
        EndGame(Move)
        return False
    else:
        print(Move)
        print(bin(int(Move))) #Converts move to binary and displays it
        MakeMove(Move)
        kit.servo[0].angle = 0 #Opens gate
        time.sleep(0.15) #Short time for piece to fall through, adjust if pieces aren't able to get through or if more than one piece falls through
        kit.servo[0].angle = 90 #Close gate
        return True
    
def MakeMove(Move):
    """
    Function takes a string or int (Move) of a number between 0 and 7 and converts it to a 3 bit binary value. This value then controls the servo motors
    """
    print("Making Move") #Debug
    print(Move) #Debug
    Pos = ('{0:03b}'.format(int(Move))) #Convert Move into a binary value and then adjust the motor positions based on each bit
    print(Pos) #Debug
    print(type(Pos)) #Debug
    print(Pos[0]) #Debug
    print(Pos[1]) #Debug
    print(Pos[2]) #Debug
    
    if int(Pos[0]) == 1: #Looks at the first bit and adjusts the top motor based on that
        print("Top Motors in Pos 1") #Debug
        kit.servo[1].angle = 0
    else:
        print("Top Motors in Pos 0") #Debug
        kit.servo[1].angle = 175

    if int(Pos[1]) == 1: #Looks at the second bit and adjusts the middle motors based on that
        print("Mid Motors in Pos 1") #Debug
        kit.servo[2].angle = 0
        kit.servo[3].angle = 0
    else:
        print("Mid Motors in Pos 0") #Debug
        kit.servo[2].angle = 90
        kit.servo[3].angle = 90

    if int(Pos[2]) == 1: #Looks at the last bit and adjusts the bottom motors based on that
        print("Bot Motors in Pos 1") #Debug
        kit.servo[4].angle = 0
        kit.servo[5].angle = 0
        kit.servo[6].angle = 0
        kit.servo[7].angle = 0
    else:
        print("Bot Motors in Pos 0") #Debug
        kit.servo[4].angle = 175
        kit.servo[5].angle = 140
        kit.servo[6].angle = 140
        kit.servo[7].angle = 180
    time.sleep(1) #Short delay to allow motors to get into position, timing could be adjusted

def EndGame(Move):
    """
    Function takes a string move value and prints on an lcd if the player won or lost
    """
    print("Game ending")
    if Move in ("W","w"):
        print("You Win") #Debug
        lcd.clearScreen()
        lcd.setCursor(0,0)
        lcd.print("You Win")
    else:
        print("You Lose") #Debug
        lcd.clearScreen()
        lcd.setCursor(0,0)
        lcd.print("You Lose")
    ColourPicker()
    Reset()

def Reset():
    """
    Function to trigger the reset of the board
    """
    print("Reseting Board")
    main()
            
def ColourPicker():
    """
    Function used to take pictures of tokens and determine thier colour for sorting
    """

    #The bellow code is used for debuging using images saved to a folder instead of pictures taken by the camera
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
    
    
    for i in range(50): #The game board has 42 slots for tokens so at most there should be 42 pieces to sort, 50 gives a buffer incase a piece is not in place in time for the picture #This for loop is a poor way to do it because it will now take the same time to sort 10 pieces and 42 pieces, a system to detect if no piece is present may be better
        picam2.capture_file("token.jpg") #Takes picture of game piece and stores it as token.jpg
        kit.servo[8].angle = 90 #Sets the default angle of the servo
        time.sleep(1) #Give the system a small delay to allow the image to save. Could be adjusted
        Image_Colour = ColourTest()#Calls the colour test function
        print(Image_Colour)
        PieceColour = get_colour_name(Image_Colour)
        print(PieceColour)
        if PieceColour == "Red":
            kit.servo[8].angle = 0
            time.sleep(2)
        else:
            kit.servo[8].angle = 180
            time.sleep(2)
        
        
def colour_difference (colour1, colour2) -> int:
    """
    calculate the difference between two colours as sum of per-channel differences
    """
    return sum([abs(component1-component2) for component1, component2 in zip(colour1, colour2)])


def get_colour_name(colour) -> str:
    """
    guess color name using the closest match from KNOWN_COLOURS
    """
    differences =[
        [colour_difference(colour, known_colour), known_name]
        for known_name, known_colour in KNOWN_COLOURS.items()
    ]
    differences.sort()  # sorted by the first element of inner lists
    return differences[0][1]  # the second element is the name

def ColourTest():
    """
    Function reads a specific image to determine the colour
    """
    color_thief = ColorThief("token.jpg")
    dominant_color = color_thief.get_color(quality=1)
    return dominant_color

if __name__ == '__main__':
    main()

