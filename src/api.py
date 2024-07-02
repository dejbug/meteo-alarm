import sys, os, urllib.request


def iter_map_region_gif_urls():
	rr = ['ba', 'bc', 'bg', 'is', 'ji', 'jz', 'km', 'po', 'sr', 'su', 'zs']
	ss = [1, 2, 3, 4]
	for r in rr:
		for s in ss:
			yield f'https://www.meteoalarm.rs/mapa/{r}_{s}.gif'


def download_map_region_gifs(root = 'img', log = sys.stderr):
	for url in iter_map_region_gif_urls():
		name = os.path.split(url)[1]
		path = os.path.join(root, name)
		if os.path.exists(path):
			log.write(f'found "{path}"\n')
			continue
		log.write(f'FETCH "{path}"\n')
		with urllib.request.urlopen(url) as page:
			if page.status == 200:
				with open(path, 'wb') as file:
					file.write(page.read())


if __name__ == '__main__':
	download_map_region_gifs()
