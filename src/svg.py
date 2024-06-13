import sys, os, re, json

from kivy.graphics.tesselator import Tesselator

import svgpathtools


class Error(Exception): pass
class TesselationError(Error): pass
class FileExistsError(Error): pass


class Path:

	def __init__(self, id, d):
		self.id = id
		self.segments = svgpathtools.parse_path(d)

	def __repr__(self):
		return self.__class__.__name__ + f'<"{self.id}">'

	@property
	def lines(self):
		for line in self.segments:
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

	@classmethod
	def finditer(cls, text):
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


class Tesselation:

	def __init__(self, path):
		self.path = path

		self.vvv = []
		self.iii = []

		self.tess = Tesselator()
		self.tess.add_contour(tuple(self.path.contour))

		if not self.tess.tesselate():
			raise TesselationError('failed to tesselate')

		for vv, ii in self.tess.meshes:
			self.vvv.append(vv)
			self.iii.append(ii)

	@property
	def id(self):
		return self.path.id

	@property
	def bbox(self):
		x, y, X, Y = sys.maxsize, sys.maxsize, 0, 0
		for vv in self.vvv:
			for i in range(0, len(vv), 4):
				x = min(x, vv[i])
				X = max(X, vv[i])
				y = min(y, vv[i + 1])
				Y = max(Y, vv[i + 1])
		return x, y, X, Y

	@property
	def dict(self):
		return {
			'id' : self.id,
			'bbox' : self.bbox,
			'contour' : list(self.path.contour),
			'vvv' : [ list(vv) for vv in self.vvv ],
			'iii' : [ list(ii) for ii in self.iii ]
		}

	def write(self, file = sys.stdout, **kk):
		json.dump(self.dict, file, **kk)


def convert(ipath, opath, force = False):
	if not os.path.isfile(ipath):
		raise FileExistsError(f'input path not found at "{ipath}"')
	if not force and os.path.exists(opath):
		raise FileExistsError(f'output path exists at "{opath}"; force overwrite not specified')

	with open(ipath) as f:
		pp = list(Path.finditer(f.read()))

	tt = [ Tesselation(p).dict for p in pp ]

	with open(opath, 'w') as f:
		json.dump(tt, f)


def load(ipath):
	with open('regions.json') as f:
		return json.load(f)



if __name__ == '__main__':
	convert('regions.svg', 'regions.json', force = True)

	# tt = load('regions.json')
	# for t in tt:
	# 	print(t['id'])
