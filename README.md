# Meteo-Alarm

This is to become a [mobile app](https://kivy.org/) frontend to the Serbian government's [weather service](https://www.hidmet.gov.rs/) site. In particular its [severe weather warning](https://www.meteoalarm.rs/ciril/meteo_alarm.php) feature.

The main purpose of this project is to give me something to do while getting to know [Kivy](https://kivy.org/).

# Devlog

## 2024-06-14

I've caught some kind of bug, a low-burning flu. And I'm still obsessing over that region-hovering digression. It's a side-quest but I need to see it through. So then, mouse input handling. The context transformations need to get applied to the cursor pos before we can even begin to think about ray-casting (or whatever). There didn't seem an easy way to do that,  like getting the canvas' internal matrices, so I've ended up removing all those transformation helper classes in favor of a single matrix. It took me quite some fiddling. It's becoming annoying how little experience I have with 3D stuff. I've been kinda faking it with the little that I know. But the knowledge is shallow and disjoint, not at all integrated into a clean conceptual framework that is useful and beautiful (pacifying, pleasing) in its explanatory power.

## 2024-06-13

I must admit, I am still not sure how to best approach the canvas. I've rewritten it so that I'm adding everything to the canvas just once, keeping references to everything that changes. All 'classical drawing' (blitting, really; pixel-bashing) is done by manipulating those references. Think tkinter's canvas; forget GDI raster graphics.

I don't like those references. I'm storing a Color ref for every single triangle. The user toggles a checkbox and I update hundreds at a time. Is this stuff supposed to be done with shaders instead? With textures? And suddenly I find myself having to dig into the underlying OpenGL.

**Q3**: I just realized that (substrings of) some of my function names are dirty words. What is Github's policy on 'dirty' function names in sources and commit messages?

**Q2**: If I (two-way-)bind a BooleanProperty to a CheckBox and vice versa, will it devolve into infinite (mutual) recursion or does Kivy catch this and correct for it?

## 2024-06-12

This is to become a mobile app of course, but I was briefly thinking about mouse-hovering animations which would reduce to [hittesting of arbirary regions](https://en.wikipedia.org/wiki/Point_in_polygon) and I got a bit derailed.

I was thinking: since my regions are already nicely tessellated this would become a lesser, point-in-triangle problem. Still, not trivial, but to speed things up we could check for bounding boxes first. And to speed that up we could use [quadtrees](https://en.wikipedia.org/wiki/Quadtree). I'm not entirley happy with any of this, though, but it made me want to look at the triangles the Kivy tesselator generated and so I went ahead and added this non-feature, too. It will all have to go.

[![Screencast](https://img.youtube.com/vi/o_XSfDedxq4/maxres2.jpg)](https://www.youtube.com/shorts/o_XSfDedxq4)

In the distant past I used to write some basic UML design software and I figured out that it's much faster to use an [offscreen bitmap](https://learn.microsoft.com/en-us/windows/win32/gdi/memory-device-contexts) and draw the hoverable shapes each in their own color (#000000, #000001, ... interpreted as their id) and simply use [`GetPixel`](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getpixel) at `WM_MOUSEMOVE`. (And yes [I was a teenage Win32 API user](https://www.youtube.com/watch?v=8GLUmIf8STw).) Point is: it was really, really fast! I hadn't expected that at all, this being the GDI and Windows.

I'm not entirely sure how to do that in OpenGL yet, but I'll try to play around with [render-to-texture](http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-14-render-to-texture/) and Kivy's [Framebuffer context](https://kivy.org/doc/stable/api-kivy.graphics.fbo.html). The docs read as if I could access the pixels via `fbo.texture.pixels`.

All this is, as they say, of purely academic value and so maybe I should better stick with the program instead. I wasn't planning on using Kivy for targeting mouse-based systems anyhow. Though it would be nice to know.

## 2024-06-11

Naturally I'm thinking about relegating run-time things to the compile-time now. To wit: extraction of the SVG path ids and vertices needs be done but once. Also I want to get rid of the [svgpathtools](https://pypi.org/project/svgpathtools/) run-time dependency. Turns out I can do my polygon scaling, centering, etc. (with modelview matrix transformations) in pure Kivy. Less usual things would still be doable by iterating on `mesh.vertices` directly. `svgpathtools` will become a dev-time dependency at worst. I am still to fully appreciate the simplifying power of the modelview transform.

(In lieu of actually coding, ...) At this point we will have to start considering that the regions will be displayed simultaneously and at various offsets to each other, namely, as a map (plus hovering effects). This means that normalizations like **vertical axis correction**, scaling and so on will no longer be local region operations but global map operations. (Here we're still trying to figure out what needs to go into the json file.) At minimum we'll have to precompute the bounding box of the collective region set, i.e. the map. (Attempting to write things clearly is really confusing me. Devlogs may not be for me.)

Note on **vertical axis correction**: (SVG has a top-down coordinate system, while Kivy's is bottom-up.) So far we did the calculations manually, hence slowly, vertex-by-vertex in `svgpath_flip_vertical()`. This was before realizing that Kivy exposes the underlying OpenGL semantics i.e. [transformation matrices](http://www.opengl-tutorial.org/beginners-tutorials/tutorial-3-matrices/). The neurotypical way, of course, is simply to scale the thing with a negative value e.g. y = -1. All this means that, with on-the-fly scaling and translation being covered by the GPU, vertex-by-vertex operation-wise this leaves us with little else to do. Making me feel rather spoiled and pampered.

## 2024-06-10

This site has a nice looking [country map](https://www.meteoalarm.rs/ciril/meteo_alarm.php) which I wanted to put in the app. The site's map is glued together from a series of gifs representing the country's regions. There are [SVG maps of Serbia](https://commons.wikimedia.org/wiki/File:Statistical_regions_of_Serbia.svg), but none of those look exactly like this one. So I decided to manually trace a screenshot of the map in [Inkskape](https://inkscape.org/). I started by drawing the shared borders first and duplicating them. I had to look up [how to join two paths](https://graphicdesign.stackexchange.com/questions/46294/how-to-join-end-nodes-of-different-paths-in-inkscape#46360), which wasn't obvious at all. Nice, relaxing work this was, all in all.

After vectorizing it the question became how to import it into the framework. Kivy's support for [SVG is experimental](https://kivy.org/doc/stable/api-kivy.graphics.svg.html). Neither does it feature a simple way to draw filled polygons. Kivy being OpenGL-based, it had to be done manually then. This is where I got entangled briefly with a charming little [tesselator](http://www.cs.cmu.edu/~quake/triangle.html), the 2003 winner of the [James Hardy Wilkinson Prize in Numerical Software](https://en.wikipedia.org/wiki/J._H._Wilkinson_Prize_for_Numerical_Software) no less. Eventually I came back to Kivy's own implementation, [experimental as it is](https://kivy.org/doc/stable/api-kivy.graphics.tesselator.html). It's infinitely more simple to use and it's working fine.

After getting the SVG to draw, I began fiddling with the Canvas object, trying to figure out what might be the best practice for updating meshes rather than re-creating them each time the window changes size. So far I've deduced three methods which all appear to work but only the devil knows whether they are portable or not. More thorough experiments are called for.
