from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import DictProperty
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.image import Image

from kivy.gesture import GestureDatabase, Gesture

import os

import scraper


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
		print('gesture')
		if match[1].name == 'refresh':
			self.on_refresh_gesture(match)

	def on_refresh_gesture(self, match):
		pass


class MapView(GestureWidget):

	warnings = DictProperty()

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

		self.bind(
			pos = self.on_pos_change,
			size = self.on_size_change,
			warnings = self.on_warnings_change)

		self.warnings = self.fetch_warnings()

	def on_warnings_change(self, *aa):
		for id, ww in self.warnings.items():
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

	@classmethod
	def fetch_warnings(cls, dt = None, cache_root = '.'):
		cache = scraper.Cache(root = cache_root)
		url = scraper.mkurl(dt)
		text = cache.fetch(url, maxage = 3600)
		rr = scraper.iter_regions(text)
		# rr = list(rr); print(rr)
		return { r[0] : r[1] for r in rr }

	def on_refresh_gesture(self, match):
		self.warnings = self.fetch_warnings()


class MapApp(App):

	def __init__(self, **kk):
		super().__init__(**kk)

	def build(self):
		self.view = MapView()
		return self.view


if __name__ == '__main__':
	MapApp().run()
