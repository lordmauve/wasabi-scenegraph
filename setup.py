from setuptools import setup, find_packages


setup(
    name='wasabi-scenegraph',
    version='0.3.0',
    description="Pure python 3D graphics engine",
    long_description=open('README.rst').read(),
    author='Daniel Pope',
    author_email='mauve@mauveweb.co.uk',
    url='https://bitbucket.org/lordmauve/wasabi-scenegraph',
    packages=find_packages(),
    install_requires=[
        'PyOpenGL==3.0.2',
        'pyglet>=1.2alpha1',
        'euclid>=0.1',
    ],
    extras_require={
        'particles': [
            'wasabi-lepton>=1.0b2'
        ]
    },
    dependency_links=[
        'http://code.google.com/p/pyglet/downloads/list',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 2',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
