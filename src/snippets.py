import abs

def clinc(rr, x, cc = None):
	'''
	Clock-like increment.

	>>> clinc([10, 10, 10], 1)
	([0, 0, 1], 0)
	>>> clinc([10, 10, 10], 123)
	([1, 2, 3], 0)
	>>> clinc([10, 10, 10], 1000)
	([0, 0, 0], 1)
	>>> clinc([10, 10, 10], 1230)
	([2, 3, 0], 1)
	>>> clinc([10, 10, 10], 4321)
	([3, 2, 1], 4)

	>>> clinc([2, 2, 2], 4)
	([1, 0, 0], 0)
	>>> clinc([2, 2, 2], 7)
	([1, 1, 1], 0)
	>>> clinc([2, 2, 2], 8)
	([0, 0, 0], 1)
	>>> clinc([2, 2, 2], 16)
	([0, 0, 0], 2)
	>>> clinc([2, 2, 2], 65535)
	([1, 1, 1], 8191)

	>>> clinc([3, 5, 2], 9)
	([0, 4, 1], 0)
	>>> clinc([3, 5, 2], 10)
	([1, 0, 0], 0)
	>>> clinc([3, 5, 2], 13)
	([1, 1, 1], 0)
	>>> clinc([3, 5, 2], 30)
	([0, 0, 0], 1)

	>>> clinc([1, 1, 1], 100)
	([0, 0, 0], 100)
	'''
	if not cc: cc = [0] * len(rr)
	# c = (x % C)
	# b = (x // C) % B
	# a = (x // C // B) % A
	for i in range(1, len(cc) + 1):
		cc[-i] = x % rr[-i]
		x //= rr[-i]
	return cc, x

def clinc_p(rr, x, cc = None):
	cc, x = clinc(rr, x, cc)
	return [c / r for c, r in zip(cc, rr)], x

def cliter(rr, method = clinc):
	c = 0
	while True:
		cc, done = method(rr, c)
		if done: break
		yield cc
		c += 1

def cliter_color(rr, callback = None):
	for cc in cliter(rr, clinc_p):
		if callback:
			yield callback(*cc)
		else:
			yield cc


if __name__ == '__main__':

	rr = (10, 2)
	cc = cliter_color(rr, lambda a, b: {'r' : a, 'g' : b, 'b' : 1})

	i = 0
	c = next(cc)
	while c:
		i += 1
		print(c)
		try:
			c = next(cc)
		except StopIteration:
			break
	print(i)

	exit()

	rr = (3, 5, 2)
	for c, cc in enumerate(cliter(rr, clinc_p)):
		print('%2d' % c, cc)






class Updatable:

# I wanted something like this:
# @Updatable(x = 0, y = 0, X = 0, Y = 0)
# class BBox:
#	def on_update(self, key):
#		self.w = self._X - self.x
#		self.h = self._Y - self.y

	def __init__(self, **kk):
		self.kk = kk

	def __call__(this, cls):

		def __init__(self, *aa, **kk):
			i = 0
			for k, v in this.kk.items():
				v = aa[i] if len(aa) > i else kk.setdefault(k, v)
				i += 1
				setattr(self, '_' + k, v)
			self.on_init(*aa, **kk)

		setattr(cls, '__init__', __init__)

		if not hasattr(cls, 'on_init'):
			setattr(cls, 'on_init', lambda self: self)

		if not hasattr(cls, 'on_update'):
			setattr(cls, 'on_update', lambda self, key: self)

		for k, v in this.kk.items():

			_k = '_' + k
#
			def setter(self, value):
				setattr(self, _k, value)
				self.on_update(k)
				return getattr(self, _k)

			setattr(cls, k, property(
				lambda self: getattr(self, _k),
				setter))

			# setattr(cls, k, property(
			# 	lambda self: getattr(self, _k),
			# 	lambda self, value: (setattr(self, _k, value), self.on_update(k), getattr(self, _k)),
			# 	None, ''))

			# FIXME: None of these work. (Why?)
			#	How do we define dynamic functions that are more
			#	powerful than Python's lambdas?

		return cls


# @abs.representable
@abs.Representable(x = '%4d', y = '%4d', X = '%4d', Y = '%4d')
class BOX:

	x = abs.Setter('update')
	y = abs.Setter('update')
	X = abs.Setter('update')
	Y = abs.Setter('update')

	def __init__(self, x = 0, y = 0, X = 0, Y = 0):
		self._x = x
		self._y = y
		self._X = X
		self._Y = Y
		self.w = self._X - self._x
		self.h = self._Y - self._y
		self.w2 = self.w >> 1
		self.h2 = self.h >> 1
		self.c = self._x + self.w2, self._y + self.h2

	def update(self, key):
		self.w = self._X - self._x
		self.h = self._Y - self._y
		self.w2 = self.w >> 1
		self.h2 = self.h >> 1
		self.c = self._x + self.w2, self._y + self.h2

	def __iter__(self):
		yield self._x
		yield self._y
		yield self._X
		yield self._Y

	@property
	def p(self):
		return self.x, self.y

	@property
	def s(self):
		return self.w, self.h

	def contains(self, x, y):
		return x >= self.x and x <= self.X and y >= self.y and y <= self.Y
