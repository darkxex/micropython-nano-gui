# fpt.py Test/demo program for framebuf plot
# Uses Adafruit ssd1351-based OLED displays (change height to suit)
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673

# The MIT License (MIT)

# Copyright (c) 2018 Peter Hinch

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# WIRING (Adafruit pin nos and names)
# Pyb   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# X1    DC (3 DC)
# X2    CS (5 OC OLEDCS)
# X3    Rst (4 R RESET)
# X6    CLK (2 CL SCK)
# X8    DATA (1 SI MOSI)

height = 96  # 1.27 inch 96*128 (rows*cols) display
# height = 128 # 1.5 inch 128*128 display

import machine
import gc
from ssd1351 import SSD1351 as SSD

# Initialise hardware and framebuf before importing modules
pdc = machine.Pin('X1', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('X2', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('X3', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(1)
gc.collect()  # Precaution befor instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance

import cmath
import math
import utime
import uos
from writer import Writer, CWriter
from fplot import PolarGraph, PolarCurve, CartesianGraph, Curve, TSequence
from nanogui import Label, refresh
refresh(ssd)

# Fonts
import arial10, freesans20

GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255, 0, 0)
BLUE = SSD.rgb(0, 0, 255)
YELLOW = SSD.rgb(255, 255, 0)
WHITE = SSD.rgb(255, 255, 255)
BLACK = 0
LIGHTGREEN = SSD.rgb(0, 100, 0)

CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
wri.set_clip(True, True, False)

def cart():
    print('Cartesian data test.')
    def populate_1(func):
        x = -1
        while x < 1.01:
            yield x, func(x)  # x, y
            x += 0.1

    def populate_2():
        x = -1
        while x < 1.01:
            yield x, x**2  # x, y
            x += 0.1

    refresh(ssd, True)  # Clear any prior image
    g = CartesianGraph(wri, 2, 2, yorigin = 2, fgcolor=WHITE, gridcolor=LIGHTGREEN) # Asymmetric y axis
    curve1 = Curve(g, YELLOW, populate_1(lambda x : x**3 + x**2 -x,)) # args demo
    curve2 = Curve(g, RED, populate_2())
    refresh(ssd)

def polar():
    print('Polar data test.')
    def populate():
        def f(theta):
            return cmath.rect(math.sin(3 * theta), theta) # complex
        nmax = 150
        for n in range(nmax + 1):
            yield f(2 * cmath.pi * n / nmax)  # complex z
    refresh(ssd, True)  # Clear any prior image
    g = PolarGraph(wri, 2, 2, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curve = PolarCurve(g, YELLOW, populate())
    refresh(ssd)

def polar_clip():
    print('Test of polar data clipping.')
    def populate(rot):
        f = lambda theta : cmath.rect(1.15 * math.sin(5 * theta), theta) * rot # complex
        nmax = 150
        for n in range(nmax + 1):
            yield f(2 * cmath.pi * n / nmax)  # complex z
    refresh(ssd, True)  # Clear any prior image
    g = PolarGraph(wri, 2, 2, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curve = PolarCurve(g, YELLOW, populate(1))
    curve1 = PolarCurve(g, RED, populate(cmath.rect(1, cmath.pi/5),))
    refresh(ssd)

def rt_polar():
    print('Simulate realtime polar data acquisition.')
    refresh(ssd, True)  # Clear any prior image
    g = PolarGraph(wri, 2, 2, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curvey = PolarCurve(g, YELLOW)
    curver = PolarCurve(g, RED)
    for x in range(100):
        curvey.point(cmath.rect(x/100, -x * cmath.pi/30))
        curver.point(cmath.rect((100 - x)/100, -x * cmath.pi/30))
        utime.sleep_ms(60)
        refresh(ssd)

def rt_rect():
    print('Simulate realtime data acquisition of discontinuous data.')
    refresh(ssd, True)  # Clear any prior image
    g = CartesianGraph(wri, 2, 2, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curve = Curve(g, RED)
    x = -1
    for _ in range(40):
        y = 0.1/x if abs(x) > 0.05 else None  # Discontinuity
        curve.point(x, y)
        utime.sleep_ms(100)
        refresh(ssd)
        x += 0.05
    g.clear()
    curve = Curve(g, YELLOW)
    x = -1
    for _ in range(40):
        y = -0.1/x if abs(x) > 0.05 else None  # Discontinuity
        curve.point(x, y)
        utime.sleep_ms(100)
        refresh(ssd)
        x += 0.05
    

def lem():
    print('Lemniscate of Bernoulli.')
    def populate():
        t = -math.pi
        while t <= math.pi + 0.1:
            x = 0.5*math.sqrt(2)*math.cos(t)/(math.sin(t)**2 + 1)
            y = math.sqrt(2)*math.cos(t)*math.sin(t)/(math.sin(t)**2 + 1)
            yield x, y
            t += 0.1
    refresh(ssd, True)  # Clear any prior image
    Label(wri, 82, 2, 'To infinity and beyond...')
    g = CartesianGraph(wri, 2, 2, height = 75, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curve = Curve(g, YELLOW, populate())
    refresh(ssd)

def liss():
    print('Lissajous figure.')
    def populate():
        t = -math.pi
        while t <= math.pi:
            yield math.sin(t), math.cos(3*t)  # x, y
            t += 0.1
    refresh(ssd, True)  # Clear any prior image
    g = CartesianGraph(wri, 2, 2, fgcolor=WHITE, gridcolor=LIGHTGREEN)
    curve = Curve(g, YELLOW, populate())
    refresh(ssd)

def seq():
    print('Time sequence test - sine and cosine.')
    refresh(ssd, True)  # Clear any prior image
    # y axis at t==now, no border
    g = CartesianGraph(wri, 2, 2, xorigin = 10, fgcolor=WHITE,
                       gridcolor=LIGHTGREEN, bdcolor=False)
    tsy = TSequence(g, YELLOW, 50)
    tsr = TSequence(g, RED, 50)
    for t in range(100):
        g.clear()
        tsy.add(0.9*math.sin(t/10))
        tsr.add(0.4*math.cos(t/10))
        refresh(ssd)
        utime.sleep_ms(100)

seq()
utime.sleep(1.5)
liss()
utime.sleep(1.5)
rt_rect()
utime.sleep(1.5)
rt_polar()
utime.sleep(1.5)
polar()
utime.sleep(1.5)
cart()
utime.sleep(1.5)
polar_clip()
utime.sleep(1.5)
lem()
