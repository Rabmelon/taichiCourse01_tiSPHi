import taichi as ti
import numpy as np
from eng.guishow import *
from eng.gguishow import *
from eng.particle_system import *
from eng.muIsph import *
from eng.wcsph import *

# TODO: make unit testing for basic functions of SPH

# ti.init(arch=ti.cpu, debug=True)
ti.init(arch=ti.cuda, packed=True, device_memory_fraction=0.75)     # MEMORY max 4G in GUT, 6G in Legion
# ti.init(arch=ti.vulkan)

if __name__ == "__main__":
    print("hallo tiSPHi!")

    # init particle system paras, world unit is cm (BUT not cm actually! maybe still m)
    screen_to_world_ratio = 500   # exp: world = (150, 100), ratio = 4, screen res = (600, 400)
    rec_world = [1.2, 0.8]   # a rectangle world start from (0, 0) to this pos
    particle_radius = 0.001
    cube_size = [0.2, 0.4]

    mat = 2
    rho = 1680.0
    TDmethod = 1    # 1 Symp Euler; 2 RK4
    flag_kernel = 1 # 1 cubic-spline; 2 Wenland

    case1 = ParticleSystem(rec_world, particle_radius)
    case1.add_cube(lower_corner=[0.0, 0], cube_size=cube_size, color=(149/255,99/255,51/255), material=mat, density=rho)

    if mat == 1:
        solver = WCSPHSolver(case1, TDmethod, flag_kernel)
    elif mat == 2:
        solver = MCmuISPHSolver(case1, TDmethod, flag_kernel, rho, 0, 29, 0)

    gguishow(case1, solver, rec_world, screen_to_world_ratio, stepwise=50, iparticle=None, color_title="d density N/m3/s", kradius=1.5, write_to_disk=0)

    # color title: pressure Pa; density N/m3; velocity m/s;
