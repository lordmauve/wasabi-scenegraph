Scenegraph Classes
==================

The end-user facing classes of Wasabi Scenegraph allow users to create simple
scenes by combining custom meshes created with tools such as Blender_ and
procedural meshes created with Python code.

.. _Blender: http://www.blender.org

The :py:class:`.Scene` object represents a scene that can be rendered,
including a selection of models and lights::

    from wasabisg.scenegraph import Scene

    scene = Scene(
        ambient=(0.05, 0.05, 0.05, 1.0)
    )

We might load a model from an .obj file and add an instance of it to the
scene::

    from wasabisg.loaders.objloader import ObjFileLoader
    from wasabisg.scenegraph import ModelNode

    loader = ObjFileLoader()
    tree_model = loader.load_obj('tree.obj')

    tree = ModelNode(tree_model, pos=(10, 0, 10))
    scene.add(tree)

We typically need a light::

    from wasabisg.lighting import Light

    # Distant light to approximate the sun
    sunlight = Light(
        pos=(100, 100, 100),
        colour=(1.0, 1.0, 1.0, 1.0),
        intensity=10,
        falloff=0
    )

    scene.add(sunlight)

Then the scene can be rendered::

    from euclid import Point3
    from wasabi.scenegraph import Camera

    c = Camera(
        pos=Point3(0, 1, -20),
        look_at=(0, 1, 0),
        width=800,  # or whatever size your viewport is
        height=600
    )
    scene.render(c)

Of course, you will need code to set up a window with an OpenGL context, and
then ensure that the scene is rendered every frame. The camera object can
persist between frames; assign to its ``pos`` and ``look_at`` attributes to
move and reorient the camera.

High Level Classes Reference
----------------------------

These high-level classes provide the main API for Wasabi Scenegraph.

.. automodule:: wasabisg.scenegraph

.. autoclass:: Scene
    :members:

The camera classes define how the scene is viewed. The ``width`` and ``height``
parameters should match the viewport into which you are rendering; these are
used both to calculate the correct aspect ratio and allocate appropriately
sized offscreen buffers when rendering.

.. autoclass:: Camera
    :members:

The standard camera applies a perspective. You can alternatively use an
orthographic camera so that your scene appears 2D or isometric.

.. autoclass:: OrthographicCamera
    :members:

.. autoclass:: ModelNode
    :members:


Lights
------

.. automodule:: wasabisg.lighting

.. autoclass:: Light

.. autoclass:: Sunlight
