SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

from kivy.config import Config
Config.set('graphics', 'width', SCREEN_WIDTH)
Config.set('graphics', 'height', SCREEN_HEIGHT)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.graphics.tesselator import Tesselator

from kivy.graphics.context_instructions import PushMatrix, PopMatrix
from kivy.graphics.context_instructions import Translate, Scale, Rotate

import sys, json


class ViewerWidget(BoxLayout):

	def __init__(self, tt, **kk):
		super().__init__(**kk)

		self.tt = tt

		gx, gy, gX, gY = sys.maxsize, sys.maxsize, 0, 0
		for t in self.tt:
			x, y, X, Y = t['bbox']
			gx = min(gx, x)
			gy = min(gy, y)
			gX = max(gX, X)
			gY = max(gY, Y)
		self.bbox = [gx, gy, gX, gY]
		# print(self.bbox)

		self.margin = 32

		self.stretch_factor = min(
			(SCREEN_WIDTH - self.margin * 2) / (gX - gx),
			(SCREEN_HEIGHT - self.margin * 2) / (gY - gy)
		)

		self.scaling_center = (
			gx + (gX - gx) / 2,
			gy + (gY - gy) / 2,
		)

		self.meshes = []
		self.scale = None

		self.update_method = 1

		# TODO: We need this so we can set the scaling even
		#	before the first time we draw anything (which is
		#	when self.scale will be initialized).
		self._scale_factor = 1.

		# self.bind(pos = self.update, size = self.update)
		self.bind(size = self.update)

	@property
	def scale_factor(self):
		return self._scale_factor

	@scale_factor.setter
	def scale_factor(self, value):
		self._scale_factor = value
		if self.scale:
			self.scale.x = value
			self.scale.y = -value

	def draw_background(self):
		with self.canvas:
			Color(1, 1, 1, .3)
			self.bg = Rectangle(pos = self.pos, size = self.size)
			Color(1, 0, 0)

	def update_background(self):
		if not self.bg:
			self.draw_background()
		self.bg.pos = self.pos
		self.bg.size = self.size

	def clear_meshes(self):
		for m in self.meshes:
			self.canvas.remove(m)
		self.meshes = []

	def draw_meshes(self):
		assert len(self.meshes) == 0

		gx, gy, gX, gY = self.bbox
		gw, gh = gX - gx, gY - gy
		xoff, yoff = (SCREEN_WIDTH - gw) / 2, (SCREEN_HEIGHT - gh) / 2

		with self.canvas:
			PushMatrix()

			# Translate(x = -self.bbox[0], y = -self.bbox[1])

			Translate(x = xoff, y = yoff)

			Scale(x = self.stretch_factor, y = self.stretch_factor,
				origin = self.scaling_center)


			# TODO: How do we pre-create a canvas command
			#	and simply add it to the canvas here? Here,
			#	this would allow us to remove self.scale_factor.
			self.scale = Scale(
				x = self.scale_factor, y = -self.scale_factor,
				origin = self.scaling_center)

			for t in self.tt:
				# print(t['id'])

				if t['id'] == 'Srem':
					Color(1., .3, .3)
				else:
					Color(.8, .8, .3)

				for vv, ii in zip(t['vvv'], t['iii']):
					m = Mesh(
						vertices = vv,
						indices = ii,
						mode = "triangle_fan"
					)
					self.meshes.append(m)

				Color(0, 0, 0)
				Line(points = t['contour'])

			PopMatrix()

	def update_tesselator(self):
		tess = Tesselator()
		tess.add_contour(tuple(self.path.contour))
		if tess.tesselate():
			self.tess = tess
			return self.tess

	def update_meshes(self):
		if not self.meshes:
			self.draw_meshes()

		# The first RegionWidget will be made visible when its
		#	window size is not yet determined (and defaults to
		#	[100, 100]). This means that we need to keep a ref
		#	to our scaling matrix so we can update its origin.
		#	Relevant only to update_method == 3.
		assert self.scale
		self.scale.origin = self.center

		# TODO: This method assumes that the previous Tesselator
		#	will be quietly released and garbage collected,
		#	otherwise we'll leak resources.
		# NOTE: This method is called after update_tesselator(),
		#	and the vv and ii of tess.meshes are memoryviews.
		assert len(self.meshes) == len(self.tess.meshes)
		for m, vv_ii in zip(self.meshes, self.tess.meshes):
			m.vertices = vv_ii[0]
			m.indices = vv_ii[1]

	def update(self, *aa):
		if self.update_method == 1:
			self.canvas.clear()
			self.meshes = []
			self.draw_background()
			self.draw_meshes()

		elif self.update_method == 2:
			self.update_background()
			self.clear_meshes()
			self.draw_meshes()

		elif self.update_method == 3:
			self.update_background()
			self.update_meshes()

class MySlider(Slider):
	def __init__(self, **kk):
		kk.setdefault('min', .025)
		kk.setdefault('max', 1.)
		kk.setdefault('step', .025)
		kk.setdefault('value', 1.)
		kk.setdefault('size_hint', (1, None))
		kk.setdefault('height', 50)
		super().__init__(**kk)

		with self.canvas:
			Color(1, 1, 1, .3)
			self.bg = Rectangle(pos = self.pos, size = self.size)

		self.bind(size = self.update)

	def update(self, *aa, **kk):
		self.bg.pos = self.pos
		self.bg.size = self.size


class ViewerApp(App):

	def on_slider_value_change(self, slider, value):
		self.viewer.scale_factor = value

	def build(self):
		with open('regions.json') as file:
			tt = json.load(file)

		self.viewer = ViewerWidget(tt)

		self.slider = MySlider()
		self.slider.bind(value = self.on_slider_value_change)

		view = BoxLayout(orientation = 'vertical')
		view.add_widget(self.viewer)
		view.add_widget(self.slider)
		return view

if __name__ == '__main__':
	ViewerApp().run()
