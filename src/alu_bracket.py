import FreeCAD
import Part 
import Draft
import Mesh
import MeshPart
import DraftVecUtils
import logging
import inspect

import os
import sys

filepath = os.getcwd()
sys.path.append(filepath)

import kcomp
import fcfun
import comps
import kparts
import shp_clss
import fc_clss
import NuevaClase

from NuevaClase import Obj3D
from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, addCyl_pos, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL

stl_dir = "/stl/"

logging.basicConfig(level = logging.DEBUG, format = '%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class alu_bracket(Obj3D):
    """
    """
    def __init__(self, n_bolt = 1, bra_w_1 = 22., bra_w_2 = 17., bra_d_1 = 21., bra_d_2 = 51., bra_h_1 = 21., bra_h_2 = 51., bolt = 5., rail = 1, d_rail = 10., reinf_thick_1 = 3., reinf_thick_2 = 5., wall_thick = 6., chmf_r = 1., dist_bet_nuts = 17., dist_hole = 5., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'alu_bracket'
        self.set_name(name, default_name, change = 0)
        Obj3D.__init__(self, axis_d, axis_w, axis_h, self.name)

        # save the arguments as attributes:
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i):
                setattr(self, i, values[i])

        self.pos = FreeCAD.Vector(0, 0, 0)
        self.position = pos

        # normal axes to print without support
        self.prnt_ax = self.axis_h

        # calculation of the bolt to hold the bottom coverplate to the wood
        self.boltshank_r_tol = kcomp.D912[bolt]['shank_r_tol']
        self.bolthead_r = kcomp.D912[bolt]['head_l']
        self.bolthead_r_tol = kcomp.D912[bolt]['head_r']
        self.bolthead_l = kcomp.D912[bolt]['head_l']

        # making the big box that will contain everything and will be cut
        if n_bolt == 1:
            self.tot_d = bra_d_1 + wall_thick  
            self.tot_w = bra_w_1 + 2 * reinf_thick_1
            self.tot_h = bra_h_1 + wall_thick
        else:
            self.tot_d = bra_d_2 + wall_thick
            self.tot_w = bra_w_2 + 2 * reinf_thick_2
            self.tot_h = bra_h_2 + wall_thick

        # definition of which axis is symmetrical
        if n_bolt == 1:
            self.h0_cen = 0
            self.w0_cen = 1   # symmetrical 
            self.d0_cen = 0
        else:
            self.h0_cen = 0
            self.w0_cen = 0   
            self.d0_cen = 0

        if n_bolt == 1:
            # vectors from the origin to the points along axis_h
            self.h_o[0] = V0
            self.h_o[1] = self.vec_h(wall_thick)
            self.h_o[2] = self.vec_h(wall_thick + dist_hole)
            self.h_o[3] = self.vec_h(wall_thick + bra_h_1/2.)
            self.h_o[4] = self.vec_h(wall_thick + dist_hole + d_rail)
            self.h_o[5] = self.vec_h(self.tot_h)
            # position along axis_d
            self.d_o[0] = V0
            self.d_o[1] = self.vec_d(dist_hole)
            self.d_o[2] = self.vec_d(dist_hole + d_rail)
            self.d_o[3] = self.vec_d(bra_d_1/2.)
            self.d_o[4] = self.vec_d(bra_d_1)
            self.d_o[5] = self.vec_d(self.tot_d)
            # position along axis_w
            self.w_o[0] = V0
            self.w_o[1] = self.vec_w(-self.boltshank_r_tol)
            self.w_o[2] = self.vec_w(-bra_w_1/2.)
            self.w_o[3] = self.vec_w(-self.tot_w/2.)
        else:
            # vectors from the origin to the points along axis_h
            self.h_o[0] = V0
            self.h_o[1] = self.vec_h(wall_thick)
            self.h_o[2] = self.vec_h(wall_thick + dist_hole)
            self.h_o[3] = self.vec_h(wall_thick + dist_hole + d_rail/2.)
            self.h_o[4] = self.vec_h(wall_thick + dist_hole + d_rail)
            self.h_o[5] = self.vec_h(wall_thick + dist_hole + d_rail + dist_bet_nuts)
            self.h_o[6] = self.vec_h(wall_thick + dist_hole + d_rail + dist_bet_nuts + d_rail/2.)
            self.h_o[7] = self.vec_h(wall_thick + dist_hole + d_rail + dist_bet_nuts + d_rail)
            self.h_o[8] = self.vec_h(self.tot_h)
            # position along axis_d
            self.d_o[0] = V0
            self.d_o[1] = self.vec_d(dist_hole)
            self.d_o[2] = self.vec_d(dist_hole + d_rail/2.)
            self.d_o[3] = self.vec_d(dist_hole + d_rail)
            self.d_o[4] = self.vec_d(dist_hole + d_rail + dist_bet_nuts)
            self.d_o[5] = self.vec_d(dist_hole + d_rail + dist_bet_nuts + d_rail/2.)
            self.d_o[6] = self.vec_d(dist_hole + d_rail + dist_bet_nuts + d_rail)
            self.d_o[7] = self.vec_d(bra_d_2)
            self.d_o[8] = self.vec_d(self.tot_d)        
            # position along axis_w
            self.w_o[0] = V0
            self.w_o[1] = self.vec_w(-reinf_thick_2)
            self.w_o[2] = self.vec_w(-(reinf_thick_2 + dist_hole))
            self.w_o[3] = self.vec_w(-(reinf_thick_2 + dist_hole + self.boltshank_r_tol))
            self.w_o[4] = self.vec_w(-(reinf_thick_2 + dist_hole + 2 * self.boltshank_r_tol))
            self.w_o[5] = self.vec_w(-(reinf_thick_2 + bra_w_2))
            self.w_o[6] = self.vec_w(-self.tot_w)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # make the whole box
        if n_bolt == 1:
            shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.pos_o)
        
            cut = []

            shp_box_int = fcfun.shp_box_dir(box_w = bra_w_1, box_d = bra_d_1, box_h = bra_h_1, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(0, 0, 1))
            cut.append(shp_box_int)

            if rail == 0:
                shp_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(3, 0, 0))
                cut.append(shp_hole1)
                shp_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(4, 0, 3))
                cut.append(shp_hole2)
            else:
                shp_hole1 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltshank_r_tol, box_d = d_rail, box_h = wall_thick, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 0, xtr_nd = 0, pos = self.get_pos_dwh(1, 0, 0))
                cut.append(shp_hole1)
                shp_hole2 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltshank_r_tol, box_d = wall_thick, box_h = d_rail, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 0, xtr_nd = 0, pos = self.get_pos_dwh(4, 0, 2))
                cut.append(shp_hole2)

            shp_cut = fcfun.fuseshplist(cut)
            shp_final = shp_box.cut(shp_cut)

            chmf_reinf_r = min(bra_d_1, bra_h_1)
            for pt_w in (-3, 3):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(0, pt_w, 5), fillet = 0, radius = chmf_reinf_r)

            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(0, 0, 0), fillet = 0, radius = chmf_r)
            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(4, 0, 1), fillet = 1, radius = chmf_r)
            
            for pt_h in (0, 5):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(5, 0, pt_h), fillet = 0, radius = chmf_r)

            if rail == 1:
                for pt_w in (-1, 1):
                    for pt_d in (1, 2):
                        shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)
                    for pt_h in (2, 4):
                        shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_d, fc_pt = self.get_pos_dwh(4, pt_w, pt_h), fillet = 1, radius = chmf_r)

        else:
            shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.pos_o)

            cut = []

            shp_box_int = fcfun.shp_box_dir(box_w = bra_w_2 + reinf_thick_2, box_d = bra_d_2, box_h = bra_h_2, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(0, 1, 1))
            cut.append(shp_box_int)
            
            if rail == 0:
                for pt_d in (2, 5):
                    shp_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(pt_d, 3, 0))
                    cut.append(shp_hole1)
                for pt_h in (3, 6):
                    shp_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(7, 3, pt_h))
                    cut.append(shp_hole2)
            else:
                for pt_d in (1, 4):
                    shp_hole1 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltshank_r_tol, box_d = d_rail, box_h = wall_thick, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 0, xtr_nd = 0, pos = self.get_pos_dwh(pt_d, 3, 0))
                    cut.append(shp_hole1)
                for pt_h in (2, 5):
                    shp_hole2 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltshank_r_tol, box_d = wall_thick, box_h = d_rail, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 0, xtr_nd = 0, pos = self.get_pos_dwh(7, 3, pt_h))
                    cut.append(shp_hole2)

            shp_cut = fcfun.fuseshplist(cut)
            shp_final = shp_box.cut(shp_cut)

            chmf_reinf_r = min(bra_d_2, bra_h_2)
            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(0, 1, 8), fillet = 0, radius = chmf_reinf_r)

            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(0, 0, 0), fillet = 0, radius = chmf_r)
            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(7, 0, 1), fillet = 1, radius = chmf_r)

            for pt_h in (0, 8):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_w, fc_pt = self.get_pos_dwh(8, 0, pt_h), fillet = 0, radius = chmf_r)

            if rail == 1:
                for pt_w in (2, 4):
                    for pt_d in (1, 3, 4, 6):
                        shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)
                    for pt_h in (2, 4, 5, 7):
                        shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_d, fc_pt = self.get_pos_dwh(7, pt_w, pt_h), fillet = 1, radius = chmf_r)

        shp_final = shp_final.removeSplitter()

        self.shp = shp_final

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_alu = alu_bracket(n_bolt = 1, bra_w_1 = 22., bra_w_2 = 17., bra_d_1 = 21., bra_d_2 = 51., bra_h_1 = 21., bra_h_2 = 51., bolt = 5., rail = 0, d_rail = 11., reinf_thick_1 = 3., reinf_thick_2 = 5., wall_thick = 6., chmf_r = 1., dist_bet_nuts = 17., dist_hole = 5., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0)