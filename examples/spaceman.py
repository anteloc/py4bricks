#!/usr/bin/env python3
"""Example script demonstrating spaceman minifigure construction."""

import random

from py4bricks.figure import Person
from py4bricks.geometry import Identity, Vector, XAxis, YAxis, ZAxis
from py4bricks.library.colours import Blue, Green, Light_Green, Red, Yellow
from py4bricks.library.parts.minifig.torsos import TorsoWithClassicSpacePattern

random.seed(12345)

for x in range(-100, 200, 100):
    for z in range(-100, 200, 100):
        orientation = Identity()
        orientation = orientation.rotate(random.randrange(0, 360), XAxis)
        orientation = orientation.rotate(random.randrange(0, 360), YAxis)
        orientation = orientation.rotate(random.randrange(0, 360), ZAxis)
        figure = Person(position=Vector(x, 0, z), rotation=orientation)
        print(figure.head(colour=Yellow, angle=0))
        print(figure.torso(colour=Light_Green, part=TorsoWithClassicSpacePattern))
        print(figure.hips(colour=Blue))
        angle = random.randrange(-90, 60)
        print(figure.left_leg(colour=Red, angle=angle))
        angle = random.randrange(-90, 60)
        print(figure.right_leg(colour=Green, angle=angle))
        angle = random.randrange(-120, 60)
        print(figure.left_arm(colour=Red, angle=angle))
        angle = random.randrange(-90, 90)
        print(figure.left_hand(colour=Yellow, angle=angle))
        angle = random.randrange(-120, 60)
        print(figure.right_arm(colour=Green, angle=angle))
        angle = random.randrange(-90, 90)
        print(figure.right_hand(colour=Yellow, angle=angle))
