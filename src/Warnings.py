from kivy.storage.jsonstore import JsonStore

import sys, os, re, time, datetime, urllib.request, urllib.error, traceback


URL = 'https://www.meteoalarm.rs/latin/meteo_alarm.php'

TAGTYPE_TAB		= 1
TAGTYPE_WTYPE	= 2
TAGTYPE_LVLBOX	= 3


class Warnings:

	def __init__(self, data = {}):
		self.data = data or {}

	@property
	def timestamp(self):
		return self.data.get('timestamp', 0)

	@property
	def url(self):
		return self.data.get('url', '')

	@property
	def warnings(self):
		return self.data.get('warnings', {})

	@property
	def date(self):
		if url := self.url:
			m = re.match(r'.*?ma_datum=(\d{4}-\d{2}-\d{2})', url)
			if m:
				return datetime.datetime.strptime(m.group(1), '%Y-%m-%d')

	@property
	def age(self):
		if timestamp := self.timestamp:
			return time.time() - timestamp

	def __repr__(self):
		return self.__class__.__name__ + str(self.data)

	@classmethod
	def load(cls, path = 'store.json'):
		store = JsonStore(path)
		if store.exists('warnings'):
			return cls(store.get('warnings'))

	def save(self, path = 'store.json'):
		store = JsonStore(path)
		store.put('warnings', **self.data)

	@classmethod
	def fetch(cls, dt = None, log = None):
		url = mkurl(dt)
		text = fetch(url, log)
		if text:
			text = text.decode('utf8')
			rr = iter_regions(text)
			# rr = list(rr); print(rr)
			rr = { r[0] : r[1] for r in rr }
			return cls({ 'warnings' : rr, 'url' : url, 'timestamp': time.time() })


def mkurl(dt = None):
	if dt:
		dt = parse_dt_arg(dt)
	else:
		dt = datetime.datetime.now()
	return URL + f'?ma_datum=' + dt.strftime('%Y-%m-%d')


def parse_dt_arg(dt):
	if isinstance(dt, datetime.datetime):
		return dt
	if isinstance(dt, str):
		# fillin = lambda old, new, _: (old // (10 ** len(new))) * 10 ** len(new) + int(new)
		fillin = lambda old, new, n: int(f'{old:0{n}}'[:n - len(new)] + new) # is a little bit faster
		# if mm := re.match(r'(?:(?:((?:\d\d)?\d?\d)-)?(\d?\d)-)?(\d?\d)', dt):
		if mm := re.match(r'^\s*(?:(?:((?:\d\d)?\d?\d)-)?(\d?\d)-)?(\d?\d)\s*$', dt):
			Y, M, D = mm.groups()
			now = datetime.datetime.now()
			Y = fillin(now.year, Y, 4) if Y else now.year
			M = fillin(now.month, M, 2) if M else now.month
			D = fillin(now.day, D, 2) if D else now.day
			return datetime.datetime(year = Y, month = M, day = D)


def fetch(url, log = sys.stderr):
	try:
		with urllib.request.urlopen(url) as page:
			# print(page.url, page.status)
			# print(page.headers)
			if page.status == 200:
				return page.read()
	except urllib.error.URLError as e:
		if log:
			traceback.print_exception(e, file = log, chain = False)


def iter_regions(text):
	id = None
	icons = []
	icon = []
	for key, value in iter_tags(text):
		# print(key, value)
		if key == TAGTYPE_TAB:
			if id:
				yield id, sort_icons_by_severity(icons)
			id = value
			icons = []
			icon = []
		else:
			icon.append(value)
			if key == TAGTYPE_LVLBOX:
				icons.append(icon)
				icon = []
	if id:
		yield id, sort_icons_by_severity(icons)


def iter_tags(text):
	state = 0
	for m in re.finditer(r'class="([a-z]+)_tab|/mapa/(w|l)(?:type|vlbox)([0-9])\.gif', text):
		tab, typ, num = m.groups()
		num = int(num) if num else num
		# print(tab, typ, num)
		if state == 0:
			if tab:
				state = 1
				yield TAGTYPE_TAB, tab
			continue
		elif state == 1:
			if typ[0] == 'l':
				assert num == 1
				state = 3
			else:
				assert typ[0] == 'w'
				state = 2
				yield TAGTYPE_WTYPE, int(num)
		elif state == 2:
			assert typ[0] == 'l'
			state = 3
			yield TAGTYPE_LVLBOX, int(num)
		elif state == 3:
			if tab:
				state = 1
				yield TAGTYPE_TAB, tab
			elif typ[0] == 'w':
				state = 2
				yield TAGTYPE_WTYPE, int(num)
			else:
				assert typ[0] == 'l'
				break


def sort_icons_by_severity(icons, reverse = False):
	icons = sorted(icons, key = lambda icon: icon[0], reverse = False)
	icons = sorted(icons, key = lambda icon: icon[1], reverse = reverse)
	return icons


def id2name(text, ascii = True):
	if text == 'ba': return 'Banat'
	if text == 'bc': return 'Backa' if ascii else 'Bačka'
	if text == 'bg': return 'Beograd'
	if text == 'is': return 'Istocna Srbija' if ascii else 'Istočna Srbija'
	if text == 'ji': return 'Jugoistocna Srbija' if ascii else 'Jugoistočna Srbija'
	if text == 'jz': return 'Jugozapadna Srbija'
	if text == 'km': return 'Kosovo i Metohija'
	if text == 'po': return 'Pomoravlje'
	if text == 'sr': return 'Srem'
	if text == 'su': return 'Sumadija' if ascii else 'Šumadija'
	if text == 'zs': return 'Zapadna Srbija'


def lvlbox2str(num):
	if num == 1: return 'green'
	if num == 2: return 'yellow'
	if num == 3: return 'orange'
	if num == 4: return 'red'


def wtype2str(num):
	if num == 0: return 'wind'
	if num == 1: return 'rain'
	if num == 2: return 'snow/hail'
	if num == 3: return 'storm'
	if num == 4: return 'fog'
	if num == 5: return 'heat'
	if num == 6: return 'cold'
	if num == 7: return 'fire'


if __name__ == '__main__':
	warnings = Warnings.load()
	print(warnings)
	print(warnings.timestamp)
	print(warnings.url)
	print(warnings.warnings)
	print(warnings.date)
	print(warnings.age)

	warnings = warnings.fetch('2024-6-12')
	print(warnings)
