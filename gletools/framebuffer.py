# -*- coding: utf-8 -*-

"""
    :copyright: 2009 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from __future__ import with_statement

from ctypes import byref

from contextlib import nested

from OpenGL.GL import *
from .util import Context, get

__all__ = ['Framebuffer']

from OpenGL.GL.glget import addGLGetConstant

# Strangely missing from PyOpenGL
addGLGetConstant(GL_FRAMEBUFFER_BINDING, (1,))


class Textures(object):
    def __init__(self, framebuffer):
        self.framebuffer = framebuffer
        self.textures = [None] * get(GL_MAX_COLOR_ATTACHMENTS)

    def __getitem__(self, i):
        return self.textures[i]

    def __setitem__(self, i, texture):
        self.attach(i, texture)

    def attach(self, i, texture, level=0):
        with self.framebuffer:
            attachment = GL_COLOR_ATTACHMENT0 + i
            glFramebufferTexture2D(
                GL_FRAMEBUFFER,
                attachment,
                texture.target,
                texture.id,
                level,
            )
            texture.attachment = attachment
            self.textures[i] = texture

    def __iter__(self):
        return iter(self.textures)


class Framebuffer(Context):
    errors = {
        GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:'GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT',
        GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:'GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT: no image is attached',
        GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS:'GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS: attached images dont have the same size',
        GL_FRAMEBUFFER_INCOMPLETE_FORMATS:'GL_FRAMEBUFFER_INCOMPLETE_FORMATS: the attached images dont have the same format',
        GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER:'GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER',
        GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER:'GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER',
        GL_FRAMEBUFFER_UNSUPPORTED:'GL_FRAMEBUFFER_UNSUPPORTED',
    }
    class Exception(Exception): pass

    _get = GL_FRAMEBUFFER_BINDING

    def bind(self, id):
        glBindFramebuffer(GL_FRAMEBUFFER, id)

    def check(self):
        return  # FIXME
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            desc = self.errors.get(status)
            if desc:
                raise self.Exception(desc)
            else:
                raise self.Exception('unkown framebuffer object problem')

    def __init__(self, *textures):
        Context.__init__(self)
        self._texture = None
        self._depth = None
        self.id = glGenFramebuffers(1)
        self._textures = Textures(self)
        for i, texture in enumerate(textures):
            self.textures[i] = texture

    def get_depth(self):
        return self._depth
    def set_depth(self, depth):
        self._depth = depth
        with self:
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER,
                GL_DEPTH_ATTACHMENT,
                GL_RENDERBUFFER,
                depth.id,
            )
    depth = property(get_depth, set_depth)

    def _set_drawto(self, enums):
        with self:
            if isinstance(enums, int):
                buffers = (GLenum * len(enums))(enums)
            else:
                buffers = (GLenum * len(enums))(*enums)
            glDrawBuffers(len(enums), buffers)
    drawto = property(None, _set_drawto)

    def get_textures(self):
        return self._textures
    def set_textures(self, textures):
        for i, texture in enumerate(textures):
            self._textures[i] = texture
    textures = property(get_textures, set_textures)


