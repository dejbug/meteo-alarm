# import regions
# rr = regions.load_regions()
# r = rr[0]
# f = r.fans[0]
# for v in f.vv:
# 	print(v)
# for t in f.triangles:
# 	print(t)
# exit()


def triangle_bbox():
	pass

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

def pt_in_triangle_fan():
	pass


import kivy
kivy.require('1.9.0')

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
# Config.set('kivy', 'keyboard_mode', 'dock')
# Config.set('kivy', 'keyboard_mode', 'system')

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.properties import NumericProperty

from kivy.base import runTouchApp

class KeyboardWidget(Widget):

	def __init__(self, **kk):
		super().__init__(**kk)

		self._keyboard = Window.request_keyboard(
			self._keyboard_closed, self, 'text')
		if not self._keyboard.widget:
			print('keyboard request failed')
		self._keyboard.bind(on_key_down = self._on_keyboard_down)

	def _keyboard_closed(self):
		print('My keyboard have been closed!')
		self._keyboard.unbind(on_key_down = self._on_keyboard_down)
		self._keyboard = None

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		print('The key', keycode, 'have been pressed')
		print(' - text is %r' % text)
		print(' - modifiers are %r' % modifiers)
		# Keycode is composed of an integer + a string
		# If we hit escape, release the keyboard
		if keycode[1] == 'escape':
			keyboard.release()
		# Return True to accept the key. Otherwise, it will be used by
		# the system

class TriangleViewer(KeyboardWidget):

	region = NumericProperty()

	def __init__(self, **kk):
		super().__init__(**kk)
		self.bind(pos = self.draw, size = self.draw)
		# self.triangle = rr[0].fans[0]
		# self.regions = load_regions()

		self.triangle = (100, 100, 500, 100, 300, 500)
		self.fan = Mesh(
			vertices = [self.triangle[0], self.triangle[1], self.triangle[0], self.triangle[1],
						self.triangle[2], self.triangle[3], self.triangle[2], self.triangle[3],
						self.triangle[4], self.triangle[5], self.triangle[4], self.triangle[5]],
			indices = [0, 1, 2],
			mode = "triangle_fan"
		)
		self.bind(region = self.draw)

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		k = keycode[0]
		if k >= ord('1') and k <= ord('9'):
			self.region = k - ord('0')
			print(self.region)

	def draw(self, *aa):
		# print(self.region)
		self.canvas.clear()

		with self.canvas:
			Color(1, 1, 1, .3)
			Rectangle(pos = self.pos, size = self.size)

			# r = self.regions[self.region]
			# print(r.id)
			# Color(1, 0, 0, .3)
			# Rectangle(pos = r.bbox[:2], size = r.bbox[2:])

			Color(1, 0, 0, .3)
			self.canvas.add(self.fan)

class TriangleViewerApp(App):

	def __init__(self, **kk):
		super().__init__(**kk)
		Window.bind(on_mouse_down = self.on_mouse_down)
		Window.bind(on_motion = self.on_motion)

	def build(self):
		self.viewer = TriangleViewer()
		return self.viewer

	def on_mouse_down(self, win, x, y, button, modifiers):
		print(x, y, button, modifiers)

	def on_motion(self, win, etype, me):
		x = (self.viewer.width + self.viewer.x) * me.sx
		y = (self.viewer.height + self.viewer.y) * me.sy
		A = self.viewer.triangle[0], self.viewer.triangle[1]
		B = self.viewer.triangle[2], self.viewer.triangle[3]
		C = self.viewer.triangle[4], self.viewer.triangle[5]
		print(pt_in_triangle(A, B, C, (x, y)))

TriangleViewerApp().run()

# runTouchApp(TriangleViewer())
