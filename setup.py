from setuptools import setup, find_packages


setup(
    name='wasabi.scenegraph',
    version='0.1',
    description="Pure python 3D graphics engine",
    long_description=open('README.rst').read(),
    author='Daniel Pope',
    author_email='mauve@mauveweb.co.uk',
    url='https://bitbucket.org/lordmauve/wasabi-scenegraph',
    packages=find_packages(),
    install_requires=[
        'pyglet>=1.2alpha1',
        'euclid>=0.1',
    ],
    extras_requires={
        'particles': [
            'lepton>=1.0b2'
        ]
    },
    dependency_links=[
        'http://code.google.com/p/pyglet/downloads/list',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: AGPL License',
        'Programming Language :: Python :: 2 :: Only',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
