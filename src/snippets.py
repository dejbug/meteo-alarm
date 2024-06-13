
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

