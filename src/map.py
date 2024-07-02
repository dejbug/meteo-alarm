from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image

class MapApp(App):
	def build(self):
		layout = FloatLayout()
		layout.add_widget(Image(source = 'img/bc_1.gif'))
		layout.add_widget(Image(source = 'img/ba_1.gif'))
		layout.add_widget(Image(source = 'img/bg_1.gif'))
		layout.add_widget(Image(source = 'img/is_3.gif'))
		layout.add_widget(Image(source = 'img/ji_3.gif'))
		layout.add_widget(Image(source = 'img/jz_2.gif'))
		layout.add_widget(Image(source = 'img/km_2.gif'))
		layout.add_widget(Image(source = 'img/po_2.gif'))
		layout.add_widget(Image(source = 'img/sr_1.gif'))
		layout.add_widget(Image(source = 'img/su_2.gif'))
		layout.add_widget(Image(source = 'img/zs_1.gif'))
		return layout

if __name__ == '__main__':
	MapApp().run()
