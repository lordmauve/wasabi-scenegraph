# -*- coding: utf-8 -*-

"""
    :copyright: 2009 by Florian Boesch <pyalot@gmail.com>.
    :license: GNU AGPL v3 or later, see LICENSE for more details.
"""

from __future__ import with_statement

from ctypes import byref
from contextlib import nested

from OpenGL.GL import *
from .util import Context

__all__ = ['DepthBuffer']


class Depthbuffer(Context):
    _get = GL_RENDERBUFFER_BINDING

    def bind(self, id):
        glBindRenderbuffer(GL_RENDERBUFFER, id)

    def __init__(self, width, height):
        Context.__init__(self)
        self.id = glGenRenderbuffers(1)
        with self:
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, width, height)
