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

class bottom_coverplate(Obj3D):
    """
    """
    def __init__(self, xtr_lat = 5., xtr_holes = 8., h_bottom = 1., d_bottom = 2., h_rail = 2., h_base = 2., dist_holes = 49., wall_thick = 4., reinf_thick = 3., arduino_w = 53., arduino_d = 105., arduino_h = 5., sides = 10., bolt = 5., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'bottom_coverplate'
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
        self.tot_d =  2 * sides + arduino_d + d_bottom
        self.tot_w = arduino_w + 2 * wall_thick - 2. + 2 * xtr_holes
        self.tot_h = h_base + arduino_h + h_bottom

        # definition of which axis is symmetrical
        self.h0_cen = 0
        self.w0_cen = 1   # symmetrical 
        self.d0_cen = 0

        # vectors from the origin to the points along axis_h
        self.h_o[0] = V0
        self.h_o[1] = self.vec_h(h_base)
        self.h_o[2] = self.vec_h(h_base + arduino_h - h_rail)
        self.h_o[3] = self.vec_h(h_base + arduino_h)
        self.h_o[4] = self.vec_h(self.tot_h)

        # position along axis_d
        self.d_o[0] = V0
        self.d_o[1] = self.vec_d(sides/2.)
        self.d_o[2] = self.vec_d(sides)
        self.d_o[3] = self.vec_d(sides + xtr_lat)
        self.d_o[4] = self.vec_d(sides + xtr_lat + xtr_holes/2.)
        self.d_o[5] = self.vec_d(sides + xtr_lat + xtr_holes)
        self.d_o[6] = self.vec_d(sides + arduino_d - 3. - xtr_holes)
        self.d_o[7] = self.vec_d(sides + arduino_d - 3. - xtr_lat)
        self.d_o[8] = self.vec_d(sides + arduino_d - 3. - xtr_holes/2)
        self.d_o[9] = self.vec_d(sides + arduino_d + d_bottom - xtr_holes)
        self.d_o[10] = self.vec_d(sides + arduino_d + d_bottom - xtr_holes/2)
        self.d_o[11] = self.vec_d(sides + arduino_d - 3.)
        self.d_o[12] = self.vec_d(sides + arduino_d)
        self.d_o[13] = self.vec_d(sides + arduino_d + d_bottom)
        self.d_o[14] = self.vec_d(sides + arduino_d + d_bottom + sides/2.)
        self.d_o[15] = self.vec_d(self.tot_d)

        # position along axis_w
        self.w_o[0] = V0
        self.w_o[1] = self.vec_w(-(arduino_w - 2. - 2 * xtr_lat)/2.)
        self.w_o[2] = self.vec_w(-(arduino_w - 2.)/2.)
        self.w_o[3] = self.vec_w(-dist_holes/2.)
        self.w_o[4] = self.vec_w(-(arduino_w + 2 * wall_thick - 2.)/2.)
        self.w_o[5] = self.vec_w(-(arduino_w + 2 * wall_thick - 2. + xtr_holes)/2.)
        self.w_o[6] = self.vec_w(-self.tot_w/2.)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # make the whole box
        shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.pos_o)

        cut = []

        for pt_d in (0, 11):
            shp_lat1 = fcfun.shp_box_dir(box_w = xtr_holes, box_d = sides + xtr_lat, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(pt_d, -4, 0))
            cut.append(shp_lat1)
            shp_lat2 = fcfun.shp_box_dir(box_w = - xtr_holes, box_d = sides + xtr_lat, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(pt_d, 4, 0))
            cut.append(shp_lat2)

        shp_cut = fcfun.fuseshplist(cut)
        shp_final = shp_box.cut(shp_cut)

        for pt_d in (0, 15):
            for pt_w in (-4, 4):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)

        cut = []

        for pt_d in (3, 6):
            shp_lat3 = fcfun.shp_box_dir(box_w = xtr_holes, box_d = xtr_holes, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(pt_d, -4, 1))
            cut.append(shp_lat3)
            shp_lat4 = fcfun.shp_box_dir(box_w = - xtr_holes, box_d = xtr_holes, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(pt_d, 4, 1))
            cut.append(shp_lat4)

        shp_cut = fcfun.fuseshplist(cut)
        shp_final = shp_final.cut(shp_cut)

        for pt_d in (3, 11):
            for pt_w in (-6, 6):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)

        cut = []

        shp_lat5 = fcfun.shp_box_dir(box_w = xtr_holes, box_d = self.tot_d - 2 * (sides + xtr_lat + xtr_holes), box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(5, -4, 0))
        cut.append(shp_lat5)
        shp_lat6 = fcfun.shp_box_dir(box_w = - xtr_holes, box_d = self.tot_d - 2 * (sides + xtr_lat + xtr_holes), box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 0, cd = 0, ch = 0, pos = self.get_pos_dwh(5, 4, 0))
        cut.append(shp_lat6)

        shp_cut = fcfun.fuseshplist(cut)
        shp_final = shp_final.cut(shp_cut)

        for pt_d in (5, 6):
            for pt_w in (-6, 6):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)

        cut = []

        for pt_d in (0, 13):
            shp_sides = fcfun.shp_box_dir(box_w = self.tot_w, box_d = sides, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(pt_d, 0, 1))
            cut.append(shp_sides)

        shp_intern = fcfun.shp_box_dir(box_w = arduino_w - 2., box_d = arduino_d - 3., box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(2, 0, 1))
        cut.append(shp_intern)

        shp_int = fcfun.shp_box_dir(box_w = arduino_w - 2., box_d = arduino_d, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(2, 0, 2))
        cut.append(shp_int)

        shp_rail = fcfun.shp_box_dir(box_w = arduino_w + 2 * TOL, box_d = arduino_d, box_h = h_rail, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(2, 0, 2))
        cut.append(shp_rail)

        trim_mat = fcfun.shp_box_dir(box_w = arduino_w - 2. - 2 * xtr_lat, box_d = arduino_d - 3. - 2 * xtr_lat, box_h = self.tot_h, fc_axis_h = axis_h, fc_axis_d = axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(3, 0, 0))
        cut.append(trim_mat)

        shp_cut = fcfun.fuseshplist(cut)
        shp_final = shp_final.cut(shp_cut)

        for pt_d in (2, 13):
            for pt_w in (-4, 4):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)
        
        for pt_w in (-2, 2):
            shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(12, pt_w, 3), fillet = 1, radius = chmf_r)
            for pt_h in (1, 3):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(2, pt_w, pt_h), fillet = 1, radius = chmf_r)

        cut = []

        for pt_d in (1, 14):
            for pt_w in (-3, 3):
                shp_hole = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = h_base, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(pt_d, pt_w, 0)) 
                cut.append(shp_hole)

        for pt_d in (4, 8):
            for pt_w in (-5, 5):
                shp_hole = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = h_base, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(pt_d, pt_w, 0)) 
                cut.append(shp_hole)

        shp_cut = fcfun.fuseshplist(cut)
        shp_final = shp_final.cut(shp_cut)
        shp_final = shp_final.removeSplitter()

        for pt_d in (5, 6):
            for pt_w in (-4, 4):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)
        
        for pt_d in (3, 7):
            for pt_w in (-1, 1):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = 4 * chmf_r)

        for pt_d in (3, 11):
            for pt_w in (-4, 4):
                shp_final = fcfun.shp_filletchamfer_dirpt(shp_final, self.axis_h, fc_pt = self.get_pos_dwh(pt_d, pt_w, 0), fillet = 1, radius = chmf_r)
        
        doc.recompute()
        self.shp = shp_final

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_bottom = bottom_coverplate(xtr_lat = 5., xtr_holes = 8., h_bottom = 1., d_bottom = 2., h_rail = 2., h_base = 2., wall_thick = 4., reinf_thick = 3., arduino_w = 53., arduino_d = 105., arduino_h = 5., sides = 8., bolt = 3., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0)