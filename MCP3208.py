import platform
import os
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
# ok, I don't want this to work in travis.ci env or on anything other than linux

class MCP3208(object):
	def __init__(self,clk=None, cs=None, miso=None, mosi=None):
		gpio = GPIO.get_platform_gpio()
		self.spi = SPI.BitBang(gpio, clk, mosi, miso, cs)
		self.spi.set_clock_hz(1000000)
		self.spi.set_mode(0)
		self.spi.set_bit_order(SPI.MSBFIRST)


	def read(self, ch):
		if 7 <= ch <= 0:
			raise Exception('MCP3208 channel must be 0-7: ' + str(ch))

		cmd = 128  # 1000 0000
		cmd += 64  # 1100 0000
		cmd += ((ch & 0x07) << 3)
		ret = self.spi.transfer([cmd, 0x0, 0x0])

		# get the 12b out of the return
		val = (ret[0] & 0x01) << 11  # only B11 is here
		val |= ret[1] << 3           # B10:B3
		val |= ret[2] >> 5           # MSB has B2:B0 ... need to move down to LSB

		return (val & 0x0FFF)  # ensure we are only sending 12b
