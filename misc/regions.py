import sys, re

import svgpathtools


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800


def svgpath_minimal(path : svgpathtools.path.Path):
	mx, Mx, my, My = path.bbox()
	return complex(mx, my)


def svgpath_maximal(path : svgpathtools.path.Path):
	mx, Mx, my, My = path.bbox()
	return complex(Mx, My)


def svgpath_flip_vertical(path : svgpathtools.path.Path):
	M = svgpath_maximal(path)
	for i, line in enumerate(path):
		sr, si = line.start.real, line.start.imag
		er, ei = line.end.real, line.end.imag
		path[i] = svgpathtools.path.Line(
			complex(sr, M.imag - si), complex(er, M.imag - ei))
	return path


def svgpath_normalize(path : svgpathtools.path.Path):
	return path.translated(-svgpath_minimal(path))


def svgpath_fit_size(path : svgpathtools.path.Path, width, height):
	mx, Mx, my, My = path.bbox()
	sx = width / (Mx - mx)
	sy = height / (My - my)
	return path.scaled(min(sx, sy))


def svgpath_center(path : svgpathtools.path.Path, width, height):
	mx, Mx, my, My = path.bbox()
	x = (width - (Mx - mx)) / 2
	y = (height - (My - my)) / 2
	return path.translated(complex(x - mx, y - my))


class Path:

	def __init__(self, id = '', d = ''):
		self.id = id
		self.d = d
		self._path = None

	def __repr__(self):
		return self.__class__.__name__ + f'<"{self.id}">'

	@property
	def path(self):
		if not self._path:
			self._path = svgpathtools.parse_path(self.d)
			self._path = svgpath_flip_vertical(self._path)
		return self._path

	def normalize(self):
		self._path = svgpath_normalize(self.path)

	def fit(self, width, height):
		self._path = svgpath_fit_size(self.path, width, height)

	def center(self, width, height):
		self._path = svgpath_center(self.path, width, height)

	@classmethod
	def iter(cls, text):
		found = False
		for m in re.finditer(r'<path([^>]+)>', text, re.S):
			inner = m.group(1)

			m = re.search(r'id="([^"]+)"', inner, re.S)
			if not m: continue
			id = m.group(1)

			m = re.search(r'[^i]d="([^"]+)"', inner, re.S)
			if not m: continue
			d = m.group(1)

			yield cls(id, d)

	@classmethod
	def sorted(cls, paths):
		return sorted(paths, key = lambda path: path.id)

	@classmethod
	def find(cls, text, id):
		for obj in cls.iter(text):
			if obj.id == id:
				return obj

	@property
	def lines(self):
		for line in self.path:
			assert isinstance(line, svgpathtools.Line)
			yield line

	@property
	def points(self):
		prev = None
		for line in self.lines:
			assert prev is None or line.start == prev.end
			prev = line
			yield line.start.real, line.start.imag
		yield line.end.real, line.end.imag

	@property
	def contour(self):
		for x, y in self.points:
			yield x
			yield y


def show_paths(file):
	from kivy.config import Config
	Config.set('graphics', 'width', SCREEN_WIDTH)
	Config.set('graphics', 'height', SCREEN_HEIGHT)

	from kivy.app import App
	from kivy.uix.boxlayout import BoxLayout
	from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
	from kivy.uix.widget import Widget
	from kivy.uix.label import Label
	from kivy.uix.button import Button
	from kivy.graphics import Color, Rectangle, Mesh
	from kivy.graphics.tesselator import Tesselator


	class RegionWidget(BoxLayout):

		def __init__(self, path):
			super().__init__()

			self.margin = 16
			self.update_method = 1

			self.path = path
			# self.path.normalize()
			# self.path.fit(self.width - self.margin, self.height - self.margin)
			# self.path.center(self.width, self.height)

			self.draw_background()

			if self.update_tesselator():
				self.draw_meshes()

			# self.bind(pos = self.update, size = self.update)
			self.bind(size = self.update)

		@property
		def meshes(self):
			return [c for c in self.canvas.children if isinstance(c, Mesh)]

		def draw_background(self):
			with self.canvas:
				Color(1, 1, 1, .3)
				self.bg = Rectangle(pos = self.pos, size = self.size)

		def update_background(self):
			self.bg.pos = self.pos
			self.bg.size = self.size

		def clear_meshes(self):
			# FIXME: This assumes that no other meshes exist in the
			#	canvas other than the ones we've added.
			for m in self.meshes:
				self.canvas.remove(m)

		def draw_meshes(self):
			with self.canvas:
				Color(.8, .8, .3)
				for vertices, indices in self.tess.meshes:
					Mesh(
						vertices = vertices,
						indices = indices,
						mode = "triangle_fan"
					)

		def update_tesselator(self):
			tess = Tesselator()
			tess.add_contour(tuple(self.path.contour))
			if tess.tesselate():
				self.tess = tess
				return self.tess

		def update_meshes(self):
			# FIXME: This assumes that the meshes are all present
			#	in the exact order in which they had been added.
			# FIXME: Another assumption is that the previous Tesselator
			#	will be quietly released and garbage collected.

			vv_ii = self.tess.meshes
			mm = self.meshes

			for i, m in enumerate(mm):
				vv, ii = vv_ii[i]
				m.vertices = vv
				m.indices = ii

		def update(self, *aa):
			self.path.fit(self.width - self.margin, self.height - self.margin)
			self.path.center(self.width, self.height)

			if self.update_tesselator():

				if self.update_method == 1:
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


	class MeteoAlarmApp(App):
		def build(self):
			view = BoxLayout()
			tabs = BoxLayout(orientation = 'vertical', size_hint = (.3, 1))
			sm = ScreenManager(transition = FadeTransition(duration = 0))

			view.add_widget(tabs)
			view.add_widget(sm)

			def mkbtn(text):
				def on_press(index):
					sm.current = text
				b = Button(text = text)
				b.bind(on_press = lambda self: on_press(text))
				return b

			def mkscr(text, path):
				s = Screen(name = text)
				s.add_widget(RegionWidget(path))
				return s

			def addscr(text, path):
				tabs.add_widget(mkbtn(text))
				sm.add_widget(mkscr(text, path))

			with open('regions.svg') as file:
				for path in Path.sorted(Path.iter(file.read())):
					addscr(path.id, path)

			return view

	MeteoAlarmApp().run()


if __name__ == '__main__':
	with open('regions.svg') as file:
		show_paths(file)
