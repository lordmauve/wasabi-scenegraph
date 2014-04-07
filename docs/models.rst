Models and Meshes
=================

To use Wasabi Scenegraph effectively you should be familiar with the following
terminology.

.. glossary::

    material
        A dictionary of parameters that configure the appearance of a
        :term:`mesh`.

    mesh
        A collection of geometry that is drawn with the same material. A mesh
        is made up of vertices, normals, texture coordinates etc. Each mesh is
        associated with exactly one material.

    model
        A collection of meshes. Not to be confused with a model node, this is
        a template that can be instantiated into the scene several times.

    model node
        An instance of a model that can appear in the scene.


Models and Materials
--------------------

.. py:module:: wasabisg.model

.. autoclass:: Model

.. autoclass:: Material


Model Loading
-------------

.. automodule:: wasabisg.loaders.objloader

The simplest way of getting a custom model into Wasabi Scenegraph is to load it
from a .obj file. This is a text representation that can be exported by most 3D
graphics programs.

.obj files are associated with a .mtl file that contains named material
definitions. The :py:class:`.ObjFileLoader` will load models together with the
associated materials from a .mtl file.

.. autoclass:: ObjFileLoader
    :members: load_obj


Generated Meshes
----------------

Meshes are a collection of vertex, normal and texture coordinate data that are
associated with a :py:class:`Material`. If necessary a Mesh can be constructed
procedurally. Note that if you want to construct simple 3D shapes such as
spheres or planes, then :ref:`concrete subclasses <primitives>` are available
to construct these for you.

.. currentmodule:: wasabisg.model

.. autoclass:: Mesh


.. _primitives:

3D Primitive Meshes
-------------------

.. automodule:: wasabisg.plane

.. autoclass:: Quad

.. autoclass:: Plane

.. automodule:: wasabisg.sphere

.. autoclass:: Sphere
