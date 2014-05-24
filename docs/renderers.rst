Renderers
---------

Wasabi Scenegraph's renderers encapsulate the low-level graphics code that
attempt to render the scene you create with the :doc:`high level API <scene>`
using OpenGL (or another API; you should be able to write a renderer to render
with Direct3D for example, or a more realistic target would be OpenGL ES).

Wasabi Scenegraph currently includes two Renderers:

* ``wasabisg.renderer.LightingAccumulationRenderer`` (the default). This
  renderer uses GLSL shaders to render standard solid objects with per-pixel
  lighting.

    .. image:: _static/lighting-accumulation.png

* ``wasabisg.fallbackrenderer.FallbackRenderer``. This uses an OpenGL 1.x-style
  fixed function pipeline to provide basic rendering functions only, such as
  vertex lighting. This can be useful for debugging or to provide compatibility
  with systems running very old hardware.

   .. image:: _static/fallbackrenderer.png

The intention is that developers will use and adapt the more powerful renderer
in most cases.
