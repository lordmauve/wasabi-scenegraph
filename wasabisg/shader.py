#
# Copyright Tristam Macdonald 2008.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#

import numbers
from itertools import chain
from contextlib import contextmanager

from OpenGL.GL import *

from pyglet.graphics import Group
from pyglet.image import SolidColorImagePattern
from ctypes import *


activeshader = None
activemtllib = None

white = None


def flatten(a):
    return list(chain(*a))


def get_white_texture():
    """Get a white texture, useful if a material does not provide a texture."""
    global white
    if white is None:
        fill = SolidColorImagePattern((255, 255, 255, 255))
        white = fill.create_image(1, 1).get_texture()
    return white


class Shader(object):
    # vert, frag and geom take arrays of source strings
    # the arrays will be concattenated into one string by OpenGL
    def __init__(self, vert='', frag='', geom='', reserved_textures=0):
        self.uniform_bindings = {}
        self.texture_bindings = {}

        # Number of texture units not used for material maps
        self.reserved_textures = reserved_textures

        # create the program handle
        self.handle = glCreateProgram()
        # we are not linked yet
        self.linked = False

        # create the vertex shader
        self.createShader([vert], GL_VERTEX_SHADER)

        # create the fragment shader
        self.createShader([frag], GL_FRAGMENT_SHADER)

        # the geometry shader will be the same, once pyglet supports the extension
        if geom:
            self.createShader([geom], GL_GEOMETRY_SHADER)

        # attempt to link the program
        self.link()

    def createShader(self, strings, type):
        count = len(strings)
        # if we have no source code, ignore this shader
        if count < 1:
            return

        # create the shader handle
        shader = glCreateShader(type)

        # convert the source strings into a ctypes pointer-to-char array, and upload them
        # this is deep, dark, dangerous black magick - don't try stuff like this at home!
#        src = (c_char_p * count)(*strings)
#        glShaderSource(shader, count, cast(pointer(src), POINTER(POINTER(c_char))), None)
        glShaderSource(shader, ''.join(strings))

        # compile the shader
        glCompileShader(shader)

        temp = c_int(0)
        # retrieve the compile status
        glGetShaderiv(shader, GL_COMPILE_STATUS, byref(temp))

        # if compilation failed, print the log
        if not temp:
            # retrieve the log length
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(temp))
            # create a buffer for the log
            buffer = create_string_buffer(temp.value)
            # retrieve the log text
            glGetShaderInfoLog(shader, temp, None, buffer)
            # print the log to the console
            print buffer.value
        else:
            # all is well, so attach the shader to the program
            glAttachShader(self.handle, shader)

    def link(self):
        # link the program
        glLinkProgram(self.handle)

        temp = c_int(0)
        # retrieve the link status
        glGetProgramiv(self.handle, GL_LINK_STATUS, byref(temp))

        # if linking failed, print the log
        if not temp:
            #    retrieve the log length
            glGetProgramiv(self.handle, GL_INFO_LOG_LENGTH, byref(temp))
            # create a buffer for the log
            buffer = create_string_buffer(temp.value)
            # retrieve the log text
            glGetProgramInfoLog(self.handle, temp, None, buffer)
            # print the log to the console
            print buffer.value
        else:
            # all is well, so we are linked
            self.linked = True

    def bind(self):
        # bind the program
        global activeshader
        glUseProgram(self.handle)
        activeshader = self

    def unbind(self):
        # unbind whatever program is currently bound - not necessarily this
        # program, so this should probably be a class method instead
        global activeshader
        glUseProgram(0)
        activeshader = None

    # upload a floating point uniform
    # this program must be currently bound
    def uniformf(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            {
                1: glUniform1f,
                2: glUniform2f,
                3: glUniform3f,
                4: glUniform4f
                # retrieve the uniform location, and set
            }[len(vals)](glGetUniformLocation(self.handle, name), *vals)

    # upload an integer uniform
    # this program must be currently bound
    def uniformi(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            {
                1: glUniform1i,
                2: glUniform2i,
                3: glUniform3i,
                4: glUniform4i
                # retrieve the uniform location, and set
            }[len(vals)](glGetUniformLocation(self.handle, name), *vals)

    # upload a uniform matrix
    # works with matrices stored as lists,
    # as well as euclid matrices
    def uniform_matrixf(self, name, mat):
        # obtian the uniform location
        loc = glGetUniformLocation(self.handle, name)
        # uplaod the 4x4 floating point matrix
        glUniformMatrix4fv(loc, 1, False, (c_float * 16)(*mat))

    def uniform1fv(self, name, values):
        """Pass an array of values"""
        loc = glGetUniformLocation(self.handle, name)
        arr = (c_float * len(values))(*values)
        glUniform1fv(loc, len(values), arr)

    def uniform2fv(self, name, values):
        """Pass an array of values"""
        loc = glGetUniformLocation(self.handle, name)
        arr = (c_float * (len(values) * 2))(*flatten(values))
        glUniform2fv(loc, len(values), arr)

    def uniform3fv(self, name, values):
        """Pass an array of values"""
        loc = glGetUniformLocation(self.handle, name)
        arr = (c_float * (len(values) * 3))(*flatten(values))
        glUniform3fv(loc, len(values), arr)

    def uniform4fv(self, name, values):
        """Pass an array of values"""
        loc = glGetUniformLocation(self.handle, name)
        arr = (c_float * (len(values) * 4))(*flatten(values))
        glUniform4fv(loc, len(values), arr)

    def set_material(self, material):
        """Read uniform properties from the given material."""
        for matprop, (uniform, type_) in self.uniform_bindings.iteritems():
            try:
                value = material[matprop]
            except KeyError:
                continue
            else:
                if type_ is int:
                    if isinstance(value, numbers.Number):
                        self.uniformi(uniform, int(value))
                    else:
                        self.uniformi(uniform, *(int(v) for v in value))
                else:
                    if isinstance(value, numbers.Number):
                        self.uniformi(uniform, value)
                    else:
                        self.uniformf(uniform, *value)

        texid = self.reserved_textures
        for mat_property, uniform in self.texture_bindings.iteritems():
            try:
                value = material.get_texture(mat_property)
            except KeyError:
                value = get_white_texture()
            self.bind_texture(uniform, texid, value.id)
            texid += 1

    def bind_texture(self, uniform, unit, id):
        """Bind a texture id to the uniform 'uniform', using texture unit unit"""
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, id)
        self.uniformi(uniform, unit)

    def unset_material(self, material):
        pass
#        texid = 0
#        for mat_property, uniform in self.texture_bindings.iteritems():
#            glActiveTexture(GL_TEXTURE0 + texid)
#            glBindTexture(GL_TEXTURE_2D, 0)
#            texid += 1

    def bind_material_to_uniformf(self, matprop, uniform):
        self.uniform_bindings[matprop] = (uniform, float)

    def bind_material_to_uniformi(self, matprop, uniform):
        self.uniform_bindings[matprop] = (uniform, int)

    def bind_material_to_texture(self, matprop, uniform):
        self.texture_bindings[matprop] = uniform


class ShaderGroup(Group):
    """A group that activates a Shader.

    Lists created with this group will be the rendered with the shader enabled;
    uniform variables can also be configured that will be applied whenever the
    shader is bound.

    """
    def __init__(self, shader, parent=None):
        super(ShaderGroup, self).__init__(parent)
        self.shader = shader
        self.uniforms = {}

    def set_state(self):
        self.shader.bind()
        for name, args in self.uniforms.iteritems():
            self.shader.uniformf(name, *args)
        ShaderGroup.currentshader = self.shader

    def uniformf(self, name, *args):
        """Set a named uniform value.

        This will be set when the shader is bound."""
        self.uniforms[name] = args

    def unset_state(self):
        self.shader.unbind()
        ShaderGroup.currentshader = None


class MaterialGroup(Group):
    def __init__(self, material, parent=None):
        self.material = material
        super(MaterialGroup, self).__init__(parent=parent)

    def set_state(self):
        super(MaterialGroup, self).set_state()
        if activeshader:
            activeshader.set_material(self.material)

    def unset_state(self):
        if activeshader:
            activeshader.unset_material(self.material)
        super(MaterialGroup, self).unset_state()
