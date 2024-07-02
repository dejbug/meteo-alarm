import sys, os, re


def iter_map_region_gif_names():
	rr = ['ba', 'bc', 'bg', 'is', 'ji', 'jz', 'km', 'po', 'sr', 'su', 'zs']
	ss = [1, 2, 3, 4]
	for r in rr:
		for s in ss:
			yield f'{r}_{s}.gif'

def iter_map_region_gif_urls():
	for name in iter_map_region_gif_names():
		yield 'https://www.meteoalarm.rs/mapa/%s' % name


def download_map_region_gifs(root = 'img', log = sys.stderr):
	import urllib.request

	for url in iter_map_region_gif_urls():
		name = os.path.split(url)[1]
		path = os.path.join(root, name)
		if os.path.exists(path):
			if log: log.write(f'found "{path}"\n')
			continue
		if log: log.write(f'FETCH "{path}"\n')
		with urllib.request.urlopen(url) as page:
			if page.status == 200:
				with open(path, 'wb') as file:
					file.write(page.read())


def iter_map_region_gif_sizes(root = 'img'):
	from kivy.core.image import Image as CoreImage

	for name in iter_map_region_gif_names():
		m = re.match(r'(..)_(\d)\.gif', name)
		if not m: continue

		path = os.path.join(root, name)
		if os.path.isfile(path):
			yield m.group(1), m.group(2), CoreImage(path).size


def get_map_region_gifs_size(root = 'img'):

	w = 0
	h = 0

	sizes = iter_map_region_gif_sizes()
	try:
		id, sev, size = next(sizes)
		w, h = size
	except StopIteration:
		raise Exception('no sizes found')

	for id, sev, size in sizes:
		if w != size[0] or h != size[1]:
			raise Exception('size mismatch detected')

	return w, h

def check_map_region_gifs_size(root = 'img', log = sys.stderr):
	try:
		return get_map_region_gifs_size(root)
	except Exception as e:
		if log: print(e, file = log)
	return None, None

if __name__ == '__main__':
	download_map_region_gifs()
	w, h = check_map_region_gifs_size()
	print(w, h)
