__version__ = '1.0.0'

import kivy
kivy.require('2.3.0')

from kivy.config import Config
if kivy.platform != 'android':
	Config.set('graphics', 'width', 400)
	Config.set('graphics', 'height', 600)
	Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
# from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
# from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.gesture import GestureDatabase, Gesture
from kivy.storage.jsonstore import JsonStore

import sys, os, re, time, datetime, threading

import scraper

from Warnings import Warnings


class AsyncWarningsFetcher:

	def __init__(self):
		self.runner = None
		self.warnings = None

	@property
	def running(self):
		return self.runner is not None

	@property
	def ok(self):
		return self.warnings is not None

	def start(self, dt = None):
		if self.runner:
			return False
		self.runner = threading.Thread(target = self.run, args = (dt, ), daemon = True)
		self.runner.start()
		return True

	def run(self, dt = None):
		self.warnings = Warnings.fetch(dt)
		self.runner = None


class AsyncRefresher:

	MAXAGE = 3600

	STATE_OK_CACHED = 4

	def __init__(self, view, store = 'store.json'):
		assert isinstance(view, MapView)
		self.view = view
		self.store = store
		self.fetcher = None
		self.timer = None
		self.start_time = 0

	@property
	def running(self):
		return self.fetcher

	@property
	def seconds(self):
		return time.time() - self.start_time if self.start_time > 0 else 0

	def start(self):
		if self.fetcher:
			return False

		warnings = Warnings.load(self.store)
		if warnings:
			if warnings.age < self.MAXAGE:
				self.view.on_fetch_result(warnings, True)
				return True

		self.start_time = time.time()
		self.fetcher = AsyncWarningsFetcher()
		self.fetcher.start()
		self.view.on_fetch_start()
		self.timer = Clock.schedule_interval(self.on_timer, 0.25)
		return True

	def cancel(self):
		self.fetcher = None

	def on_timer(self, *aa):
		if self.fetcher:
			if self.fetcher.running:
				self.view.on_fetch_tick(time.time() - self.start_time)
			else:
				self.view.on_fetch_result(self.fetcher.warnings, False)
				if self.fetcher.warnings:
					self.fetcher.warnings.save(self.store)
				self.fetcher = None

		if not self.fetcher:
			self.timer.cancel()
			self.timer = None


class MapImages:

	RIDS = ['ba', 'bc', 'bg', 'is', 'ji', 'jz', 'km', 'po', 'sr', 'su', 'zs']

	WIDTH = 346
	HEIGHT = 504
	RATIO = WIDTH / HEIGHT

	@classmethod
	def path(cls, id, severity = '%d', root = 'img'):
		# return os.path.join(root, f'{id}_{severity}.gif')
		return os.path.join(root, f'png/{id}.png')

	@classmethod
	def paths(self, severity = '%d', root = 'img'):
		for id in cls.RIDS:
			yield id, cls.path(id, severity, root)

	@classmethod
	def size(cls, id = 'ba', severity = 1, root = 'img'):
		from kivy.core.image import Image as CoreImage
		path = cls.path(id, severity, root)
		return CoreImage(path).size


class GestureWidget(Widget):

	def __init__(self, **kk):
		super().__init__(**kk)

		self.gestures = GestureDatabase()
		gesture = self.gestures.str_to_gesture(b'eNprYJkqz8YABj082ZlllXrpqcUlpUWpU3rY3aGsyVM0G6fUTtHoYS3PTCnJmOLuIAPVwZaRmpmeUQIUKWyAiPBDtccXFOWnlCaDpNi1FFnOVZzrYS8uKcrPTi2eEjslg6GHF2p6MFgQYQdbQX5mXglIkQZQFQ9UVQBIEKGIsWKK+/6227nbbuc19DBWTnG3fyQv+jFe9EtpUoYgRE2GCFxFhqi7/YO7jldkHa/glL/XHlDKHlCBU/625EwgmEO2/BXmFVbNKxwGTP74JE+VSZ4aAyZfBmYyDC75AmCUl3IyAOX3H/+xvuvH+o5hJW/fCpRm9wfLX40G+j93B33le8KP1oQfAYX//psVIPf1kC1/ay4o/14qTUrt4SlOLkpNzUOUE+4OlQagwofR3aFmAZjRNgVZLAFcNKGIVX/AIiaAKValgClWYYBpRykW84ouIMQCoGJ5DxBiE8BMd4fM/f9BACy2AKouvR5TLA1JL1xsARaxBixiCQg3w8UcoGKppUmJPZwl+TmpRYl5yanA0nQnqDCbOauHJS8xF1gTMEwpTdIDAIT1WkI=')
		gesture.name = 'refresh'
		self.gestures.add_gesture(gesture)

	def on_touch_down(self, touch):
		touch.ud['gesture_path'] = [(touch.x, touch.y)]
		super().on_touch_down(touch)

	def on_touch_move(self, touch):
		touch.ud['gesture_path'].append((touch.x, touch.y))
		super().on_touch_move(touch)

	def on_touch_up(self, touch):
		if 'gesture_path' in touch.ud:
			gesture = Gesture()
			gesture.add_stroke(touch.ud['gesture_path'])
			gesture.normalize()
			match = self.gestures.find(gesture, minscore = 0.9)
			if match:
				self.on_gesture(match)
		super().on_touch_up(touch)

	def on_gesture(self, match):
		if match[1].name == 'refresh':
			self.on_refresh_gesture(match)

	def on_refresh_gesture(self, match):
		pass


class MapView(GestureWidget):

	status = StringProperty()
	warnings = ObjectProperty()

	def __init__(self, **kk):
		super().__init__(**kk)

		self.regions = {}
		self.region_colors = {}

		self.warning_colors = [
			(1, 1, 1, .5),
			(0, 1, 0, 1),
			(1, 1, 0, 1),
			(.9, .6, 0, 1),
			(.9, .1, 0, 1),
		]

		with self.canvas:
			Color(1, 1, 1, .4)
			self.bg = Rectangle(pos = self.pos, size = self.size)

			for id in MapImages.RIDS:
				path = MapImages.path(id, 1)
				self.region_colors[id] = Color(1, 1, 1, 1)
				self.regions[id] = Rectangle(source = path, pos = self.pos, size = self.size)

		# self.register_event_type('on_refresh_ok')

		self.bind(
			pos = self.on_pos_change,
			size = self.on_size_change,
			warnings = self.on_warnings_change)

		# Window.bind(on_mouse_down = self.on_mouse_down)

		self.refresher = AsyncRefresher(self)
		self.refresher.start()

	# def on_refresh_ok(self, *aa):
	# 	self.warnings = self.fetcher.warnings

	def on_fetch_start(self):
		print('AsyncRefresher: starting')

	def on_fetch_tick(self, seconds):
		print(f'AsyncRefresher: tick {seconds}')

	def on_fetch_result(self, warnings, cached):
		print('AsyncRefresher: result', f'({warnings.age if warnings and cached else None})')
		if warnings:
			self.warnings = warnings

	def on_warnings_change(self, *aa):
		for id, ww in self.warnings.warnings.items():
			highest_severity = ww[-1][-1] if ww else 1
			# print(id, ww, highest_severity)
			self.set_region_warning(id, highest_severity)

	def on_pos_change(self, *aa):
		pass

	def on_size_change(self, *aa):
		self.bg.pos = self.pos
		self.bg.size = self.size

		w, h = self.region_image_size
		for r in self.regions.values():
			# r.pos = (self.size[0] - w) / 2, (self.size[1] - h) / 2
			r.pos = (self.pos[0], self.size[1] - h)
			r.size = (w, h)

	# def on_mouse_down(self, win, x, y, button, modifiers):
	# 	print(x, y, button, modifiers)

	def set_region_color(self, id, rgba):
		self.region_colors[id].rgba = rgba

	def set_region_warning(self, id, severity = 0):
		self.set_region_color(id, self.warning_colors[severity])

	@property
	def region_image_size(self):
		w, h = self.size
		R = w / h
		r = MapImages.RATIO

		if r < R:
			w = h * r
		elif r > R:
			h = w / r

		return w, h

	def on_refresh_gesture(self, match):
		# self.refresher.cancel()
		self.refresher.start()


class MapApp(App):

	def __init__(self, **kk):
		super().__init__(**kk)

	def build(self):
		self.info = Label(text = '', pos_hint = {'right': .9, 'top': 1}, size_hint = (.1, .1))
		self.view = MapView()

		layout = FloatLayout()
		layout.add_widget(self.info)
		layout.add_widget(self.view)

		self.view.bind(status = self.on_view_status_change)

		return layout

	def on_view_status_change(self, widget, text):
		self.info.text = text


if __name__ == '__main__':
	MapApp().run()
