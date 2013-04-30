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
    namespace_packages=['wasabi'],
    install_requires=[
        'pyglet>=1.2alpha1',
        'euclid>=0.1',
        'gletools>=0.1.0'
    ],
    extras_requires={
        'particles': [
            'lepton>=1.0b2'
        ]
    },
    dependency_links=[
        'http://code.google.com/p/pyglet/downloads/list',
        'hg+http://hg.codeflow.org/gletools@da011bbc16d0db3f42441fe11556fefc58e6835c#egg=gletools-0.1.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: AGPL License',
        'Programming Language :: Python :: 2 :: Only',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
