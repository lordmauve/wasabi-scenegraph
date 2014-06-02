"""Run regression tests against Wasabi-Scenegraph.

We compare the current rendering of the initial frame of each demo with a
reference rendering.

This will call each demo in turn and get them to spit out a screenshot. Each
screenshot will be compared to the reference rendering.

"""
import sys
import os
import os.path
import subprocess
import math
import operator
import unittest
import time
try:
    from PIL import Image
    from PIL import ImageChops
except ImportError:
    raise ImportError("PIL is required to run regression tests.")

# Root directory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"
    hist = ImageChops.difference(im1, im2).histogram()

    channels = [
        hist[:256],
        hist[256:512],
        hist[512:768],
        hist[768:]
    ]

    # calculate rms
    return math.sqrt(
        sum(h * (i ** 2) for c in channels for i, h in enumerate(c)) /
        (float(im1.size[0]) * im1.size[1] * 4)
    )


class RegressionTest(object):
    DEMO = None

    def setUp(self):
        self.cwd = os.getcwd()
        os.chdir(os.path.join(ROOT, 'demos', self.DEMO))

    def tearDown(self):
        os.chdir(self.cwd)

    def runTest(self):
        script = '%s.py' % self.DEMO
        if not os.path.exists(script):
            self.fail('Script %s does not exist' % script)
        proc = subprocess.Popen(['python', script, '-s', 'output.png'])
        for _ in xrange(40):
            if proc.poll():
                break
            time.sleep(0.05)
        if proc.returncode is None:
            proc.terminate()
            self.fail('Failed to write screenshot after 2s')
        if proc.returncode:
            self.fail('Exited with code %d' % proc.returncode)
        elif not os.path.exists('output.png'):
            self.fail('Failed to write screenshot')

        if not os.path.exists('reference.png'):
            raise unittest.SkipTest(
                'No reference image available (rename demos/%s/output.png to '
                'demos/%s/refererence.png if it is acceptable)' % (
                    self.DEMO, self.DEMO
                )
            )

        rms = rmsdiff(
            Image.open('output.png'),
            Image.open('reference.png'),
        )
        self.assertLess(
            rms, 10.0,
            msg="Output differs from reference image (rms = %0.1f)" % rms
        )


def load():
    demos = os.listdir(os.path.join(ROOT, 'demos'))
    bases = (RegressionTest, unittest.TestCase)
    for d in demos:
        clsname = '%s_RegressionTest' % d
        cls = type(clsname, bases, {'DEMO': d})
        globals()[clsname] = cls


load()
