from ST7735 import TFT
from sysfont import sysfont
from machine import SPI, Pin, ADC
from framebuf import FrameBuffer, RGB565
import time
import math

#lcd module 160 x 128

WIDTH = 128
HEIGHT = 160
WHITE = TFT.WHITE
GREEN = TFT.BLUE

# pin layout - SPI1 SCK and SPI1 TX
# VCC - 3.3V - pin 36
# GND - GND
# DIN - MOSI - TX - pin 11
# CLK - SCK - pin 10
# CS - pin 13
# DC - pin 14
# RST - pin 15
# BL - dont have to use
# MISO - not used - pin 12

DIN_pin = 11
CLK_pin = 10
CS_pin = 13
DC_pin = 14
RST_pin = 15

spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(CLK_pin), mosi=Pin(DIN_pin), miso=Pin(12))
tft=TFT(spi, RST_pin, DC_pin, CS_pin)
tft.initr()
tft.rgb(True)
tft.fill(TFT.BLACK)

# adding screen buffer so tft.fill(TFT.BLACK) won't be needed - it caused screen flickering
buf = bytearray(128*160*2)
fb = FrameBuffer(buf, 128, 160, RGB565)
tft._setwindowloc((0,0),(127,159))

# adc
ADC2 = ADC(Pin(28))
ADC1 = ADC(Pin(27))
ADC0 = ADC(Pin(26))

x_axis = ADC2.read_u16() / 512
y_axis = ADC1.read_u16() / 410
zoom = ADC0.read_u16() / 32768

# variables to stabilize potentiometers output
stabilize = 0.9
stabilizeZoom = 0.8

build_btn = Pin(16, Pin.IN, Pin.PULL_DOWN)
build_led = Pin(17, Pin.OUT)
build_led.value(0)

def map(n, start1, stop1, start2, stop2):
    return ((n - start1)/(stop1 - start1)) * (stop2 - start2) + start2

def update_cords():
    global x_axis, y_axis, zoom
    x_axis = ((ADC2.read_u16() / 65535) - 0.5) * 5.5
    y_axis = ((ADC1.read_u16() / 65535) - 0.5) * 2.7
    zoom = ADC0.read_u16() / 65535

# mandelbrot
maxn = 40
def mandelbrot(c):
    z, n = 0, 0
    
    while(abs(z) <= 2 and n < maxn):
        z = z*z + c
        n += 1
    return n

xOffset = -0.8
RE_START = -2 + xOffset
RE_END = 2 + xOffset
IM_START = -1
IM_END = 1

def draw_fractal():  
    RE_START_OFF = RE_START + x_axis
    RE_WIDTH = RE_END - RE_START
    
    IM_START_OFF = IM_START + y_axis
    IM_WIDTH = IM_END - IM_START
    
    for x in range(WIDTH):
        xx = (RE_START_OFF + (x / WIDTH) * RE_WIDTH) * zoom  
        for y in range(HEIGHT):
            yy = (IM_START_OFF + (y / HEIGHT) * IM_WIDTH) * zoom * 2
            c = complex(xx, yy)
            m = mandelbrot(c)
            if m == maxn:
                color = 0
            else:
                bright = map(m, 0, maxn, 0, 1)
                color = int(map(math.sqrt(bright), 0, 1, 0x0000, 0xffff))
            
            fb.pixel(x, y, color)

while True:
    # graph
    update_cords()
    if build_btn.value() == 1:
        fb.fill(0)
        build_led.value(1)
        
        draw_fractal()
        
        build_led.value(0)
  
    # draw data
    # clear block with text
    fb.fill_rect(0, 0, WIDTH, 25, 0)
    # point to center
    fb.hline(0, int(HEIGHT/2), WIDTH, WHITE)
    fb.vline(int(WIDTH/2), 0, HEIGHT, WHITE)
    #generate text
    h = 5
    w = 5
    fb.text("x: %0.1f" % x_axis, w, h, WHITE)
    fb.text("y: %0.1f" % y_axis, w, h + sysfont["Height"], WHITE)
    fb.text("z: %0.1f" % zoom, int(WIDTH/2 + 10), 10, WHITE)
    
    tft._writedata(buf)
    time.sleep_ms(100)
 
