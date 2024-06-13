
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

from kivy.config import Config
Config.set('graphics', 'width', SCREEN_WIDTH)
Config.set('graphics', 'height', SCREEN_HEIGHT)

from kivy.app import App
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.graphics.tesselator import Tesselator

from kivy.graphics.context_instructions import PushMatrix, PopMatrix
from kivy.graphics.context_instructions import Translate, Scale, Rotate

import sys, json

import random


color_cb_g1 = lambda a, b, r: Color(a, 0, b, mode = 'hsv')
color_cb_c1 = lambda a, b, r: Color(a, b, r)
color_cb_c2 = lambda a, b, r: Color(a, 1, 1, .3, mode = 'hsv')

def triangle_colors(regions, callback = None):
	rc = len(regions)
	tc = [ len(r['vvv']) for r in regions ]
	for r in range(rc):
		a = r / rc
		for t in range(tc[r]):
			b = t / tc[r]
			x = random.random()
			yield callback(a, b, x) if callback else a, b, x


def region_colors(regions, callback = None):
	rc = len(regions)
	for r in range(rc):
		a = r / rc
		b = 0
		x = random.random()
		yield callback(a, b, x) if callback else a, b, x


class TriangleColorizer:

	cb_bw = lambda a, b, r: Color(a, 0, b, mode = 'hsv')
	cb_color = lambda a, b, r: Color(a, b, r)

	def __init__(self, tt, callback = None):
		self.xx = tuple( len(t['vvv']) for t in tt )
		self.callback = callback
		# print(self.xx)
		self.reset()

	@property
	def ic(self):
		return len(self.xx)

	@property
	def jc(self):
		if self.i < self.ic:
			return self.xx[self.i]
		return 0

	def reset(self):
		self.i = 0
		self.j = 0

	def jnext(self):
		return next(self)

	def inext(self):
		# self.j = sys.maxsize
		# return next(self)
		if self.i < self.ic:
			self.j = self.jc
			return next(self)

	def __next__(self):
		if self.i >= self.ic:
			return

		if self.j >= self.jc:
			self.i += 1
			self.j = 0
			if self.i >= self.ic:
				return

		a = self.i / self.ic
		b = self.j / self.jc
		self.j += 1

		if not self.callback:
			return a, b, random.random()

		return self.callback(a, b, random.random())


class TtBbox:

	def __init__(self, tt):
		self.x, self.y, self.X, self.Y = sys.maxsize, sys.maxsize, 0, 0
		for t in tt:
			x, y, X, Y = t['bbox']
			self.x = min(self.x, x)
			self.y = min(self.y, y)
			self.X = max(self.X, X)
			self.Y = max(self.Y, Y)

	def __iter__(self):
		yield self.x
		yield self.y
		yield self.X
		yield self.Y

	@property
	def w(self):
		return self.X - self.x

	@property
	def h(self):
		return self.Y - self.y

	@property
	def c(self):
		return self.x + self.w / 2, self.y + self.h / 2

	@property
	def p(self):
		return self.x, self.y

	@property
	def s(self):
		return self.w, self.h


class ViewerWidget(BoxLayout):

	show_triangles = BooleanProperty(defaultvalue = False)
	show_triangle_colors = BooleanProperty(defaultvalue = True)
	show_background = BooleanProperty(defaultvalue = False)
	show_region_boundaries = BooleanProperty(defaultvalue = False)

	def on_size(self, _, size):
		self.stretch_factor = min(
			(size[0] - self.margin * 2) / self.bbox.w,
			(size[1] - self.margin * 2) / self.bbox.h
		)
		self.scaling_center = self.bbox.c

		self.xoff = (size[0] - self.bbox.w) / 2
		self.yoff = (size[1] - self.bbox.h) / 2

	def __init__(self, tt, **kk):
		super().__init__(**kk)

		self.tt = tt
		self.bbox = TtBbox(self.tt)

		self.meshes = []
		self.scale = None

		self.margin = 8
		self.update_method = 1

		self.stretch_factor = 1
		self.scaling_center = self.center
		self.xoff, self.yoff = 0, 0

		# TODO: We need this so we can set the scaling even
		#	before the first time we draw anything (which is
		#	when self.scale will be initialized).
		self._scale_factor = 1.

		# self.bind(pos = self.update, size = self.update)
		self.bind(size = self.update)
		self.bind(
			show_triangles = self.update,
			show_triangle_colors = self.update,
			show_region_boundaries = self.update)

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



		with self.canvas:
			PushMatrix()

			Translate(x = self.x + self.xoff, y = self.y + self.yoff)

			Scale(x = self.stretch_factor, y = self.stretch_factor,
				origin = self.scaling_center)

			# TODO: How do we pre-create a canvas command
			#	and simply add it to the canvas here? Here,
			#	this would allow us to remove self.scale_factor.
			self.scale = Scale(
				x = self.scale_factor, y = -self.scale_factor,
				origin = self.scaling_center)


			if self.show_background:
				Color(1, 1, 1)
				Rectangle(pos = self.bbox.p, size = self.bbox.s)


			if self.show_triangle_colors:
				tc = triangle_colors(self.tt, color_cb_c1)
			else:
				tc = triangle_colors(self.tt, color_cb_g1)


			for ti, t in enumerate(self.tt):

				if t['id'] == 'Srem':
					Color(1., .3, .3)
				else:
					Color(.8, .8, .3)

				for vv, ii in zip(t['vvv'], t['iii']):
					if self.show_triangles:
						next(tc)

					m = Mesh(
						vertices = vv,
						indices = ii,
						mode = "triangle_fan"
					)
					self.meshes.append(m)

				Color(0, 0, 0)
				Line(points = t['contour'])

		with self.canvas:
			if self.show_region_boundaries:
				tc = region_colors(self.tt, color_cb_c2)
				for t in self.tt:
					next(tc)
					x, y, X, Y = t['bbox']
					Rectangle(pos = (x, y), size = (X - x, Y - y))
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
			self.meshes = []
			self.canvas.clear()
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
		super().__init__(**kk)

		with self.canvas:
			Color(1, 1, 1, .3)
			self.bg = Rectangle(pos = self.pos, size = self.size)

		self.bind(size = self.update)

	def update(self, *aa, **kk):
		self.bg.pos = self.pos
		self.bg.size = self.size


class ControlWidget(BoxLayout):

	def __init__(self, **kk):
		kk.setdefault('size_hint', (1, None))
		kk.setdefault('height', '50sp')
		kk.setdefault('spacing', '8sp')
		super().__init__(**kk)

		with self.canvas:
			Color(1, 1, 1, .3)
			self.bg = Rectangle(pos = self.pos, size = self.size)

		self.bind(size = self.update)

	def update(self, *aa, **kk):
		self.bg.pos = self.pos
		self.bg.size = self.size


class Toggler(CheckBox):

	def __init__(self, viewer, prop, slave = None, **kk):
		# kk.setdefault('active', False)
		# kk.setdefault('disabled', False)
		super().__init__(**kk)

		self.viewer = viewer
		self.prop = prop
		self.slave = slave

		self.on = kk.setdefault('active', False)
		self.update_slave()

	def on_press(self, *aa):
		self.on = not self.on
		self.update_slave()

	def update_slave(self):
		if self.slave:
			self.slave.disabled = not self.on

	@property
	def on(self):
		return getattr(self.viewer, self.prop)

	@on.setter
	def on(self, value):
		setattr(self.viewer, self.prop, value)


class ColorControlWidget(BoxLayout):

	def __init__(self, viewer, **kk):
		self.viewer = viewer
		kk.setdefault('size_hint', (None, 1))
		kk.setdefault('width', '180sp')
		super().__init__(**kk)

		t = Toggler(self.viewer, 'show_triangle_colors', active = False)
		self.add_widget(Toggler(self.viewer, 'show_triangles', t))
		self.add_widget(t)
		self.add_widget(Toggler(self.viewer, 'show_region_boundaries'))


class ViewerApp(App):

	def on_slider_value_change(self, slider, value):
		self.viewer.scale_factor = value

	def build(self):
		with open('regions.json') as file:
			tt = json.load(file)

		self.viewer = ViewerWidget(tt)

		slider = MySlider(max = 2)
		slider.bind(value = self.on_slider_value_change)

		view = BoxLayout(orientation = 'vertical')

		control = ControlWidget()
		control.add_widget(slider)
		control.add_widget(ColorControlWidget(self.viewer))

		view.add_widget(self.viewer)
		view.add_widget(control)

		return view

if __name__ == '__main__':
	ViewerApp().run()
