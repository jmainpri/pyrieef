#!/usr/bin/env python

# Copyright (c) 2015 Max Planck Institute
# All rights reserved.
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without   fee is hereby granted, provided   that the above  copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS  SOFTWARE INCLUDING ALL  IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR  BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR  ANY DAMAGES WHATSOEVER RESULTING  FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION,   ARISING OUT OF OR IN    CONNECTION WITH THE USE   OR
# PERFORMANCE OF THIS SOFTWARE.
#
# Jim Mainprice on Sunday June 17 2018

from __future__ import print_function
from common_imports import *


class Trajectory:

    def __init__(self, T=0, n=2):
        assert T > 0 and n > 0
        self._n = n
        self._T = T
        self._x = np.zeros(n * (2 + T))

    def __str__(self):
        ss = ""
        ss += " - n : " + str(self._n) + "\n"
        ss += " - T : " + str(self._T) + "\n"
        ss += " - x : " + str(self._x)
        return ss

    def final_configuration(self):
        return self.configuration(self._T)

    def configuration(self, i):
        """ To get a mutable part : 
            traj.configuration(3)[:] = np.ones(2)
        """
        beg_idx = self._n * i
        end_idx = self._n * (i + 1)
        return self._x[beg_idx:end_idx]

    def clique(self, i):
        assert i > 0
        beg_idx = self._n * (i - 1)
        end_idx = self._n * (i + 2)
        return self._x[beg_idx:end_idx]

    def set(self, x):
        assert x.shape[0] == self._n * (2 + self._T)
        self._x = x
