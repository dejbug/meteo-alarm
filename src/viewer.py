
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800

from kivy.config import Config
Config.set('graphics', 'width', SCREEN_WIDTH)
Config.set('graphics', 'height', SCREEN_HEIGHT)
Config.set('input', 'mouse', 'mouse,disable_multitouch')
# Config.set('input', 'mouse', 'mouse,disable_on_activity')

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.graphics.transformation import Matrix
from kivy.graphics.context_instructions import PushMatrix, PopMatrix, MatrixInstruction

import sys, json, random

import regions


color_cb_g1 = lambda a, b, r: Color(a, 0, b, mode = 'hsv')
color_cb_c1 = lambda a, b, r: Color(a, b, r)
color_cb_c2 = lambda a, b, r: Color(a, 1, 1, .3, mode = 'hsv')


def triangle_colors(regions, callback = None):
	rc = len(regions)
	for i, r in enumerate(regions):
		a = i / rc
		tc = len(r['vvv'])
		for t in range(tc):
			b = t / tc
			x = random.random()
			yield callback(a, b, x) if callback else (a, b, x)


def region_colors(regions, callback = None):
	rc = len(regions)
	for r in range(rc):
		a = r / rc
		b = 0
		x = random.random()
		yield callback(a, b, x) if callback else (a, b, x)


class BBox:

	def __init__(self, x = 0, y = 0, X = 0, Y = 0):
		self.x, self.y, self.X, self.Y = x, y, X, Y

	def __repr__(self):
		return f'BBox[{self.x:8.3f} {self.y:8.3f} {self.X:8.3f} {self.Y:8.3f}]'

	@classmethod
	def from_regions(cls, tt):
		self = cls(sys.maxsize, sys.maxsize, 0, 0)
		for t in tt:
			x, y, X, Y = t['bbox']
			self.x = min(self.x, x)
			self.y = min(self.y, y)
			self.X = max(self.X, X)
			self.Y = max(self.Y, Y)
		return self

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

	def contains(self, x, y):
		return x >= self.x and x <= self.X and y >= self.y and y <= self.Y


class ViewerWidget(BoxLayout):

	show_triangles = BooleanProperty()
	show_triangle_colors = BooleanProperty()
	show_region_boundaries = BooleanProperty()

	show_background = BooleanProperty()

	def on_size(self, _, size):
		self.bg.pos = self.pos
		self.bg.size = self.size

		self.stretch_factor = min(
			(size[0] - self.margin * 2) / self.bbox.w,
			(size[1] - self.margin * 2) / self.bbox.h
		)

		self.zoom = self._zoom # update scaling (with new stretch_factor)

	@property
	def zoom(self):
		return self._zoom

	@zoom.setter
	def zoom(self, value):
		self._zoom = value

		self.matrix.identity()

		self.matrix.translate(
			self.center[0] - self.bbox.w / 2 - self.bbox.x,
			self.center[1] - self.bbox.h / 2 - self.bbox.y, 0)

		# The bbox is flush with the vertices. We need
		#	the document size here.
		# TODO: Extract it from the SVG:
		#	viewBox="0 0 210 297".
		dbox = BBox(0, 0, 210, 297)

		self.matrix.translate(0, dbox.h, 0)
		self.matrix.scale(1, -1, 1)

		zoom = self._zoom * self.stretch_factor

		self.matrix.scale(zoom, zoom, 1)
		self.matrix.translate(
			-self.bbox.x * (zoom - 1),
			 self.bbox.y * (zoom - 1), 0)

		self.matrix.translate(
			-zoom * self.bbox.w / 2,
			 zoom * self.bbox.h / 2, 0)
		self.matrix.translate(self.bbox.w / 2, -self.bbox.h / 2, 0)

		self.matrix_inverse = self.matrix.inverse()

		self.transformation.matrix = self.matrix

	def __init__(self, tt, **kk):
		super().__init__(**kk)

		self.tt = tt
		self.bbox = BBox.from_regions(self.tt)

		self.margin = 8

		self._zoom = 1
		self.matrix = Matrix()
		self.matrix_inverse = self.matrix.inverse()
		self.transformation = MatrixInstruction(matrix = self.matrix)

		self.tcolors = { }
		self.bcolors = { }
		self.fans = { }

		self.init_canvas()
		self.bind(
			size = self.update_canvas,
			show_triangles = self.update_canvas,
			show_triangle_colors = self.update_canvas,
			show_region_boundaries = self.update_canvas)

	def init_canvas(self, *aa):

		assert not self.tcolors
		assert not self.bcolors

		with self.canvas:

			self.bg_color = Color(1, 1, 1, 0)
			self.bg = Rectangle()

			PushMatrix()
			self.canvas.add(self.transformation)

			for t in self.tt:
				tc = self.tcolors[t['id']] = []

				self.fans[t['id']] = fans = []

				for vv, ii in zip(t['vvv'], t['iii']):
					fans.append(regions.Fan(vv, ii))

					tc.append(Color())
					Mesh(
						vertices = vv,
						indices = ii,
						mode = "triangle_fan"
					)

				Color(0, 0, 0)
				Line(points = t['contour'])

			for t in self.tt:
				self.bcolors[t['id']] = Color()
				bbox = BBox(*t['bbox'])
				Rectangle(pos = bbox.p, size = bbox.s)

			PopMatrix()

	def update_canvas(self, *aa):

		if self.show_background:
			self.bg_color.a = .3
		else:
			self.bg_color.a = 0

		if self.show_triangles:

			if self.show_triangle_colors:
				CC = triangle_colors(self.tt, color_cb_c1)
			else:
				CC = triangle_colors(self.tt, color_cb_g1)

			for id, cc in self.tcolors.items():
				for c in cc:
					c.rgba = next(CC).rgba
		else:

			for id, cc in self.tcolors.items():

				if id == 'Srem':
					C = Color(1., .3, .3)
				else:
					C = Color(.8, .8, .3)

				for c in cc:
					c.rgba = C.rgba

		if self.show_region_boundaries:

			cc = region_colors(self.tt, color_cb_c2)
			for k, c in self.bcolors.items():
				c.rgba = next(cc).rgba
		else:

			for k, c in self.bcolors.items():
				c.a = 0


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
		kk.setdefault('color', (0, 0, 0, 1))
		super().__init__(**kk)

		self.viewer = viewer
		self.prop = prop
		self.slave = slave

		self.margin = kk.setdefault('margin', 0)
		self.on = kk.setdefault('active', False)

		self.update_slave()

		with self.canvas.before:
			self.bg = Color(1, 1, 1, .1)
			self.rc = Rectangle(pos = self.pos, size = self.size)

		self.bind(disabled = self.update)
		self.bind(pos = self.update, size = self.update)

	def update(self, *aa):
		self.bg.a = .1 if self.disabled else .3
		self.rc.pos = (
			self.x + self.margin,
			self.y + self.margin
		)
		self.rc.size = (
			self.width - self.margin - self.margin,
			self.height - self.margin - self.margin
		)

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

		t = Toggler(self.viewer, 'show_triangle_colors', active = True)
		self.add_widget(Toggler(self.viewer, 'show_triangles', t))
		self.add_widget(t)
		self.add_widget(Toggler(self.viewer, 'show_region_boundaries'))


class ViewerApp(App):

	def on_mouse_down(self, win, x, y, button, modifiers):
		# print(x, y, button, modifiers)
		if not self.button:
			self.button = button

	def on_mouse_up(self, win, x, y, button, modifiers):
		# print(x, y, button, modifiers)
		self.button = None

	def on_motion(self, win, etype, me):
		# print(etype, me)
		x = (self.viewer.width + self.viewer.x) * me.sx
		y = (self.viewer.height + self.viewer.y) * me.sy

		x, y, _ = self.viewer.matrix_inverse.transform_point(x, y, 0)

		if not self.viewer.show_region_boundaries and not self.button:

			id_bb_s = ( ( t['id'], BBox(*t['bbox']) ) for t in self.viewer.tt )

			if self.viewer.show_triangles:

				done = False

				if self.last_fan:
					if self.last_fan.contains(x, y):
						done = True
					else:
						self.last_fan = None
						self.last_fan_color.rgba = self.last_fan_rgba
						# self.last_fan_color = None
						# self.last_fan_rgba = None

				RGBA = (0, 0, 0, 1) if self.viewer.show_triangle_colors else (1, 0, 0, 1)

				for id, bb in id_bb_s:
					if done: break
					if not bb.contains(x, y): continue

					cc = iter(self.viewer.tcolors[id])
					fans = self.viewer.fans[id]
					for fan in fans:
						c = next(cc)
						if fan.contains(x, y):
							self.last_fan = fan
							self.last_fan_color = c
							self.last_fan_rgba = c.rgba
							c.rgba = RGBA
							done = True
							break

			else:

				for id, bb in id_bb_s:
					c = self.viewer.bcolors[id]
					if bb.contains(x, y):
						c.a = .3
					else:
						c.a = 0

		else:

			if x < self.viewer.x: return
			if y < self.viewer.y: return

			# self.viewer.translate.x = x - self.viewer.bbox.c[0]
			# self.viewer.translate.y = y - self.viewer.bbox.c[1]

	def on_slider_value_change(self, slider, value):
		self.viewer.zoom = value

	def __init__(self, **kk):
		super().__init__(**kk)
		self.button = None
		self.last_fan = None
		self.last_fan_color = None
		self.last_fan_rgba = None

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

		Window.bind(on_motion = self.on_motion)
		Window.bind(on_mouse_down = self.on_mouse_down)
		Window.bind(on_mouse_up = self.on_mouse_up)

		return view

if __name__ == '__main__':
	ViewerApp().run()
