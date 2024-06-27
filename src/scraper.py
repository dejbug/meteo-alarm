import sys, os, re, time, base64, pickle, urllib.request, io, datetime

URL = 'https://www.meteoalarm.rs/latin/meteo_alarm.php'

def mkurl(dt = None):
	if dt:
		dt = parse_dt_arg(dt)
	else:
		dt = datetime.datetime.now()
	return URL + f'?ma_datum=' + dt.strftime('%Y-%m-%d')

def parse_dt_arg(dt):
	# print(f'[> \'{dt}\']')

	if isinstance(dt, datetime.datetime):
		return dt

	if isinstance(dt, str):
		# fillin = lambda old, new, _: (old // (10 ** len(new))) * 10 ** len(new) + int(new)
		fillin = lambda old, new, n: int(f'{old:0{n}}'[:n-len(new)] + new) # is a little bit faster

		# if res := parse_dt_arg_relative(dt):
		# 	return res

		# if mm := re.match(r'(?:(?:((?:\d\d)?\d?\d)-)?(\d?\d)-)?(\d?\d)', dt):
		if mm := re.match(r'^\s*(?:(?:((?:\d\d)?\d?\d)-)?(\d?\d)-)?(\d?\d)\s*$', dt):
			Y, M, D = mm.groups()
			now = datetime.datetime.now()
			Y = fillin(now.year, Y, 4) if Y else now.year
			M = fillin(now.month, M, 2) if M else now.month
			D = fillin(now.day, D, 2) if D else now.day
			return datetime.datetime(year = Y, month = M, day = D)

def parse_dt_arg_relative(dt):
	# FIXME: E.g.: parse_dt_arg('365 days ago') will fail.

	# FIXME: How do you sanely specify a date-range in various
	#	units (i.e. years, months, days; i.e. hence not just in
	#	days as required by timedelta) and still get leap years
	#	honored?

	if mm := re.match(r'.*(\s+ago\s*)$', dt):
		dt = dt[:mm.start(1)]
		Y, M, D = now.year, now.month, now.day
		for m in re.finditer(r'\s*(?:and\s+)?(\d+)\s+([dmyDMY])\S*', dt):
			v = int(m.group(1))
			k = m.group(2).lower()
			if k == 'y': Y = now.year - v
			elif k == 'm': M = now.month - v
			elif k == 'd': D = now.day - v
		return datetime.datetime(year = Y, month = M, day = D)

class Cache:

	def __init__(self, root = None):
		self.root = root or os.getcwd()

	def set(self, key, value, force = False):
		'''
		Returns: True if written, False if not written
			(i.e. if file exists and force flag was not True),
			or None if something exists but it is not a file.
		'''
		path = self.key2path(key, self.root)

		if os.path.exists(path):
			if not os.path.isfile(path):
				return None
			if not force:
				return False

		with open(path, 'wb') as file:
			pickle.dump(value, file)
		return True

	def get(self, key):
		path = self.key2path(key, self.root)
		if os.path.isfile(path):
			with open(path, 'rb') as file:
				return pickle.load(file)

	def age(self, key):
		path = self.key2path(key, self.root)
		if os.path.isfile(path):
			return time.time() - os.path.getmtime(path)

	@property
	def keys(self):
		for slot in self.slots:
			yield self.slot2key(slot)

	@property
	def slots(self):
		for n in os.listdir(self.root):
			if n.endswith('.pickle'):
				yield os.path.splitext(n)[0]

	@classmethod
	def path_can_write(cls, path, maxage = None):
		'''
			Returns: True if path does not exist or if path is
				a file AND either its modified age >= maxage
				or maxage is not a positive integer.
		'''
		if maxage is None or maxage <= 0:
			return not os.path.exists(path) or os.path.isfile(path)
		if os.path.isfile(path):
			return time.time() - os.path.getmtime(path) >= maxage
		if not os.path.exists(path):
			return True

	@classmethod
	def key2path(cls, key, root = None):
		slot = cls.key2slot(key)
		assert key == cls.slot2key(slot)

		path = cls.slot2path(slot, root)
		assert slot == cls.path2slot(path)

		return path

	@classmethod
	def slot2path(cls, slot, root = None):
		root = root or os.getcwd()
		return os.path.join(root, slot + '.pickle') if root else slot

	@classmethod
	def path2slot(cls, path):
		path, e = os.path.splitext(path)
		return os.path.basename(path)

	@classmethod
	def key2slot(cls, key):
		slot = base64.b64encode(key.encode('utf8'), altchars = b'+-')
		return slot.decode('ascii')

	@classmethod
	def slot2key(cls, slot):
		key = base64.b64decode(slot.encode('ascii'), altchars = b'+-')
		return key.decode('utf8')

	def fetch(self, url, maxage = None):
		age = self.age(url)

		new = age is None
		refetch = maxage is not None and maxage <= 0
		expired = maxage is not None and age is not None and age >= maxage

		# age == None or maxage != None and (maxage <= 0 or age >= maxage)
		if new or refetch or expired:
			text = fetch(url)
			text = text.decode('utf8')
			if text:
				self.set(url, text, force = True)
			return text

		elif age is not None:
			sys.stderr.write('* cache hit')
			if maxage is None:
				sys.stderr.write(' (forced)')
			if expired:
				sys.stderr.write(' (expired)')
			sys.stderr.write('\n')
			text = self.get(url)
			return text

def fetch(url = URL):
	with urllib.request.urlopen(url) as page:
		# print(page.url, page.status)
		# print(page.headers)
		if page.status == 200:
			return page.read()

def iter_tags(text):
	regex = re.compile(r'class="([a-z]+)_tab|/mapa/(w|l)(?:type|vlbox)([0-9])\.gif')
	state = 0
	for m in regex.finditer(text):
		tab, typ, num = m.groups()
		num = int(num) if num else num
		# print(tab, typ, num)
		if state == 0:
			if tab:
				state = 1
				yield 'T', tab
			continue
		elif state == 1:
			if typ[0] == 'l':
				assert num == 1
				state = 3
			else:
				assert typ[0] == 'w'
				state = 2
				yield 'W', int(num)
		elif state == 2:
			assert typ[0] == 'l'
			state = 3
			yield 'L', int(num)
		elif state == 3:
			if tab:
				state = 1
				yield 'T', tab
			elif typ[0] == 'w':
				state = 2
				yield 'W', int(num)
			else:
				assert typ[0] == 'l'
				break

def tab(text, ascii = True):
	if text == 'bc': return 'Backa' if ascii else 'Bačka'
	if text == 'ba': return 'Banat'
	if text == 'sr': return 'Srem'
	if text == 'bg': return 'Beograd'
	if text == 'zs': return 'Zapadna' # + ' Srbija'
	if text == 'su': return 'Sumadija' if ascii else 'Šumadija'
	if text == 'po': return 'Pomoravlje'
	if text == 'is': return 'Istocna' if ascii else 'Istočna' # + ' Srbija'
	if text == 'ji': return 'Jugoistocna' if ascii else 'Jugoistočna' # + ' Srbija'
	if text == 'jz': return 'Jugozapadna' # + ' Srbija'
	if text == 'km': return 'Kosovo' # + ' i Metohija'

def lvlbox2str(num):
	if num == 1: return 'green'
	if num == 2: return 'yellow'
	if num == 3: return 'orange'
	if num == 4: return 'red'

def wtype(num):
	if num == 0: return 'wind'
	if num == 1: return 'rain'
	if num == 2: return 'snow' # 'snow/hail'
	if num == 3: return 'storm'
	if num == 4: return 'fog'
	if num == 5: return 'heat'
	if num == 6: return 'cold'
	if num == 7: return 'fire'

def iter_regions(text):
	id = None
	icons = []
	icon = []
	for tag, text in iter_tags(text):
		# print(text)
		if tag == 'T':
			if id:
				yield id, icons
			id = text
			icons = []
			icon = []
		else:
			icon.append(text)
			if tag == 'L':
				icons.append(icon)
				icon = []
	if id:
		yield id, icons

def sort_icons_by_severity(icons, reverse = False):
	icons = sorted(icons, key = lambda icon: icon[0], reverse = False)
	icons = sorted(icons, key = lambda icon: icon[1], reverse = reverse)
	return icons

def group_icons_by_severity(icons, reverse = False):
	groups = [ [] for i in range(4) ]
	icons = sort_icons_by_severity(icons)
	for wtype, lvl in icons:
		groups[lvl - 1].append(wtype)
	if reverse:
		lvls = reversed(range(1, 1 + 4))
		groups = reversed(groups)
	else:
		lvls = range(1, 1 + 4)
	# yield from zip(groups, lvls)
	return list(zip(groups, lvls))

def print_regions_1(rr):
	for id, icons in rr:
		print('%-12s' % tab(id), end = ': ')
		for w, l in sort_icons_by_severity(icons, reverse = True):
			print('%6s' % lvlbox2str(l), '%-5s' % wtype(w), end = ' | ')
		print()

def print_regions_2(regions):

	rr = {}
	for id, icons in regions:
		rr[id] = ll = {}
		for lvl in range(1, 1 + 4):
			ll.setdefault(lvl, [])
		for w, lvl in icons:
			ll[lvl].append(w)
	# print(rr)

	# cc = {}
	# for id, ll in rr.items():
	# 	for lvl in range(1, 1 + 4):
	# 		ww = ll[lvl]
	# 		c = len(' '.join(wtype(w) for w in ww))
	# 		cc[lvl] = max(cc.setdefault(lvl, 0), c)
	# print(cc)

	xx = {}
	for id, ll in rr.items():
		for lvl, ww in ll.items():
			ss = xx.setdefault(lvl, set())
			ss.update(set(ww))
	# print(xx)

	cc = {}
	for lvl, ww in xx.items():
		cc[lvl] = len(' '.join(wtype(w) for w in ww))
	# print(cc)

	print('_' * 12, end = '|')
	for lvl in range(1, 1 + 4):
		c = cc[lvl]
		if c:
			c2 = c >> 1
			ps = '_' * (c2 + 1)
			pe = '_' * (c - c2)
			print(ps + str(lvl) + pe, end = '|')
		else:
			print(lvl, end = '|')
	print()

	for id, ll in rr.items():
		print('%-11s' % tab(id), end = ' | ')
		for lvl in range(1, 1 + 4):
			ww = ll[lvl]
			# s = ' '.join(wtype(w) for w in ww)
			# s += ' ' * (cc[lvl] - len(s))
			# print(s, end = ' | ')
			ss = []
			for x in xx[lvl]:
				s = wtype(x)
				if x not in ww:
					s = ' ' * len(s)
				ss.append(s)
			if ss:
				print(' '.join(ss), end = ' | ')
			else:
				print('| ', end = '')
		print()

	return

	s = io.StringIO()

	lengths = {1:0, 2:0, 3:0, 4:0}
	for id, icons in rr:
		local_lengths = {1:0, 2:0, 3:0, 4:0}
		for w, lvl in icons:
			local_lengths[lvl] += 1 + len(wtype(w))
		for k, v in local_lengths.items():
			lengths[k] = max(lengths[k], v - 1)
	print(lengths)

	for id, icons in rr:
		s.write('%-11s |' % tab(id))

		icons = group_icons_by_severity(icons, reverse = True)
		for ww, lvl in icons:
			t = ' '.join(wtype(w) for w in ww)
			t += ' ' * (lengths[lvl] - len(t))
			s.write(t)
			s.write(' | ')

		s.write('\n')

	print(s.getvalue())

if __name__ == '__main__':
#
	# with open('meteo_alarm.php', 'r', encoding = 'utf8') as ifile:
	# 	with open(Cache.key2path(URL), 'wb') as ofile:
	# 		pickle.dump(ifile.read(), ofile)

	cache = Cache()
	for key in cache.keys:
		print(key)
	print('-' * 79)

	# url = mkurl()
	# dt = datetime.datetime.now()
	# dt -= datetime.timedelta(days = 1)
	# dt -= datetime.timedelta(days = 2)
	# dt -= datetime.timedelta(days = 3)
	# dt -= datetime.timedelta(days = 4)
	# url = mkurl(dt)
	url = mkurl('2024-6-25')
	print(url)
	print('-' * 79)

	# text = cache.fetch(url, maxage = 0)
	# text = cache.fetch(url, maxage = 3600 * 24)
	text = cache.fetch(url)
	# print(text)
	# for tag in iter_tags(text): print(tag)

	rr = list(iter_regions(text))
	assert len(rr) == 11

	# print('-' * 79)
	# print_regions_1(rr)
	print('-' * 79)
	print_regions_2(rr)
