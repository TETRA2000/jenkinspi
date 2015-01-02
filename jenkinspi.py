#!/usr/bin/env python
#-*- coding:utf-8 -*-

import time
import RPi.GPIO as GPIO
import multitask
import jenkinsapi
from jenkinsapi.jenkins import Jenkins

class Indicator(object):
	""" LED indicator """

	# flash mode
	MODE = ['continus', 'blink']

	# color
	# TODO: support more color using PDM
	COLOR = ['red', 'blue']

	def __init__(self, red_port, blue_port):
		self.running = False

		# default color, mode
		self.color = 'blue'
		self.mode = 'continus'

		self.red_port	= red_port
		self.blue_port	= blue_port

	def _init_GPIO(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(red_port, GPIO.OUT)
		GPIO.setup(blue_port, GPIO.OUT)

	def _cleanup_GPIO(self):
		GPIO.cleanup()

	def set_mode(self, mode):
		if mode.lower() in MODE:
			self.mode = mode.lower()

	def set_color(self, color):
		if color.lower() in COLOR:
			self.color = color.lower()

	def start(self):
		# stop last running
		self.stop()
		time.sleep(1)

		self.running = True
		multitask.add(self._flash_in_background())


	def stop(self):
		self.running = False

		self._cleanup_GPIO()

	def _flash_in_background(self):
		while self.running:
			if self.color == 'red':
				led = red_port
			else:
				led = blue_port

			GPIO.output(led, 1)

			if self.mode == 'blink':
				# turn off while...
				GPIO.output(led, 1)
				time.sleep(0.75)

			GPIO.output(led, 0)
			yield

class JenkinsPi(object):
	"""JenkinsPi"""
	def __init__(self, server_url, red_port, blue_port):
		self.indicator = Indicator(red_port=red_port, blue_port=blue_port)

		self.J = Jenkins(server_url)

		self.running = True
		
		multitask.add(self._background_task())
		multitask.run()

	# TODO: add the way to stop...
	
	def _background_task(self):
		while self.running:
			tasks = self.J.keys()
			if len(tasks) >0:
				has_failed_task = False
				has_building_task = False

				for task in tasks:
					build = self.J[task].get_latest_build()

					if not build.is_good():
						has_failed_task = True

					if build.is_running():
						has_building_task = True

				# priority: "Building" > "Failed" > "Normal"
				if has_building_task:
					self.indicator.set_color('blue')
					self.indicator.set_mode("blink")
				elif has_failed_task:
					self.indicator.set_color('red')
					self.indicator.set_mode("continus")
				else: # Normal
					self.indicator.set_color('blue')
					self.indicator.set_mode("continus")

			else:
				# no projects add something!!
				self.indicator.set_color('blue')
				self.indicator.set_mode("blink")

		yield self



if __name__ == '__main__':
	print('Jenkins Pi')

	JP = JenkinsPi(server_url='http://localhost:8080', red_port=3, blue_port=5)
	JP.start()
