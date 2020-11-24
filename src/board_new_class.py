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

class board(Obj3D):
    """
    Create a board to achieve the same movement of two profiles.

          axis_h
            :
            :____          ___________          ____
            |    |        |           |        |    |
            |    |________|           |________|    |
            |        ::                   ::        |
            |________::___________________::________|....................> axis_d


         axis_w
            :
            :_______________________________________
            |    |        |           |        |    |
            |    |   (o)  |           |   (o)  |    |
            |    |        |           |        |    |
            |    |   (o)  |           |   (o)  |    |
            |____|________|___________|________|____|....................> axis_d

    pos_o (origin) is at pos_d=0, pos_w=0, pos_h=0, it's marked with o

    Parameters:
    ------------
    alusize_d: float
    alusize_w: float
    alusize_h: float
    dist_alu: float
    wall_thick: float
        thickness of some sides
    bolt_wall_d: float
        metric of the bolts to attach the holder
    opt_sides: int
        0:
        1:
    axis_h: FreeCAD Vector
        axis along the axis of the motor
    axis_d: FreeCAD Vector
        axis normal to surface where the holder will be attached to
    axis_w: FreeCAD Vector
        axis perpendicular to axis_h and axis_d, symmetrical (not necessary)
    pos_d: int
        location of pos along axis_d (0,1,2,3,4,5,6,7,8,9)
        0: at the beginning
        1: thickness of the optional wall
        2: bolt holes to hold the profile
        3: aluminum profile 
        4: distance between the two profiles
        5: bolt holes to hold the profile
        6: at the end of the piece without the optional wall
        7: at the end of the piece
    pos_w: int
        location of pos along axis_w (0,1,2,3). Symmetrical
        0: at the center of symmetry
        1: at the center of the  holes to attach the profile
        2: at the end of the piece
    pos_h: int
        location of pos along axis_h (0,1,2,3,4,5,6)
        0: at the top
        1: possition where the profiles are supported
        2: at the end of the piece
    pos: FreeCAD.Vector
        position of the holder (considering ref_axis)
    """
    def __init__(self, alusize_d= 50., alusize_w=30., alusize_h = 50., dist_alu = 30., wall_thick = 4., bolt_wall_d = 4., opt_sides = 1, axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'board'
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

        # calculation of the bolt to hold the base to the profile 
        self.boltshank_r_tol = kcomp.D912[bolt_wall_d]['shank_r_tol']
        self.bolthead_r = kcomp.D912[bolt_wall_d]['head_l']
        self.bolthead_r_tol = kcomp.D912[bolt_wall_d]['head_r']
        self.bolthead_l = kcomp.D912[bolt_wall_d]['head_l']
        self.bolthead_l_tol = kcomp.D912[bolt_wall_d]['head_l_tol']

        # making the big box that will contain everything and will be cut
        if opt_sides == 0:
            self.tot_d = 2 * alusize_d + dist_alu
            self.tot_w = 4 * self.bolthead_r_tol
            self.tot_h = wall_thick + alusize_h/2.
        else:
            self.tot_d = 2 * wall_thick + 2 * alusize_d + dist_alu
            self.tot_w = 4 * self.bolthead_r_tol
            self.tot_h = wall_thick + alusize_h/2.

        # definition of which axis is symmetrical
        self.h0_cen = 0
        self.d0_cen = 0   # symmetrical 
        self.w0_cen = 1   # symmetrical 

        # vectors from the origin to the points along axis_h
        self.h_o[0] = V0
        self.h_o[1] = self.vec_h(wall_thick)
        self.h_o[2] = self.vec_h(self.tot_h)

        # position along axis_d
        if opt_sides == 0:
            self.d_o[0] = V0
            self.d_o[1] = self.vec_d(alusize_d/2.)
            self.d_o[2] = self.vec_d(alusize_d)
            self.d_o[3] = self.vec_d(alusize_d + dist_alu)
            self.d_o[4] = self.vec_d(alusize_d + dist_alu + alusize_d/2.)
            self.d_o[5] = self.vec_d(self.tot_d)
        else:
            self.d_o[0] = V0
            self.d_o[1] = self.vec_d(wall_thick)
            self.d_o[2] = self.vec_d(wall_thick + alusize_d/2.)
            self.d_o[3] = self.vec_d(wall_thick + alusize_d)
            self.d_o[4] = self.vec_d(wall_thick + alusize_d + dist_alu)
            self.d_o[5] = self.vec_d(wall_thick + alusize_d + dist_alu + alusize_d/2.)
            self.d_o[6] = self.vec_d(wall_thick + alusize_d + dist_alu + alusize_d)
            self.d_o[7] = self.vec_d(self.tot_d)

        # vectors from the origin to the points along axis_w
        self.w_o[0] = V0
        self.w_o[1] = self.vec_w(-self.bolthead_r_tol)
        self.w_o[2] = self.vec_w(-self.tot_w/2.)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # make the whole box
        if opt_sides == 0: 
            shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.pos_o)
            super().add_child(shp_box, 1, 'shp_box')

            # make the shape of the piece
            cut_box1 = fcfun.shp_box_dir(box_w = self.tot_w, box_d = alusize_d + TOL, box_h = alusize_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(0, 0, 1))
            super().add_child(cut_box1, 0, 'cut_box1')
            cut_box2 = fcfun.shp_box_dir(box_w = self.tot_w, box_d = alusize_d + TOL, box_h = alusize_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(3, 0, 1))
            super().add_child(cut_box2, 0, 'cut_box2')

            # holes to hold the profile 
            cut_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(1, -1, 0))
            super().add_child(cut_hole1, 0, 'cut_hole1')
            cut_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(1, 1, 0))
            super().add_child(cut_hole2, 0, 'cut_hole2')
            cut_hole3 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(4, -1, 0))
            super().add_child(cut_hole3, 0, 'cut_hole3')
            cut_hole4 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(4, 1, 0))
            super().add_child(cut_hole4, 0, 'cut_hole4')
        
        else:
            shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.pos_o)
            super().add_child(shp_box, 1, 'shp_box')

            # make the shape of the piece
            cut_box1 = fcfun.shp_box_dir(box_w = self.tot_w, box_d = alusize_d + TOL, box_h = alusize_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(1, 0, 1))
            super().add_child(cut_box1, 0, 'cut_box1')
            cut_box2 = fcfun.shp_box_dir(box_w = self.tot_w, box_d = alusize_d + TOL, box_h = alusize_h, fc_axis_d = self.axis_d, fc_axis_h = self.axis_h, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(4, 0, 1))
            super().add_child(cut_box2, 0, 'cut_box2')

            # holes to hold the profile 
            cut_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(2, -1, 0))
            super().add_child(cut_hole1, 0, 'cut_hole1')
            cut_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(2, 1, 0))
            super().add_child(cut_hole2, 0, 'cut_hole2')
            cut_hole3 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(5, -1, 0))
            super().add_child(cut_hole3, 0, 'cut_hole3')
            cut_hole4 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(5, 1, 0))
            super().add_child(cut_hole4, 0, 'cut_hole4')
        
        super().make_parent(name)

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_board = board(alusize_d = 6., alusize_w = 30., alusize_h = 6., dist_alu = 14., wall_thick = 2., opt_sides = 0, axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0)