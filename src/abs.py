
def representable(cls):
	setattr(cls, '__repr__', lambda self: self.__class__.__name__ + str(self.__dict__))
	return cls


class Representable:
	def __init__(self, **kk):
		self.kk = kk

	def __call__(self, cls):

		def __repr__(obj):
			vv = []
			for k, f in self.kk.items():
				v = getattr(obj, k)
				v = f % getattr(obj, k) if f else str(v)
				vv.append(f'{k}: {v}')
			return obj.__class__.__name__ + ' [ ' + ' | '.join(vv) + ' ]'

		setattr(cls, '__repr__', __repr__)
		return cls


class Setter:
	def __init__(self, cb_key = None):
		self.cb_key = cb_key

	def __set_name__(self, obj, key):
		self.key = key
		self._key = '_' + key
		if self.cb_key and hasattr(obj, self.cb_key):
			self.cb = getattr(obj, self.cb_key)
		else:
			self.cb = None

	def __get__(self, obj, objtype = None):
		return getattr(obj, self._key)

	def __set__(self, obj, value):
		setattr(obj, self._key, value)
		if self.cb: self.cb(obj, self.key)
