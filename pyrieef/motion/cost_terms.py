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

# from __future__ import print_function
from __init__ import *
from geometry.differentiable_geometry import *
from abc import ABCMeta, abstractproperty


class FiniteDifferencesVelocity(AffineMap):

    """ Define velocities where clique = [ x_t ; x_{t+1} ] """

    def __init__(self, dim, dt):
        self._a = np.matrix(np.zeros((dim, 2 * dim)))
        self._b = np.matrix(np.zeros((dim, 1)))
        self._initialize_matrix(dim, dt)

    def _initialize_matrix(self, dim, dt):
        """ Velocity = [ x_{t+1} - x_{t} ] / dt """
        I = np.eye(dim)
        self._a[0:dim, 0:dim] = -I
        self._a[0:dim, dim:(2 * dim)] = I
        self._a /= dt


class FiniteDifferencesAcceleration(AffineMap):

    """ Define accelerations where clique = [ x_{t-1} ; x_{t} ; x_{t+1} ] """

    def __init__(self, dim, dt):
        self._a = np.matrix(np.zeros((dim, 3 * dim)))
        self._b = np.matrix(np.zeros((dim, 1)))
        self._initialize_matrix(dim, dt)

    def _initialize_matrix(self, dim, dt):
        """ Acceleration = [ x_{t+1} + x_{t-1} - 2 * x_{t} ] / dt^2 """
        I = np.eye(dim)
        self._a[0:dim, 0:dim] = I
        self._a[0:dim, dim:(2 * dim)] = -2 * I
        self._a[0:dim, (2 * dim):(3 * dim)] = I
        self._a /= (dt * dt)


class SquaredNormDerivative(DifferentiableMap):

    """ Define any norm of derivatives clique = [x_t ; x_{t+1} ; ... ] """

    def __init__(self, dim):
        self._sq_norm = SquaredNorm(np.zeros(dim))
        return

    @abstractproperty
    def _derivative(self):
        pass

    def output_dimension(self):
        return 1

    def input_dimension(self):
        return self._derivative.input_dimension()

    def forward(self, clique):
        return self._sq_norm(self._derivative(clique))

    def jacobian(self, clique):
        d = self._derivative(clique)
        return self._derivative(clique) * self._derivative.a()

    def hessian(self, clique):
        return self._derivative.a().transpose() * self._derivative.a()


class SquaredNormVelocity(SquaredNormDerivative):

    """ Defines SN of velocities where clique = [x_t ; x_{t+1} ] """

    def __init__(self, dim, dt):
        SquaredNormDerivative.__init__(self, dim)
        self._derivative = FiniteDifferencesVelocity(dim, dt)


class SquaredNormAcceleration(SquaredNormDerivative):

    """ Defines SN of acceleration clique = [x_{t-1} ; x_{t} ; x_{t+1} ] """

    def __init__(self, dim, dt):
        SquaredNormDerivative.__init__(self, dim)
        self._derivative = FiniteDifferencesAcceleration(dim, dt)


class BoundBarrier(DifferentiableMap):

    """ Barrier between values """

    def __init__(self, v_lower, v_upper, margin=1e-10):
        assert v_lower.size == v_upper.size
        self._v_lower = v_lower
        self._v_upper = v_upper
        self._alpha = 1.
        self._margin = margin

    def output_dimension(self):
        return 1

    def input_dimension(self):
        return self._v_lower.size

    def forward(self, x):
        value = 0.
        for i, x_i in enumerate(x):
            l_dist = x_i - self._v_lower[i]
            u_dist = self._v_upper[i] - x_i
            if l_dist < self._margin or u_dist < self._margin:
                return float("inf")
            value += -self._alpha * np.log(l_dist)
            value += -self._alpha * np.log(u_dist)
        return value

    def jacobian(self, x):
        J = np.matrix(np.zeros((
            self.output_dimension(), self.input_dimension())))
        for i, x_i in enumerate(x):
            l_dist = x_i - self._v_lower[i]
            u_dist = self._v_upper[i] - x_i
            if l_dist < self._margin or u_dist < self._margin:
                return np.matrix(np.zeros((
                    self.output_dimension(), self.input_dimension())))
            J[0, i] += -self._alpha / l_dist
            J[0, i] += self._alpha / u_dist
        return J

    def hessian(self, x):
        H = np.matrix(np.zeros((
            self.input_dimension(), self.input_dimension())))
        for i, x_i in enumerate(x):
            l_dist = x_i - self._v_lower[i]
            u_dist = self._v_upper[i] - x_i
            if l_dist < self._margin or u_dist < self._margin:
                return np.matrix(np.zeros((
                    self.output_dimension(), self.output_dimension())))
            H[i, i] += self._alpha / (l_dist ** 2)
            H[i, i] += self._alpha / (u_dist ** 2)
        return H


class SimplePotential2D(DifferentiableMap):

    """ obstacle potential class """

    def __init__(self, signed_distance_field):
        assert signed_distance_field.input_dimension() == 2
        assert signed_distance_field.output_dimension() == 1
        self._sdf = signed_distance_field
        self._rho_scaling = 100.
        self._alpha = 10.
        self._margin = 0.

    def output_dimension(self):
        return 1

    def input_dimension(self):
        return 2

    def forward(self, x):
        return self._rho_scaling * np.exp(-self._alpha * self._sdf.forward(x))

    def _sdf_jacobian(self, x):
        sdf, J_sdf = self._sdf.evaluate(x)
        d_obs = sdf - self._margin
        rho = self._rho_scaling * np.exp(-self._alpha * d_obs)
        return J_sdf, rho

    def jacobian(self, x):
        J_sdf, rho = self._sdf_jacobian(x)
        return -self._alpha * rho * J_sdf

    def hessian(self, x):
        J_sdf, rho = self._sdf_jacobian(x)
        H_sdf = self._sdf.hessian(x)
        J_sdf_sq = J_sdf.transpose() * J_sdf
        return rho * (self._alpha**2 * J_sdf_sq - self._alpha * H_sdf)


class CostGridPotential2D(SimplePotential2D):

    """ obstacle potential class with margin and offset"""

    def __init__(self, signed_distance_field, alpha, margin, offset):
        SimplePotential2D.__init__(self, signed_distance_field)
        self._alpha = alpha
        self._margin = margin
        self._offset = offset

    def forward(self, x):
        d_obs = self._sdf.forward(x) - self._margin
        return self._rho_scaling * np.exp(-self._alpha * d_obs) + self._offset


class ObstaclePotential2D(DifferentiableMap):

    """ obstacle potential class """

    def __init__(self, signed_distance_field):
        assert signed_distance_field.input_dimension() == 2
        assert signed_distance_field.output_dimension() == 1
        self._sdf = signed_distance_field
        self._rho_scaling = 50.
        self._alpha = 1.e-3

    def output_dimension(self):
        return 3

    def input_dimension(self):
        return 2

    def forward(self, x):
        rho = np.exp(-self._alpha * self._sdf.forward(x))
        y = np.zeros(3)
        y[0] = self._rho_scaling * rho
        y[1] = x[0]
        y[2] = x[1]
        return y

    def jacobian(self, x):
        [sdf, J_sdf] = self._sdf.evaluate(x)
        rho = np.exp(-self._alpha * sdf)
        J = np.matrix(np.zeros((3, 2)))
        J[0, :] = -self._alpha * self._rho_scaling * rho * J_sdf
        J[1:3, :] = np.matrix(np.eye(2, 2))
        return J

    def hessian(self, x):
        J_phi = self.jacobian().transpose()
        return J_phi.transpose() * J_phi
