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
from __init__ import *
from motion.trajectory import *
from motion.cost_terms import *
from motion.objective import *
import time
from numpy.linalg import norm

np.random.seed(0)


def test_finite_differences():
    dim = 4
    acceleration = FiniteDifferencesAcceleration(dim, 1)
    print acceleration.jacobian(np.zeros(dim * 3))
    assert check_jacobian_against_finite_difference(acceleration)

    velocity = FiniteDifferencesVelocity(dim, 1)
    print velocity.jacobian(np.zeros(dim * 3))
    assert check_jacobian_against_finite_difference(acceleration)


def test_cliques():
    A = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    cliques = [A[i:3 + i] for i in range(len(A) - 2)]
    print A
    print cliques
    assert len(cliques) == (len(A) - 2)

    dimension = 10
    network = CliquesFunctionNetwork(dimension, 1)
    x_0 = np.zeros(3)
    for _ in range(network.nb_cliques()):
        network.add_function(SquaredNorm(x_0))
    cliques = network.all_cliques(A)
    print cliques
    assert len(cliques) == (len(A) - 2)


def test_trajectory():
    T = 10
    n = 2

    traj = Trajectory(T)
    print type(traj)
    print traj

    size = n * (T + 2)  # This is the formula for n = 2

    traj.set(np.ones(size))
    print type(traj)
    print str(traj)

    traj.set(np.random.rand(size))
    print type(traj)
    print str(traj)

    print "final configuration : "
    print traj.final_configuration()

    print "config 3 : "
    print traj.configuration(3)

    print "clique 3 : "
    print traj.clique(3)

    print "config 3 (ones) : "
    traj.configuration(3)[:] = np.ones(n)
    print traj.configuration(3)

    print "final configuration (ones) : "
    traj.final_configuration()[:] = np.ones(n)
    print traj.final_configuration()

    x_active = np.random.random(n * (T + 1))
    traj = Trajectory(q_init=np.zeros(n), x=x_active)
    print("x_active : ", x_active)
    print("traj.x : ", traj.x())
    assert traj.x().size == size
    assert np.isclose(traj.x()[:2], np.zeros(n)).all()


def test_continuous_trajectory():
    q_init = np.random.random(2)
    q_goal = np.random.random(2)
    trajectory_1 = linear_interpolation_trajectory(q_init, q_goal, 10)
    trajectory_2 = ContinuousTrajectory(7, 2)
    trajectory_2.set(linear_interpolation_trajectory(q_init, q_goal, 7).x())
    for k, s in enumerate(np.linspace(0., 1., 11)):
        q_1 = trajectory_2.configuration_at_parameter(s)
        q_2 = trajectory_1.configuration(k)
        assert_allclose(q_1, q_2)


def test_obstacle_potential():

    # np.random.seed(0)

    workspace = Workspace()
    for center, radius in sample_circles(nb_circles=10):
        workspace.obstacles.append(Circle(center, radius))
    sdf = SignedDistanceWorkspaceMap(workspace)
    phi = ObstaclePotential2D(sdf)
    print "Checkint Obstacle Potential"
    assert check_jacobian_against_finite_difference(phi)

    phi = SimplePotential2D(sdf)
    print "Checkint Simple Potential Gradient"
    assert check_jacobian_against_finite_difference(phi)
    print "Checkint Simple Potential Hessian"
    assert check_hessian_against_finite_difference(phi)

    phi = CostGridPotential2D(sdf, 10, 0.1, 1.)
    print "Checkint Grid Potential Gradient"
    assert check_jacobian_against_finite_difference(phi)
    print "Checkint Grid Potential Hessian"
    assert check_hessian_against_finite_difference(phi)


def test_squared_norm_derivatives():

    f = SquaredNormVelocity(2, dt=0.1)

    print "Check SquaredNormVelocity (J implementation) : "
    assert check_jacobian_against_finite_difference(f)

    print "Check SquaredNormVelocity (H implementation) : "
    assert check_hessian_against_finite_difference(f)

    f = SquaredNormAcceleration(2, dt=0.1)

    print "Check SquaredNormAcceleration (J implementation) : "
    assert check_jacobian_against_finite_difference(f)

    print "Check SquaredNormAcceleration (H implementation) : "
    assert check_hessian_against_finite_difference(f)


def test_center_of_clique():
    config_dim = 2
    nb_way_points = 10
    trajectory = linear_interpolation_trajectory(
        q_init=np.zeros(2),
        q_goal=np.ones(2),
        T=nb_way_points)
    network = CliquesFunctionNetwork(trajectory.x().size, config_dim)
    center_of_clique = network.center_of_clique_map()
    network.register_function_for_all_cliques(center_of_clique)
    for t, x_t in enumerate(network.all_cliques(trajectory.x())):
        assert (np.linalg.norm(network.function_on_clique(t, x_t) -
                               x_t[2:4]) < 1.e-10)


def test_motion_optimimization_smoothness_metric():
    print "Checkint Motion Optimization"
    objective = MotionOptimization2DCostMap()
    A = objective.create_smoothness_metric()


def calculate_analytical_gradient_speedup(f, nb_points=10):
    samples = np.random.rand(nb_points, f.input_dimension())
    time1 = time.time()
    [f.gradient(x) for x in samples]
    time2 = time.time()
    t_analytic = (time2 - time1) * 1000.0
    print '%s function took %0.3f ms' % ("analytic", t_analytic)
    time1 = time.time()
    [finite_difference_jacobian(f, x) for x in samples]
    time2 = time.time()
    t_fd = (time2 - time1) * 1000.0
    print '%s function took %0.3f ms' % ("finite diff", t_fd)
    print " -- speedup : {} x".format(int(round(t_fd / t_analytic)))


def test_motion_optimimization_2d():

    np.random.seed(0)

    print "Check Motion Optimization (Derivatives)"
    objective = MotionOptimization2DCostMap()
    trajectory = Trajectory(objective.T)
    sum_acceleration = objective.cost(trajectory)
    print "sum_acceleration : ", sum_acceleration
    q_init = np.zeros(2)
    q_goal = np.ones(2)
    trajectory = linear_interpolation_trajectory(
        q_init, q_goal, objective.T)
    print trajectory
    print trajectory.final_configuration()
    sum_acceleration = objective.cost(trajectory)
    print "sum_acceleration : ", sum_acceleration

    print "Test J for trajectory"
    assert check_jacobian_against_finite_difference(
        objective.objective, False)

    # Check the hessian of the trajectory
    print "Test H for trajectory"
    is_close = check_hessian_against_finite_difference(
        objective.objective, False, tolerance=1e-2)

    xi = np.random.rand(objective.objective.input_dimension())
    H = objective.objective.hessian(xi)
    H_diff = finite_difference_hessian(objective.objective, xi)
    H_delta = H - H_diff
    print " - H_delta dist = ", np.linalg.norm(H_delta, ord='fro')
    print " - H_delta maxi = ", np.max(np.absolute(H_delta))

    assert is_close

    # Calulate speed up.
    # print "Calculat analytic gradient speedup"
    # calculate_analytical_gradient_speedup(objective.objective)


def test_linear_interpolation():
    trajectory = linear_interpolation_trajectory(
        q_init=np.zeros(2),
        q_goal=np.ones(2),
        T=22
    )
    q_1 = trajectory.configuration(0)
    q_2 = trajectory.configuration(1)
    dist = norm(q_1 - q_2)
    for i in range(1, trajectory.T() + 1):
        q_1 = trajectory.configuration(i)
        q_2 = trajectory.configuration(i + 1)
        dist_next = norm(q_1 - q_2)
        assert abs(dist_next - dist) < 1.e-10


def test_linear_interpolation_velocity():
    dim = 2
    dt = 0.1
    deriv = SquaredNormVelocity(dim, dt)
    deriv_comp = Pullback(
        SquaredNorm(np.zeros(dim)), FiniteDifferencesVelocity(dim, dt))
    trajectory = linear_interpolation_trajectory(
        q_init=np.zeros(dim),
        q_goal=np.ones(dim),
        T=22
    )
    q_1 = trajectory.configuration(0)
    q_2 = trajectory.configuration(1)
    g_traj = np.zeros(trajectory.x().shape)
    clique = np.append(q_1,  q_2)
    velocity = deriv(clique)
    gradient_1 = deriv.gradient(clique)
    for i in range(0, trajectory.T() + 1):
        q_1 = trajectory.configuration(i)
        q_2 = trajectory.configuration(i + 1)
        clique = np.append(q_1,  q_2)
        velocity_next = deriv(clique)
        gradient_2 = deriv.gradient(clique)
        # g_traj[i + 1: i + 1 + dim] += gradient_2
        print("i = {}, g2 : {}".format(i, gradient_2))
        assert abs(velocity - velocity_next) < 1.e-10
        assert norm(deriv_comp.gradient(clique) - gradient_2) < 1.e-10
        assert norm(gradient_1[0:2] + gradient_2[2:4]) < 1.e-10
    print g_traj


def test_linear_interpolation_optimal_potential():
    """ makes sure that the start and goal potentials
        are applied at the correct place """
    trajectory = linear_interpolation_trajectory(
        q_init=np.zeros(2),
        q_goal=np.ones(2),
        T=10
    )
    objective = MotionOptimization2DCostMap(
        T=trajectory.T(),
        q_init=trajectory.initial_configuration(),
        q_goal=trajectory.final_configuration()
    )
    # print "q_init  : ", trajectory.initial_configuration()
    # print "q_goal  : ", trajectory.final_configuration()
    # objective.create_clique_network()
    # objective.add_init_and_terminal_terms()
    # objective.create_objective()
    # v = objective.objective.forward(trajectory.active_segment())
    # g = objective.objective.gradient(trajectory.active_segment())
    # print v
    # assert abs(v - 0.) < 1.e-10
    # assert np.isclose(g, np.zeros(trajectory.active_segment().shape)).all()

    # TODO test velocity profile. Gradient should correspond.
    # This is currently not the case.
    # assert check_jacobian_against_finite_difference(objective.objective, False)
    objective.create_clique_network()
    objective.add_smoothness_terms(2)
    objective.create_objective()
    v = objective.objective.forward(trajectory.active_segment())
    g = objective.objective.gradient(trajectory.active_segment())
    g_diff = finite_difference_jacobian(
        objective.objective, trajectory.active_segment())
    print "v : ", v
    print "x : ", trajectory.active_segment()
    print "g : ", g
    print "g_diff : ", g_diff
    print g.shape
    assert np.isclose(
        g, np.zeros(trajectory.active_segment().shape), atol=1e-5).all()


def test_optimize():
    print "Check Motion Optimization (optimize)"
    q_init = np.zeros(2)
    objective = MotionOptimization2DCostMap()
    objective.optimize(q_init, nb_steps=5)

if __name__ == "__main__":
    test_trajectory()
    test_continuous_trajectory()
    test_cliques()
    test_finite_differences()
    test_squared_norm_derivatives()
    test_obstacle_potential()
    test_motion_optimimization_2d()
    test_motion_optimimization_smoothness_metric()
    test_optimize()
    test_center_of_clique()
    test_linear_interpolation()
    test_linear_interpolation_velocity()
    test_linear_interpolation_optimal_potential()
