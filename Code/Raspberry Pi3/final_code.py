import os, sys, pygame, time
from pygame.locals import *
import numpy as np
import RPi.GPIO as GPIO
import math
from math import pi
import serial

import FK, VK, IK

port = "/dev/ttyAMA0"

pos_offset = [0, 0, 5]
servo_ID1 = 0.0
servo_degree = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

## system flag
sysRunning_flag = True    # system Running flag
type_flag = True




def GPIO27_callback(channel):
    print ("")
    print "Button 27 pressed..."
    global sysRunning_flag
    sysRunning_flag = False
    print("System shut down")
    
GPIO.setmode(GPIO.BCM)   #set up GPIO pins
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

## add callback event
GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_callback, bouncetime=300)


try:
    while (sysRunning_flag):
        time.sleep(0.02)
        
        with open("/home/pi/OpenCV-red-circle-detection/positions.txt", "r") as f:
            lines = f.readlines()

            #if(lines != ""):
            #    a = np.fromstring((lines), dtype=float, sep=' ')
            #    print(a)
            #x, y, z = [float(x) for x in next(f).split()]
        f.close()
        s1 = serial.Serial('/dev/ttyACM0', 9600)
        s1.flushInput()
        
        length = len(lines)
        for i in range(0, length):
            a = np.fromstring((lines[i]), dtype=float, sep=' ')
            goal_position = [a[0], a[1], a[2]]    ## x, y, z should be converted to meters, like 0.025
            
            print("Goal position read: ", goal_position)
            
            ## FK service
            current_angles = [0, 0, 0, 0, 0]
            test_angle = [pi / 4, pi / 4, pi / 4, pi / 4,0]
            FK_result = FK.fk_srv(test_angle)
            print(FK_result)
            print("above is FK")
          
            ## VK service
            jac = VK.vk_srv(current_angles)
            print(jac)
            
            print("above is VK")
            
            
            ## IK service
            #goal_position = [FK_result[0, 3], FK_result[1, 3], FK_result[2, 3]]
            #goal_position = [0.175, 0, 0.08]
            rotating_angle = list(IK.ik_srv(goal_position))
            
            rotating_angle.append(servo_ID1)
            #rotating_angle[4] = -(rotating_angle[1] + rotating_angle[2] + rotating_angle[3]) + (pi / 2)
            rotating_angle[4] = 0
            print("rotating angle:", rotating_angle)
            
            for i in range(0, 3):
                servo_degree[i] = int(-(((rotating_angle[i] * 360) / (2 * pi)) / 0.24) - 0.5)
            servo_degree[3] = int((((rotating_angle[3] * 360) / (2 * pi)) / 0.24) + 0.5)
            servo_degree[4] = int((((rotating_angle[4] * 360) / (2 * pi)) / 0.24) + 0.5)
            servo_degree[5] = int((((rotating_angle[5] * 360) / (2 * pi)) / 0.24) + 0.5)
            
            print("servo degree:", servo_degree)
            ## serial communication 
            

            
            count = 0
            
            comp_list = ["Completed\r\n", "Hello Pi, This is Arduino UNO...:\r\n", "All completed\r\n"]
            done_signal = ["done\r\n"]
            while count < 6:
                if s1.inWaiting()>0:
                    inputValue = s1.readline()
                    print(inputValue)
                    if inputValue in comp_list:
                        try:
                            n = servo_degree[count]
                            print("Pi's pos and number:",count,n)
                            s1.write('%d'%n)
                            count = count+1
                        except:
                            print("Input error, please input a number")
                            s1.write('0')
            
            inputValue = s1.readline()
            while inputValue not in done_signal:
                inputValue = s1.readline()
        sysRunning_flag = False


except KeyboardInterrupt:
    GPIO.cleanup() # clean up GPIO on CTRL+C exit

print("exit")
GPIO.cleanup()
