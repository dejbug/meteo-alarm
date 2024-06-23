import sys, re, json

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
	from kivy.uix.slider import Slider
	from kivy.graphics import Color, Rectangle, Mesh
	from kivy.graphics.tesselator import Tesselator

	from kivy.graphics.context_instructions import PushMatrix, PopMatrix
	from kivy.graphics.context_instructions import Translate, Scale, Rotate

	class RegionWidget(BoxLayout):

		def __init__(self, path):
			super().__init__()

			self.margin = 16
			self.update_method = 3

			self.path = path
			# self.path.normalize()
			# self.path.fit(self.width - self.margin, self.height - self.margin)
			# self.path.center(self.width, self.height)

			# We defer all drawing to self.update() which will
			#	do nothing if self.visible is False.
			self.visible = False

			self.bg = None
			self.meshes = []
			self.scale = None

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
				self.scale.x = self.scale.y = value


		# @property
		# def meshes(self):
			# return [c for c in self.canvas.children if isinstance(c, Mesh)]

		def draw_background(self):
			with self.canvas:
				Color(1, 1, 1, .3)
				self.bg = Rectangle(pos = self.pos, size = self.size)
				Color(1, 0, 0)

				# OBSOLETE: Ignore this. Just testing...
				if False:
					PushMatrix()
					Scale(x = 10., y = 10., origin = (15, 15))
					Translate(30, 30)
					Rotate(angle = 45, axis = (0, 0, 1), origin = (15, 15))
					Rectangle(pos = (10, 10), size = (20, 20))
					PopMatrix()

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

				# TODO: How do we pre-create a canvas command
				#	and simply add it to the canvas here? Here,
				#	this would allow us to remove self.scale_factor.
				self.scale = Scale(
					x = self.scale_factor, y = self.scale_factor,
					origin = self.center)

				Color(.8, .8, .3)
				for vertices, indices in self.tess.meshes:
					m = Mesh(
						vertices = vertices,
						indices = indices,
						mode = "triangle_fan"
					)
					self.meshes.append(m)

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
			# print('%20s' % self.path.id, f'{int(self.width):4} {int(self.height):4}', 'UPDATE' if self.visible else '')

			if not self.visible: return

			self.path.fit(self.width - self.margin, self.height - self.margin)
			self.path.center(self.width, self.height)

			if self.update_tesselator():

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


	class MyApp(App):

		@property
		def screen(self):
			return self.sm.get_screen(self.sm.current)

		@property
		def region(self):
			return self.screen.children[0]

		@property
		def regions(self):
			for screen in self.sm.screens:
				yield screen.children[0]

		def on_screen_activate(self, sm, name):
			sm.get_screen(name).children[0].visible = True

		def on_slider_value_change(self, slider, value):
			# scale = self.region.scale
			# if scale: scale.x = scale.y = value
			for region in self.regions:
				region.scale_factor = value

		def build(self):
			view = BoxLayout(orientation = 'vertical')
			main = BoxLayout(orientation = 'horizontal')
			tabs = BoxLayout(orientation = 'vertical', size_hint = (.3, 1))
			sm = ScreenManager(transition = FadeTransition(duration = 0))
			sm.bind(current = self.on_screen_activate)

			self.slider = MySlider()
			self.slider.bind(value = self.on_slider_value_change)

			main.add_widget(tabs)
			main.add_widget(sm)

			view.add_widget(main)
			view.add_widget(self.slider)

			self.sm = sm

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

			for path in Path.sorted(Path.iter(file.read())):
				addscr(path.id, path)

			return view

	MyApp().run()


def triangle_orient(A, B, C):
	# https://www.baeldung.com/cs/check-if-point-is-in-2d-triangle
	ABx = B[0] - A[0]
	ABy = B[1] - A[1]
	ACx = C[0] - A[0]
	ACy = C[1] - A[1]
	cp = ABx * ACy - ABy * ACx
	return 1 if cp > 0 else -1


def pt_in_triangle(A, B, C, p):
	# https://www.baeldung.com/cs/check-if-point-is-in-2d-triangle
	return 3 == abs(triangle_orient(A, B, p) + triangle_orient(B, C, p) + triangle_orient(C, A, p))


class Fan:
	def __init__(self, vv, ii):
		self.bbox = None
		self.vv = []

		j = 0
		for i in ii:
			v = vv[j:j+4]
			self.vv.extend(v)
			j += 4

	@property
	def triangle_count(self):
		return len(self) - 2

	def triangle(self, index):
		return self.vv[index : index + 12]

	@property
	def triangles(self):
		for i in range(self.triangle_count):
			yield self.triangle(i)

	def __len__(self):
		return len(self.vv) >> 2

	def contains(self, x, y):
		if self.bbox and not self.bbox.contains(x, y):
			return False
		if len(self) == 3:
			A = self.vv[0], self.vv[1]
			B = self.vv[4], self.vv[5]
			C = self.vv[8], self.vv[9]
			return pt_in_triangle(A, B, C, (x, y))
		else:
			# A B C, C D A, D E A, ...
			# A B C, A C D, A D E, ...
			A = self.vv[0], self.vv[1]
			offset = 0
			for i in range(len(self) - 2):
				# offset = i << 2
				B = self.vv[4 + offset], self.vv[5 + offset]
				C = self.vv[8 + offset], self.vv[9 + offset]
				if pt_in_triangle(A, B, C, (x, y)):
					return True
				offset += 4
			return False


class Region:
	def __init__(self, id, vvv, iii, bbox):
		self.id = id
		self.fans = [ Fan(vv, ii) for vv, ii in zip(vvv, iii) ]
		self.bbox = bbox

	def __repr__(self):
		return self.__class__.__name__ + str(self.__dict__)

	def __len__(self):
		return len(self.fans)

	def __getitem__(self, key):
		return self.fans[key]

def load_regions(path = 'regions.json'):
	with open(path) as file:
		tt = json.load(file)
		return [ Region(t['id'], t['vvv'], t['iii'], t['bbox']) for t in tt ]


if __name__ == '__main__':
	with open('regions.svg') as file:
		show_paths(file)
