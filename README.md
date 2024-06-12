# Meteo-Alarm

This is to become a [mobile app](https://kivy.org/) frontend to the Serbian government's [weather service](https://www.hidmet.gov.rs/) site. In particular its [severe weather warning](https://www.meteoalarm.rs/ciril/meteo_alarm.php) feature.

The main purpose of this project is to give me something to do while getting to know [Kivy](https://kivy.org/).

# Devlog

## 2024-06-12

This is to become a mobile app of course, but I was briefly thinking about mouse-hovering animations which would reduce to [hittesting of arbirary regions](https://en.wikipedia.org/wiki/Point_in_polygon) and I got a bit derailed.

I was thinking: since my regions are already nicely tesellated into triangles this would become a point-in-triangle problem. To speed things up we could check for bounding boxes first. Second, to speed that up, we could use [quadtrees](https://en.wikipedia.org/wiki/Quadtree). I'm not happy with any of this, though.

All of this made me want to see the triangles the Kivy tesselator generated and so I went ahead and added this non-feature, too. It will all have to go.

[![Screencast](https://img.youtube.com/vi/o_XSfDedxq4/maxres2.jpg)](https://www.youtube.com/shorts/o_XSfDedxq4)

In the distant past I used to write some basic UML design software and I figured out that it's much faster to use an [offscreen bitmap](https://learn.microsoft.com/en-us/windows/win32/gdi/memory-device-contexts) and draw the hoverable shapes each in their own color (#000000, #000001, ... interpreted as their id) and simply use [`GetPixel`](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getpixel) at `WM_MOUSEMOVE`. (And yes [I was a teenage Win32 API user](https://www.youtube.com/watch?v=8GLUmIf8STw).) Point is: it was really, really fast! I hadn't expect that at all, this being the GDI and Windows.

I'm not entirely sure how to do that in OpenGL yet, but I'll try to play around with [render-to-texture](http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-14-render-to-texture/) and Kivy's [Framebuffer context](https://kivy.org/doc/stable/api-kivy.graphics.fbo.html). The docs read as if I could access the pixels via `fbo.texture.pixels`.

All this is, as they say, of purely academic value and so maybe I should better stick with the program instead. I wasn't planning on using Kivy for targeting mouse-based systems anyhow.

## 2024-06-11

Naturally I'm thinking about delegating run-time things to the compile-time. To wit: extraction of the SVG path ids and vertices needs be done but once. Moreover will I have to get rid of the [svgpathtools](https://pypi.org/project/svgpathtools/) run-time dependency. Turns out I can do my polygon scaling with modelview matrix transformations in pure Kivy. (Alternatively, I could do some manual matrix arithmetics on a mesh itself.) Centering would then be doable by iterating on `mesh.vertices` instead. All this means that `svgpathtools` will be relegated to a dev-time dependency at worst.

(In lieu of actually coding, ...) At this point we will have to start considering that the regions will be displayed simultaneously and at various offsets to each other, namely, as a map. This means that normalization, **vertical axis correction**, scaling and so on will no longer be local region operations but global map operations. This should be no problem since in both cases similar considerations apply.

Note on **vertical axis correction**: (SVG has a top-down coordinate system, while Kivy's is bottom-up.) So far we did the calculations manually, hence slowly, vertex-by-vertex in `svgpath_flip_vertical()`. This was before realizing that Kivy exposes the underlying OpenGL semantics i.e. [transformation matrices](http://www.opengl-tutorial.org/beginners-tutorials/tutorial-3-matrices/). The neurotypical way, of course, is simply to scale the thing with a negative value. All this means that, with scaling and translation being covered, vertex-by-vertex operation-wise this leaves us only with normalization. But this too can be handled at dev-time. Nice!

## 2024-06-10

The site has a nice looking [country map](https://www.meteoalarm.rs/ciril/meteo_alarm.php) which I wanted to put in the app. The site's map is glued together from a series of gifs representing the country's regions. There are [SVG maps of Serbia](https://commons.wikimedia.org/wiki/File:Statistical_regions_of_Serbia.svg), but none of those look exactly like this one. So I decided to manually trace a screenshot of the map in [Inkskape](https://inkscape.org/). I started by drawing the shared borders first and duplicating them. I had to look up [how to join two paths](https://graphicdesign.stackexchange.com/questions/46294/how-to-join-end-nodes-of-different-paths-in-inkscape#46360), which wasn't obvious at all. Nice, relaxing work this was, all in all.

After vectorizing it the question became how to import it into the framework. Kivy's support for [SVG is experimental](https://kivy.org/doc/stable/api-kivy.graphics.svg.html). Neither does it feature a simple way to draw filled polygons. Kivy being OpenGL-based, it had to be done manually then. This is where I got entangled briefly with a charming little [tesselator](http://www.cs.cmu.edu/~quake/triangle.html), the 2003 winner of the [James Hardy Wilkinson Prize in Numerical Software](https://en.wikipedia.org/wiki/J._H._Wilkinson_Prize_for_Numerical_Software) no less. Eventually I came back to Kivy's own implementation, [experimental as it is](https://kivy.org/doc/stable/api-kivy.graphics.tesselator.html). It's infinitely more simple to use and it's working fine.

After getting the SVG to draw, I began fiddling with the Canvas object, trying to figure out what might be the best practice for updating meshes rather than re-creating them each time the window changes size. So far I've deduced three methods which all appear to work but only God knows whether they are portable or not. More thorough experiments are called for.
