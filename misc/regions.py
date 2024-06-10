import sys, re

import svgpathtools


def svgpath_minimal(path : svgpathtools.path.Path):
	mx, Mx, my, My = path.bbox()
	return complex(mx, my)


def svgpath_maximal(path : svgpathtools.path.Path):
	mx, Mx, my, My = path.bbox()
	return complex(Mx, My)


def svgpath_normalize(path : svgpathtools.path.Path):
	return path.translated(-svgpath_minimal(path))


def svgpath_flip_vertical(path : svgpathtools.path.Path):
	M = svgpath_maximal(path)
	for i, line in enumerate(path):
		sr, si = line.start.real, line.start.imag
		er, ei = line.end.real, line.end.imag
		path[i] = svgpathtools.path.Line(
			complex(sr, M.imag - si), complex(er, M.imag - ei))
	return path


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
			# self._path = self._path.scaled(10.0)

			self._path = svgpath_normalize(self._path)
			self._path = svgpath_flip_vertical(self._path)

			M = svgpath_maximal(self._path)
			fr = 800 / M.real
			fi = 640 / M.imag
			self._path = self._path.scaled(min(fr, fi))

		return self._path

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


def write_to_nodefile(path, file = sys.stdout):
	# For use with <http://www.cs.cmu.edu/~quake/triangle.html>
	# But it turns out that Kivy has a tesselator, too.

	pp = tuple(path.points)

	print(len(pp), 2, 0, 0)
	for i, p in enumerate(pp, start = 1):
		file.write(f'{i} {p[0]} {p[1]}\n')

	print(len(pp) - 1, 0)
	for i in range(1, len(pp) + 1):
		file.write(f'{i} {i + 1}\n')


def iter_meshes(path):
	from kivy.graphics.tesselator import Tesselator
	from kivy.graphics import Mesh

	tess = Tesselator()
	tess.add_contour(tuple(path.contour))

	ok = tess.tesselate()
	assert ok

	for vertices, indices in tess.meshes:
		yield Mesh(
			vertices = vertices,
			indices = indices,
			mode = "triangle_fan"
		)

def show_meshes(meshes):
	from kivy.config import Config
	Config.set('graphics', 'width', 800)
	Config.set('graphics', 'height', 640)

	from kivy.app import App
	from kivy.uix.widget import Widget
	from kivy.graphics import Color

	class MyApp(App):
		def build(self):
			widget = Widget()
			# with widget.canvas:
				# Color(1, 1, 1)
				# Rectangle(pos = (10, 10), size = (100, 100))
			widget.canvas.add(Color(.8, .8, .3))
			for mesh in meshes:
				widget.canvas.add(mesh)
			return widget

	MyApp().run()


def show_region(file, id):
	path = Path.find(file.read(), id)
	# print(path)
	meshes = iter_meshes(path)
	# print(meshes)
	show_meshes(meshes)


def show_paths(file):
	paths = tuple(Path.iter(file.read()))

	from kivy.config import Config
	Config.set('graphics', 'width', 1200)
	Config.set('graphics', 'height', 800)

	from kivy.app import App
	from kivy.uix.boxlayout import BoxLayout
	from kivy.uix.screenmanager import ( ScreenManager, Screen,
		FallOutTransition, NoTransition )
	from kivy.uix.widget import Widget
	from kivy.uix.label import Label
	from kivy.uix.button import Button
	from kivy.graphics import Color, Rectangle

	from kivy.graphics.tesselator import Tesselator
	from kivy.graphics import Mesh


	class RegionWidget(BoxLayout):

		def __init__(self, path):
			super().__init__()

			# self.add_widget(Label(text = text))

			self.tess = Tesselator()
			self.tess.add_contour(tuple(path.contour))
			ok = self.tess.tesselate()
			assert ok

			with self.canvas:
				Color(1, 1, 1, .3)
				self.bg = Rectangle(pos = self.pos, size = self.size)
				Color(.8, .8, .3)

				for vertices, indices in self.tess.meshes:
					Mesh(
						vertices = vertices,
						indices = indices,
						mode = "triangle_fan"
					)

			self.bind(pos = self.update, size = self.update)

		def update(self, *aa):
			self.bg.pos = self.pos
			self.bg.size = self.size


	class MyApp(App):
		def build(self):
			with open('regions.svg') as file:
				paths = tuple(Path.iter(file.read()))

			view = BoxLayout(orientation = 'vertical')

			tabs = BoxLayout(orientation = 'horizontal',
				size_hint = (1, None), height = 30)

			# sm = ScreenManager(transition = NoTransition())
			sm = ScreenManager(transition = FallOutTransition())

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

			for path in paths:
				addscr(path.id, path)


			# def on_tabs_resize(self, size):
			# 	with self.canvas.before:
			# 		Color(1, 1, 1)
			# 		Rectangle(pos = self.pos, size = self.size)
			# tabs.bind(size = on_tabs_resize)

			# widget.canvas.add(Color(.8, .8, .3))
			# for mesh in meshes:
			# 	widget.canvas.add(mesh)

			return view

	MyApp().run()


if __name__ == '__main__':

	with open('regions.svg') as file:
		show_paths(file)
		exit()

		show_region(file, 'Srem')
		exit()

		text = file.read()

	path = Path.find(text, 'Beograd')
	# print(path)

	# write_to_nodefile(path)
	meshes = iter_meshes(path)
	# print(meshes)

	show_meshes(meshes)
