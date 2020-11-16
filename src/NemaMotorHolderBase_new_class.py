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

class base(Obj3D):
    """
    """
    def __init__(self, nema_size = 17, base_motor_d = 6., base_d = 4., base_h = 16., wall_thick = 4., motor_thick = 4., reinf_thick = 4., motor_min_h = 10., motor_max_h = 20., motor_xtr_space = 2., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'base'
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
        
        self.motor_w = kcomp.NEMA_W[nema_size]
        self.motor_bolt_sep = kcomp.NEMA_BOLT_SEP[nema_size]
        self.motor_bolt_d = kcomp.NEMA_BOLT_D[nema_size]

        # calculation of the bolt to hold the base to the profile 
        self.boltshank_r_tol = kcomp.D912[bolt1_wall_d]['shank_r_tol']
        self.bolthead_r = kcomp.D912[bolt1_wall_d]['head_l']
        self.bolthead_r_tol = kcomp.D912[bolt1_wall_d]['head_r']
        self.bolthead_l = kcomp.D912[bolt1_wall_d]['head_l']

        # calculation of the bolt wall d
        self.boltwallhead_l = kcomp.D912[bolt_wall_d]['head_l']
        self.boltwallhead_r = kcomp.D912[bolt_wall_d]['head_r']
        self.washer_thick = kcomp.WASH_D125_T[bolt_wall_d]

        # calculation of the bolt wall separation
        self.max_bolt_wall_sep = self.motor_w - 2 * self.boltwallhead_r
        if bolt_wall_sep == 0:
            self.bolt_wall_sep = self.max_bolt_wall_sep
        elif bolt_wall_sep > self.max_bolt_wall_sep: 
            logger.debug('bolt separation too large:' + str(bolt_wall_sep))
            self.bolt_wall_sep = self.max_bolt_wall_sep
            logger.debug('taking largest value:' + str(self.bolt_wall_sep))
        elif bolt_wall_sep < 4 * self.boltwallhead_r:
            logger.debug('bolt separation too short:' + str(bolt_wall_sep))
            self.bolt_wall_sep = self.self.max_bolt_wall_sep
            logger.debug('taking smallest value:' + str(self.bolt_wall_sep))
        
        # distance from the motor to the inner wall (in axis_d)
        self.motor_inwall_space = motor_xtr_space + self.boltwallhead_l + self.washer_thick

        # making the big box that will contain everything and will be cut
        self.tot_h = wall_thick + base_h + motor_thick + motor_max_h + 2 * bolt_wall_d        
        self.tot_w = 2 * reinf_thick + self.motor_w + 2 * motor_xtr_space
        self.tot_d = base_motor_d + wall_thick + self.motor_w + self.motor_inwall_space

        # definition of which axis is symmetrical
        self.h0_cen = 0
        self.w0_cen = 1   # symmetrical 
        self.d0_cen = 0

        # vectors from the origin to the points along axis_h
        self.h_o[0] = V0
        self.h_o[1] = self.vec_h(wall_thick)
        self.h_o[2] = self.vec_h(wall_thick + base_h)
        self.h_o[3] = self.vec_h(wall_thick + base_h + motor_thick)
        self.h_o[4] = self.vec_h(wall_thick + base_h + motor_thick + motor_min_h)
        self.h_o[5] = self.vec_h(wall_thick + base_h + motor_thick + motor_max_h)
        self.h_o[6] = self.vec_h(self.tot_h)

         # position along axis_d
        self.d_o[0] = V0
        self.d_o[1] = self.vec_d(base_d)
        self.d_o[2] = self.vec_d(base_motor_d)
        self.d_o[3] = self.vec_d(base_d + self.bolthead_r_tol)
        self.d_o[4] = self.vec_d(base_d + 2 * self.bolthead_r)

        # vectors from the origin to the points along axis_w
        self.w_o[0] = V0
        self.w_o[1] = self.vec_w(-self.bolt_wall_sep/2.)
        self.w_o[2] = self.vec_w(-self.motor_bolt_sep/2.)
        self.w_o[3] = self.vec_w(-self.tot_w/2.)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # make the whole box
        shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.pos_o)
        super().add_child(shp_box, 1, 'shp_box')

        shp_box_int = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = base_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(1, 0, 1))
        super().add_child(shp_box_int, 0, 'shp_box_int')

        shp_box_ext = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = motor_thick + motor_max_h + 2 * bolt_wall_d, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(2, 0, 2))
        super().add_child(shp_box_ext, 0, 'shp_box_ext')
        
        shp_box_init = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = wall_thick, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(4, 0, 0))
        super().add_child(shp_box_init, 0, 'shp_box_init')
        
        shp_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(3, -2, 0)) 
        super().add_child(shp_hole1, 0, 'shp_hole1')

        shp_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(3, 2, 0)) 
        super().add_child(shp_hole2, 0, 'shp_hole2')

        super().make_parent(name)
        chmf_reinf_r = min(base_motor_d - base_d, base_h)
        self.shp = fcfun.shp_filletchamfer_dirpt(self.shp, self.axis_w, fc_pt = self.get_pos_dwh(2, 0, 2), fillet = 0, radius = (chmf_reinf_r - TOL))

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

class NemaMotorHolder(Obj3D):
    """
    """
    def __init__(self, nema_size = 17, base_motor_d = 6., base_d = 4., base_h = 16., wall_thick = 4., motor_thick = 4., reinf_thick = 4., motor_min_h = 10., motor_max_h = 20., motor_xtr_space = 2., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., rail = 1, chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'NemaMotorHolder'
        self.set_name(name, default_name, change = 0)
        Obj3D.__init__(self, axis_d, axis_w, axis_h, self.name)

        self.pos = FreeCAD.Vector(0, 0, 0)
        self.position = pos

        # save the arguments as attributes
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if not hasattr(self,i):
                setattr(self, i, values[i])
        
        # normal axes to print without support
        self.prnt_ax = self.axis_h
        
        self.motor_w = kcomp.NEMA_W[nema_size]
        self.motor_bolt_sep = kcomp.NEMA_BOLT_SEP[nema_size]
        self.motor_bolt_d = kcomp.NEMA_BOLT_D[nema_size]

        # calculation of the bolt wall d
        self.boltwallshank_r_tol = kcomp.D912[bolt_wall_d]['shank_r_tol']
        self.boltwallhead_l = kcomp.D912[bolt_wall_d]['head_l']
        self.boltwallhead_r = kcomp.D912[bolt_wall_d]['head_r']
        self.washer_thick = kcomp.WASH_D125_T[bolt_wall_d]

        # calculation of the bolt wall separation
        self.max_bolt_wall_sep = self.motor_w - 2 * self.boltwallhead_r
        self.min_bolt_wall_sep = 4 * self.boltwallhead_r
        if bolt_wall_sep == 0:
            self.bolt_wall_sep = self.max_bolt_wall_sep
        elif bolt_wall_sep > self.max_bolt_wall_sep: 
            logger.debug('bolt separation too large:' + str(bolt_wall_sep))
            self.bolt_wall_sep = self.max_bolt_wall_sep
            logger.debug('taking largest value:' + str(self.bolt_wall_sep))
        elif bolt_wall_sep < self.min_bolt_wall_sep:
        #elif bolt_wall_sep < 4 * self.boltwallhead_r:
            logger.debug('bolt separation too short:' + str(bolt_wall_sep))
            #self.bolt_wall_sep = self.self.max_bolt_wall_sep
            self.bolt_wall_sep = self.min_bolt_wall_sep
            logger.debug('taking smallest value:' + str(self.bolt_wall_sep))
        
        # distance from the motor to the inner wall (in axis_d)
        self.motor_inwall_space = motor_xtr_space + self.boltwallhead_l + self.washer_thick

        # making the big box that will contain everything and will be cut
        self.tot_h = motor_thick + motor_max_h + 2 * bolt_wall_d
        self.tot_w = 2 * reinf_thick + self.motor_w + 2 * motor_xtr_space
        self.tot_d = wall_thick + self.motor_w + self.motor_inwall_space

        # distance from the motor axis to the wall (in axis_d)
        self.motax2wall = wall_thick + self.motor_inwall_space + self.motor_w/2.

        # definition of which axis is symmetrical
        self.h0_cen = 0
        self.w0_cen = 1   # symmetrical 
        self.d0_cen = 0

        # vectors from the origin to the points along axis_h
        self.h_o[0] = V0
        self.h_o[1] = self.vec_h(motor_thick)
        self.h_o[2] = self.vec_h(motor_thick + motor_min_h)
        self.h_o[3] = self.vec_h(motor_thick + motor_max_h)
        self.h_o[4] = self.vec_h(self.tot_h)

        # position along axis_d
        self.d_o[0] = V0
        self.d_o[1] = self.vec_d(wall_thick)
        self.d_o[2] = self.vec_d(self.motax2wall - self.motor_bolt_sep/2.)
        self.d_o[3] = self.vec_d(self.motax2wall)
        self.d_o[4] = self.vec_d(self.motax2wall + self.motor_bolt_sep/2.)
        self.d_o[5] = self.vec_d(self.tot_d)

        # vectors from the origin to the points along axis_w
        self.w_o[0] = V0
        self.w_o[1] = self.vec_w(-self.bolt_wall_sep/2.)
        self.w_o[2] = self.vec_w(-self.motor_bolt_sep/2.)
        self.w_o[3] = self.vec_w(-self.tot_w/2.)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # make the whole box, extra height and depth to cut all the way back and down
        shp_box1 = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.pos_o)
        # little chamfer at the corners, if fillet there are some problems
        shp_box2 = fcfun.shp_filletchamfer_dir(shp_box1, self.axis_h, fillet = 0, radius = chmf_r)
        # chamfer of the box to make a 'triangular' reinforcement
        chmf_reinf_r = min(self.tot_d - wall_thick, self.tot_h - motor_thick)
        shp_box3 = fcfun.shp_filletchamfer_dirpt(shp_box2, self.axis_w, fc_pt = self.get_pos_dwh(5, 0, 4), fillet = 0, radius = chmf_reinf_r)
        super().add_child(shp_box3, 1, 'shp_box3')

        # holes

            # the space for the motor
        shp_motor = fcfun.shp_box_dir(box_w = self.motor_w + 2 * motor_xtr_space, box_d = self.tot_d + chmf_r, box_h = self.tot_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(1, 0, 1))
        shp_motor = fcfun.shp_filletchamfer_dir(shp_motor, self.axis_h, fillet = 0, radius = chmf_r)
        super().add_child(shp_motor, 0, 'shp_motor')

            # central circle of the motor 
        shp_hole1 = fcfun.shp_cylcenxtr(r = (self.motor_bolt_sep - self.motor_bolt_d)/2., h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_d(3))
        super().add_child(shp_hole1, 0, 'shp_hole1')

            # motor bolt holes
        shp_hole2 = fcfun.shp_cylcenxtr(r = self.motor_bolt_d/2. + TOL, h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(2, -2, 0))
        super().add_child(shp_hole2, 0, 'shp_hole2')
        shp_hole3 = fcfun.shp_cylcenxtr(r = self.motor_bolt_d/2. + TOL, h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(2, 2, 0))
        super().add_child(shp_hole3, 0, 'shp_hole3')
        shp_hole4 = fcfun.shp_cylcenxtr(r = self.motor_bolt_d/2. + TOL, h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(4, -2, 0))
        super().add_child(shp_hole4, 0, 'shp_hole4')
        shp_hole5 = fcfun.shp_cylcenxtr(r = self.motor_bolt_d/2. + TOL, h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(4, 2, 0))
        super().add_child(shp_hole5, 0, 'shp_hole5')
            
            # rail holes
        if rail == 1:
            shp_hole6 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltwallshank_r_tol, box_d = wall_thick, box_h = motor_max_h - motor_min_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 1, xtr_nd = 1, pos = self.get_pos_dwh(0, -1, 2))
            super().add_child(shp_hole6, 0, 'shp_hole6')
            shp_hole7 = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltwallshank_r_tol, box_d = wall_thick, box_h = motor_max_h - motor_min_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 1, xtr_nd = 1, pos = self.get_pos_dwh(0, 1, 2))
            super().add_child(shp_hole7, 0, 'shp_hole7')
            
            # hole for the ending of the rails (4 semicircles)
        shp_hole8 = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot =1, pos = self.get_pos_dwh(0, -1, 2))
        super().add_child(shp_hole8, 0, 'shp_hole8')
        shp_hole9 = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot =1, pos = self.get_pos_dwh(0, 1, 2))
        super().add_child(shp_hole9, 0, 'shp_hole9')
        shp_hole10 = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot =1, pos = self.get_pos_dwh(0, -1, 3))
        super().add_child(shp_hole10, 0, 'shp_hole10')
        shp_hole11 = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot =1, pos = self.get_pos_dwh(0, 1, 3))
        super().add_child(shp_hole11, 0, 'shp_hole11')

        super().make_parent(name)

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

class NemaMotorHolderBase(Obj3D):
    """
    """
    def __init__(self, nema_size = 17, base_motor_d = 6., base_d = 4., base_h = 16., wall_thick = 4., motor_thick = 4., reinf_thick = 4., motor_min_h = 10., motor_max_h = 20., motor_xtr_space = 2., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., rail = 1, chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product
        
        default_name = 'NemaMotorHolderBase'
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
        
        self.motor_w = kcomp.NEMA_W[nema_size]
        self.motor_bolt_sep = kcomp.NEMA_BOLT_SEP[nema_size]
        self.motor_bolt_d = kcomp.NEMA_BOLT_D[nema_size]

        # calculation of the bolt to hold the base to the profile 
        self.boltshank_r_tol = kcomp.D912[bolt1_wall_d]['shank_r_tol']
        self.bolthead_r = kcomp.D912[bolt1_wall_d]['head_l']
        self.bolthead_r_tol = kcomp.D912[bolt1_wall_d]['head_r']
        self.bolthead_l = kcomp.D912[bolt1_wall_d]['head_l']
        self.bolthead_l_tol = kcomp.D912[bolt1_wall_d]['head_l_tol']

        # calculation of the bolt wall d
        self.boltwallshank_r_tol = kcomp.D912[bolt_wall_d]['shank_r_tol']
        self.boltwallhead_l = kcomp.D912[bolt_wall_d]['head_l']
        self.boltwallhead_r = kcomp.D912[bolt_wall_d]['head_r']
        self.washer_thick = kcomp.WASH_D125_T[bolt_wall_d]

        # calculation of the bolt wall separation
        self.max_bolt_wall_sep = self.motor_w - 2 * self.boltwallhead_r
        self.min_bolt_wall_sep = 4 * self.boltwallhead_r
        if bolt_wall_sep == 0:
            self.bolt_wall_sep = self.max_bolt_wall_sep
        elif bolt_wall_sep > self.max_bolt_wall_sep: 
            logger.debug('bolt separation too large:' + str(bolt_wall_sep))
            self.bolt_wall_sep = self.max_bolt_wall_sep
            logger.debug('taking largest value:' + str(self.bolt_wall_sep))
        elif bolt_wall_sep < 4 * self.boltwallhead_r:
            logger.debug('bolt separation too short:' + str(bolt_wall_sep))
            self.bolt_wall_sep = self.self.max_bolt_wall_sep
            logger.debug('taking smallest value:' + str(self.bolt_wall_sep))
        
        # distance from the motor to the inner wall (in axis_d)
        self.motor_inwall_space = motor_xtr_space + self.boltwallhead_l + self.washer_thick

        # making the big box that will contain everything and will be cut
        self.tot_h = wall_thick + base_h + motor_thick + motor_max_h + 2 * bolt_wall_d        
        self.tot_w = 2 * reinf_thick + self.motor_w + 2 * motor_xtr_space
        self.tot_d = base_motor_d + wall_thick + self.motor_w + self.motor_inwall_space

        # distance from the motor axis to the wall (in axis_d)
        self.motax2wall = wall_thick + self.motor_inwall_space + self.motor_w/2.

        # definition of which axis is symmetrical
        self.h0_cen = 0
        self.w0_cen = 1   # symmetrical 
        self.d0_cen = 0

        # vectors from the origin to the points along axis_h
        self.h_o[0] = V0
        self.h_o[1] = self.vec_h(wall_thick)
        self.h_o[2] = self.vec_h(wall_thick + base_h)
        self.h_o[3] = self.vec_h(wall_thick + base_h + motor_thick)
        self.h_o[4] = self.vec_h(wall_thick + base_h + motor_thick + motor_min_h)
        self.h_o[5] = self.vec_h(wall_thick + base_h + motor_thick + motor_max_h)
        self.h_o[6] = self.vec_h(self.tot_h)

        # position along axis_d
        self.d_o[0] = V0
        self.d_o[1] = self.vec_d(base_d)
        self.d_o[2] = self.vec_d(base_motor_d)
        self.d_o[3] = self.vec_d(base_d + self.bolthead_r_tol)
        self.d_o[4] = self.vec_d(base_d + 2 * self.bolthead_r)
        self.d_o[5] = self.vec_d(base_motor_d + wall_thick)
        self.d_o[6] = self.vec_d(base_motor_d + self.motax2wall - self.motor_bolt_sep/2.)
        self.d_o[7] = self.vec_d(base_motor_d + self.motax2wall)
        self.d_o[8] = self.vec_d(base_motor_d + self.motax2wall + self.motor_bolt_sep/2.)
        self.d_o[9] = self.vec_d(self.tot_d)

        # vectors from the origin to the points along axis_w
        self.w_o[0] = V0
        self.w_o[1] = self.vec_w(-self.bolt_wall_sep/2.)
        self.w_o[2] = self.vec_w(-self.motor_bolt_sep/2.)
        self.w_o[3] = self.vec_w(-self.tot_w/2.)

        # calculates the position of the origin, and keeps it in attribute pos_o
        self.set_pos_o()

        # base
        motherboard = base(nema_size = 17, base_motor_d = 8., base_d = 6., base_h = 16., wall_thick = 6., motor_thick = 6., reinf_thick = 1., motor_min_h =10., motor_max_h =50., motor_xtr_space = 3., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 0,  pos_d = 0, pos_w = 0, pos = self.get_pos_dwh(0, 0, 0))
        self.append_part(motherboard)
        motorholder = NemaMotorHolder(nema_size = 17, base_motor_d = 8., base_d = 6., base_h = 16., wall_thick = 6., motor_thick = 6., reinf_thick = 1., motor_min_h =10., motor_max_h =50., rail = 1, motor_xtr_space = 3., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 0,  pos_d = 0, pos_w = 0, pos = self.get_pos_dwh(2, 0, 2))
        self.append_part(motorholder)

        super().make_group()
        
        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_nema = NemaMotorHolderBase(nema_size = 17, base_motor_d = 8., base_d = 6., base_h = 16., wall_thick = 6., motor_thick = 6., reinf_thick = 1., motor_min_h =10., motor_max_h =50., rail = 1, motor_xtr_space = 3., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1,  pos_d = 3, pos_w = 0, pos = V0)