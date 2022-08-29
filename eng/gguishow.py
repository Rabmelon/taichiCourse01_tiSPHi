import taichi as ti
import numpy as np
import os
import csv
from datetime import datetime

# TODO: add different color choice
# TODO: try to make a single color selector!!!

def gguishow(case, solver, world, s2w_ratio=1,
             step_ggui=1, pause_flag=True, stop_step=0, exit_flag=False,
             save_png=0, save_msg=False, iparticle=None,
             kradius=1.0, grid_line=None, color_title=None,
             given_max=-1, given_min=-1, fix_max=0, fix_min=0):
    print("ggui starts to serve!")

    # basic paras
    drawworld = [i + 2 * case.grid_size for i in world]
    res = (np.array(drawworld) * s2w_ratio).astype(int)
    w2s=s2w_ratio / res.max()
    window = ti.ui.Window('tiSPHi window', res=(max(res), max(res)))
    canvas = window.get_canvas()
    canvas.set_background_color((1,1,1))

    # draw grid line
    if grid_line is not None and grid_line != 0.0:
        if not isinstance(grid_line,list):
            grid_line = [grid_line for _ in range(case.dim)]
        num_grid_point = [int((world[i] - 1e-8) // grid_line[i]) for i in range(case.dim)]
        num_all_grid_point = sum(num_grid_point)
        num_all2_grid_point = 2 * num_all_grid_point
        np_pos_line = np.array([[0.0 for _ in range(case.dim)] for _ in range(num_all2_grid_point)], dtype=np.float32)
        np_indices_line = np.array([[i, i + num_all_grid_point] for i in range(num_all_grid_point)], dtype=np.int32)
        pos_line = ti.Vector.field(case.dim, ti.f32, shape=num_all2_grid_point)
        indices_line = ti.Vector.field(2, ti.i32, shape=num_all_grid_point)
        indices_line.from_numpy(np_indices_line)
        for id in range(case.dim):
            id2 = case.dim - 1 - id
            for i in range(num_grid_point[id]):
                np_pos_line[i + sum(num_grid_point[0:id])][id] = (i + 1) * grid_line[id]
                np_pos_line[i + sum(num_grid_point[0:id]) + num_all_grid_point][id] = (i + 1) * grid_line[id]
                np_pos_line[i + sum(num_grid_point[0:id]) + num_all_grid_point][id2] = world[id2]
        pos_line.from_numpy((np_pos_line + case.grid_size) * w2s)

    # control paras
    count_step = 0
    count_stop = 0
    show_pos = [0.0, 0.0]
    show_grid = [0, 0]
    max_res = int(res.max())
    str_color_title = chooseColorTitle(color_title)

    # save png path
    cappath = os.getcwd() + r"\screenshots"
    if save_png > 0 or save_msg:
        timestamp = datetime.today().strftime('%Y_%m_%d_%H%M%S')
        simpath = os.getcwd() + "\\sim_" + timestamp
        if not os.path.exists(simpath):
            os.mkdir(simpath)
        os.chdir(simpath)

    # prepare to draw iparticle(s)
    if iparticle is not None:
        num_ip = 1
        if isinstance(iparticle, list):
            num_ip = len(iparticle)
        i_pos = ti.Vector.field(case.dim, ti.f32, shape=num_ip)
        tmp_pos = np.array([[0.0 for _ in range(case.dim)] for _ in range(num_ip)])

    # save messages into txt
    if save_msg and iparticle is not None:
        timestamp = datetime.today().strftime('%Y_%m_%d_%H%M%S')
        savecsv = simpath + "\\msg_" + timestamp + ".csv"
        fid = open(savecsv, "w", encoding="utf-8", newline='')
        fid_writer = csv.writer(fid)
        str_row0 = ["step"]
        save_title = ["pid", "posx", "posy", "vx", "vy", "rho", "sxx", "syy", "sxy", "szz"]
        if not isinstance(iparticle, list):
            iparticle = [iparticle]
        for ip in iparticle:
            str_row0 += save_title
        fid_writer.writerow(str_row0)

    # main loop
    while window.running:
        if not pause_flag:
            # print or save msg in iparticle(s)
            if iparticle is not None:
                if not save_msg and not isinstance(iparticle, list) and iparticle >= 0:
                    str_msg = "---- %06d, p[%d]: x=(%.6f, %.6f), v=(%.6f, %.6f), ρ=%.3f, σ=(%.6f, %.6f, %.6f, %.6f)" % (count_step, iparticle, solver.ps.x[iparticle][0], solver.ps.x[iparticle][1], solver.ps.v[iparticle][0], solver.ps.v[iparticle][1], solver.ps.density[iparticle], solver.stress[iparticle][0,0], solver.stress[iparticle][1,1], solver.stress[iparticle][0,1], solver.stress[iparticle][2,2])
                    print(str_msg)
                if save_msg:
                    if not isinstance(iparticle, list):
                        iparticle = [iparticle]
                    str_i = [count_step]
                    for ip in iparticle:
                        istr_data = [ip, solver.ps.x[ip][0], solver.ps.x[ip][1], solver.ps.v[ip][0], solver.ps.v[ip][1], solver.ps.density[ip], solver.stress[ip][0,0], solver.stress[ip][1,1], solver.stress[ip][0,1], solver.stress[ip][2,2]]
                        # istr_data = "\t%d\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f" % (ip, solver.ps.x[ip][0], solver.ps.x[ip][1], solver.ps.v[ip][0], solver.ps.v[ip][1], solver.ps.density[ip], solver.stress[ip][0,0], solver.stress[ip][1,1], solver.stress[ip][0,1], solver.stress[ip][2,2])
                        str_i += istr_data
                    fid_writer.writerow(str_i)

            for i in range(step_ggui):
                solver.step()
                count_step += 1

        # draw grids
        if grid_line is not None and grid_line != 0.0:
            canvas.lines(pos_line, 0.0025, indices_line, (0.8, 0.8, 0.8))   # ! WARRNING: Overriding last binding

        # draw particles
        solver.ps.copy2vis(s2w_ratio, max_res)
        solver.init_value()
        solver.ps.v_maxmin(given_max, given_min, fix_max, fix_min)
        solver.ps.set_color()
        draw_radius = solver.ps.particle_radius * s2w_ratio * kradius / max_res
        canvas.circles(solver.ps.pos2vis, radius=draw_radius, per_vertex_color=solver.ps.color)   # ! WARRNING: Overriding last binding

        # draw iparticle(s)
        if iparticle is not None:
            if not isinstance(iparticle, list):
                iparticle = [iparticle]
            for nip in range(num_ip):
                tmp_pos[nip] = solver.ps.pos2vis[iparticle[nip]]
            i_pos.from_numpy(tmp_pos)
            canvas.circles(i_pos, radius=1.5*draw_radius, color=(1.0, 0.0, 0.0))   # ! WARRNING: Overriding last binding

        # show text
        window.GUI.begin("Info", 0.03, 0.03, 0.4, 0.3)
        window.GUI.text('Total particle number: {pnum:,}'.format(pnum=solver.ps.particle_num[None]))
        window.GUI.text('Step: {fstep:,}'.format(fstep=count_step))
        window.GUI.text('Time: {t:.6f}s, dt={dt:.6f}s'.format(t=solver.dt[None] * count_step, dt=solver.dt[None]))
        window.GUI.text('Pos: {px:.3f}, {py:.3f}'.format(px=show_pos[0], py=show_pos[1]))
        window.GUI.text('Grid: {gx:.1f}, {gy:.1f}'.format(gx=show_grid[0], gy=show_grid[1]))
        window.GUI.text('colorbar: {str}'.format(str=str_color_title))
        window.GUI.text('max value: {maxv:.3f}'.format(maxv=solver.ps.vmax[None]))
        window.GUI.text('min value: {minv:.3f}'.format(minv=solver.ps.vmin[None]))
        window.GUI.end()

        # control
        for e in window.get_events(ti.ui.PRESS):
            if e.key == ti.ui.ESCAPE:
                window.running = False
            elif e.key == ti.ui.SPACE:
                pause_flag = not pause_flag
            elif e.key == ti.ui.LMB:
                show_pos = [i / s2w_ratio * max_res - case.grid_size for i in window.get_cursor_pos()]
                show_grid = [(i - j) // case.grid_size for i,j in zip(show_pos, case.bound[0])]
        if window.is_pressed('p'):
            captureScreen(window, cappath)
        if stop_step > 0 and count_step > stop_step - step_ggui and count_stop == 0:
            pause_flag = True
            count_stop += 1
            if exit_flag:
                captureScreen(window, cappath)
                window.running = False

        # output
        if save_png > 0 and count_step % (save_png * step_ggui) == 0:
            window.save_image(f"{count_step:06d}.png")

        window.show()

    if save_msg and iparticle is not None:
        fid.close()

def captureScreen(window, cappath):
    timestamp = datetime.today().strftime('%Y_%m_%d_%H%M%S')
    fname = os.path.join(cappath, f"screenshot{timestamp}.jpg")
    window.save_image(fname)
    print(f"Screenshot has been saved to {fname}")

def chooseColorTitle(flag):
    if flag is not None:
        if isinstance(flag, str):
            res = flag
        elif flag == 1:
            res = "index"
        elif flag == 2:
            res = "density kg/m3"
        elif flag == 21:
            res = "d density kg/m3/s"
        elif flag == 3:
            res = "velocity norm m/s"
        elif flag == 31:
            res = "velocity x m/s"
        elif flag == 32:
            res = "velocity y m/s"
        elif flag == 33:
            res = "velocity z m/s"
        elif flag == 4:
            res = "position m"
        elif flag == 41:
            res = "position x m"
        elif flag == 42:
            res = "position y m"
        elif flag == 43:
            res = "position z m"
        elif flag == 5:
            res = "stress Pa"
        elif flag == 51:
            res = "stress xx Pa"
        elif flag == 52:
            res = "stress yy Pa"
        elif flag == 53:
            res = "stress zz Pa"
        elif flag == 54:
            res = "stress xy Pa"
        elif flag == 55:
            res = "stress yz Pa"
        elif flag == 56:
            res = "stress zx Pa"
        elif flag == 57:
            res = "stress hydro Pa"
        elif flag == 58:
            res = "stress devia Pa"
        elif flag == 6:
            res = "strain"
        elif flag == 61:
            res = "strain pla equ"
        elif flag == 7:
            res = "displacement norm m"
        elif flag == 8:
            res = "pressure Pa"
        else:
            res = "Null"
    return res

###########################################################################
# colored value
###########################################################################
# @ti.kernel
# def init_value(solver, flag):
#     for p_i in range(solver.ps.particle_num[None]):
#         if solver.ps.material[p_i] < 10:
#             if flag == 1:
#                 """index"""
#                 solver.ps.val[p_i] = p_i
#             elif flag == 2:
#                 """density kg/m3"""
#                 solver.ps.val[p_i] = solver.ps.density[p_i]
#             elif flag == 21:
#                 """d density kg/m3/s"""
#                 solver.ps.val[p_i] = solver.d_density[p_i]
#             elif flag == 3:
#                 """velocity norm m/s"""
#                 solver.ps.val[p_i] = solver.ps.v[p_i].norm()
#             elif flag == 31:
#                 """velocity x m/s"""
#                 solver.ps.val[p_i] = solver.ps.v[p_i][0]
#             elif flag == 32:
#                 """velocity y m/s"""
#             elif flag == 33:
#                 """velocity z m/s"""
#             elif flag == 4:
#                 """position m"""
#             elif flag == 41:
#                 """position x m"""
#             elif flag == 42:
#                 """position y m"""
#             elif flag == 43:
#                 """position z m"""
#             elif flag == 5:
#                 """stress Pa"""
#             elif flag == 51:
#                 """stress xx Pa"""
#             elif flag == 52:
#                 """stress yy Pa"""
#                 solver.ps.val[p_i] = -solver.stress[p_i][1,1]
#             elif flag == 53:
#                 """stress zz Pa"""
#             elif flag == 54:
#                 """stress xy Pa"""
#             elif flag == 55:
#                 """stress yz Pa"""
#             elif flag == 56:
#                 """stress zx Pa"""
#             elif flag == 57:
#                 """stress hydro Pa"""
#             elif flag == 58:
#                 """stress devia Pa"""
#                 solver.ps.val[p_i] = solver.strain_p_equ[p_i]
#             elif flag == 6:
#                 """strain"""
#             elif flag == 61:
#                 """strain pla equ"""
#             elif flag == 7:
#                 """displacement norm m"""
#                 solver.ps.val[p_i] = ti.sqrt(((solver.ps.x[p_i] - solver.ps.x0[p_i])**2).sum())
#             elif flag == 8:
#                 """pressure Pa"""
#                 solver.ps.val[p_i] = solver.pressure[p_i]
#             else:
#                 """Null"""
#                 solver.ps.val[p_i] = 0.0
