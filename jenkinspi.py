#!/usr/bin/env python
#-*- coding:utf-8 -*-

import time
import RPi.GPIO as GPIO
import jenkinsapi
from jenkinsapi.jenkins import Jenkins

class Indicator(object):
	""" LED indicator """

	BLINK_INTERVAL = 1

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

		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.red_port, GPIO.OUT)
		GPIO.setup(self.blue_port, GPIO.OUT)

	def flash(self, mode='continus', color='blue', duration=10):
			# turn off all LEDs
			GPIO.output(self.red_port, 0)
			GPIO.output(self.blue_port, 0)

			if color == 'red':
				led = self.red_port
			else:
				led = self.blue_port

			GPIO.output(led, 1)

			t0 = time.time()
			while time.time() - t0 < duration:
				if mode == 'blink':
					GPIO.output(led, 0)
					time.sleep(Indicator.BLINK_INTERVAL)
					GPIO.output(led, 1)
				else:
					time.sleep(1)


class JenkinsPi(object):
	"""JenkinsPi"""
	def __init__(self, server_url, red_port, blue_port):
		self.indicator = Indicator(red_port=red_port, blue_port=blue_port)

		self.J = Jenkins(server_url)

	def start(self):
		self.running = True
		
		self._background_task()

	# TODO: add the way to stop...
	
	def _background_task(self):

		while self.running:
			tasks = self.J.keys()
			if len(tasks) >0:
				has_failed_task = False
				has_building_task = False

				for task in tasks:
					build = self.J[task].get_last_build()

					if not build.is_good():
						has_failed_task = True

					if build.is_running():
						has_building_task = True

				# priority: "Building" > "Failed" > "Normal"
				if has_building_task:
					self.indicator.flash(mode='blink', color='blue', duration=10)
					print("building...")
				elif has_failed_task:
					self.indicator.flash(mode='continus', color='red', duration=10)

					print("failed")
				else: # Normal
					self.indicator.flash(mode='continus', color='blue', duration=10)

					print("normal")

			else:
				# no projects add something!!
				self.indicator.flash(mode='blink', color='red', duration=10)

				print ("no project")



if __name__ == '__main__':
	print('Jenkins Pi')

	JP = JenkinsPi(server_url='http://localhost:8080', red_port=3, blue_port=5)
	JP.start()
