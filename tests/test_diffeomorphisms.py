import test_common_imports
from test_differentiable_geometry import *
from diffeomorphisms import *


def CheckBeta(alpha, beta, beta_inv):
    success = False
    for i in range(1000):
        eta=.001
        r=.2
        gamma=3.
        dx = np.random.rand(1)[0]
        # print dx
        dy = beta(eta, r, gamma, dx)
        dx_new = beta_inv(eta, r, gamma, dy)
        if np.fabs( dx - dx_new ) > 1.e-12 :
            print "test beta (", i, ")"
            print " -- value : ", dx
            print " -- forward : ", dy
            print " -- inverse : ", dx_new
            print "Error."
            success = False
            break
        
        # print "x = ", x, " , y = ", y , " , x_new = ", x_new
        # print "Ok."
        success = True
    return success

def CheckInverse(obstacle):
    success = True 
    o = obstacle.object()
    print "center : ", o.origin
    print  "radius : ", o.radius
    # np.random.seed(0)
    if success:
        success = False
        for i in range(1000):
            x = 1. * np.random.rand(2) + o.origin
            if np.linalg.norm(x - o.origin) < o.radius :
                continue
            p = obstacle.Forward(x)
            x_new = obstacle.Inverse(p)
            dist = np.linalg.norm(x - x_new)
            if dist > 1.e-12:
                print "test (", i, ")"
                print " -- norm : ", np.linalg.norm(x)
                print " -- point : ", x
                print " -- forward : ", p
                print " -- inverse : ", x_new
                print "Error."
                success = False
                break
            success = True
    return success

def test_inverse_functions():

    assert CheckBeta(alpha_f, beta_f, beta_inv_f)
    assert CheckBeta(alpha2_f, beta2_f, beta2_inv_f)

    # TODO look why this one fails...
    # assert CheckBeta(alpha3_f, beta3_f, beta3_inv_f)

    print "Test PolarCoordinateSystem"
    obstacle = PolarCoordinateSystem()
    assert CheckJacobianAgainstFiniteDifference(obstacle)
    assert CheckInverse(obstacle)

    print "Test ElectricCircle"
    obstacle = ElectricCircle()
    assert CheckJacobianAgainstFiniteDifference(obstacle)
    assert CheckInverse(obstacle)

    print "Test AnalyticCircle"
    obstacle = AnalyticCircle()
    obstacle.set_alpha(alpha_f, beta_inv_f)
    assert CheckJacobianAgainstFiniteDifference(obstacle)
    assert CheckInverse(obstacle)

    # obstacle = AnalyticEllipse()
    # obstacle.set_alpha(alpha_f, beta_inv_f)
    # if CheckInverse(obstacle):
    #     print "Analytic Ellipse OK !!!"
    # else:
    #     print "Analytic Ellipse Error !!!"

    print "Done."


if __name__ == "__main__":
    test_inverse_functions()