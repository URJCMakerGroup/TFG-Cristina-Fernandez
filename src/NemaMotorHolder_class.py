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

from NuevaClase import Obj3D
from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, addCyl_pos, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL

stl_dir = "/stl/"

logging.basicConfig(level = logging.DEBUG, format = '%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NemaMotorHolder(Obj3D):
    """
    Creates a holder for a Nema motor. 

              axis_d
                 :
                 :
         ________:_________
        ||                ||
        || O     __     O ||
        ||    /      \    ||
        ||   |        |   ||
        ||    \      /    ||
        || O     __     O ||
        ||________________|| .....
        ||________________|| ..... wall_thick.....> axis_w


           motor_xtr_space           motor_xtr_space
          ::            ::             ::
         _::____________::_         ___::____________ ..............> axis_d
        |  ::  :    :  ::  |       |      :     :    |    + motorside_thick
        |__::__:____:__::__|       0.1....:..3..:....5....:
        ||                ||       | :              /
        || ||          || ||       | :           /
        || ||          || ||       | :        /
        || ||          || ||       | :      /
        || ||          || ||       | :   /
        ||________________||       |_: /
        ::       :                 :                 :
         + reinf_thick             :....tot_d........:
                 :                 :
                 v                 v
               axis_h            axis_h


              axis_d
                 :
         ________5_________
        ||                ||
        || O     4_     O ||
        ||    /      \    ||
        ||   |   3    |   ||
        ||    \      /    ||
        || O     2_     O ||
        ||_______1________|| .....
        ||_______o____::__|| ..... wall_thick.....> axis_w
                 0    1 2  3 (axis_w)


         ________o_________ ....................................> axis_w
        |  ::  :    :  ::  |                                  :
        |__::__:_1__:__::__|....................              :
        ||                ||....+ motor_min_h  :              :
        ||  ||   2    ||  ||                   :              +tot_h
        ||  ||        ||  ||                   + motor_max_h  :
        ||  ||        ||  ||                   :              :
        ||  ||   3    ||  ||...................:              :
        ||_______4________||..................................:
        :   :    :     :   :
        :   :    v     :   :
        :   :  axis_h  :   :
        :   :          :   :
        :   :..........:   :
        :   bolt_wall_sep  :
        :                  :
        :                  :
        :.....tot_w........:
    
    pos_o (origin) is at pos_d=0, pos_w=0, pos_h=0, it's marked with o

    Parameters:
    ------------
    nema_size: int
        size of the motor (NEMA)
    wall_thick: float
        thickness of the side where the holder will be screwed to
    motor_thick: float
        thickness of the top side where the motor will be screwed to
    reinf_thick: float
        thickness of the reinforcement walls
    motor_min_h: float
        distance of from the inner top side to the top hole of the bolts to 
        attach the holder (see drawing)
    motor_max_h: float
        distance of from the inner top side to the bottom hole of the bolts to 
        attach the holder
    motor_xtr_space: float
        extra separation between the motor and the sides
    bolt_wall_d: float
        metric of the bolts to attach the holder
    bolt_wall_sep: float
        separation between the 2 bolt holes (or rails). Optional.
    rail: int
        1: the holes for the bolts are not holes, there are 2 rails, from
           motor_min_h to motor_max_h
        0: just 2 pairs of holes. One pair at defined by motor_min_h and the
           other defined by motor_max_h
    chmf_r: float
        radius of the chamfer, whenever chamfer is done
    axis_h: FreeCAD Vector
        axis along the axis of the motor
    axis_d: FreeCAD Vector
        axis normal to surface where the holder will be attached to
    axis_w: FreeCAD Vector
        axis perpendicular to axis_h and axis_d, symmetrical (not necessary)
    pos_d: int
        location of pos along axis_d (0,1,2,3,4,5)
        0: at the beginning, touching the wall where it is attached
        1: at the inner side of the side where it will be screwed
        2: bolts holes closed to the wall to attach the motor
        3: at the motor axis
        4: bolts holes away from to the wall to attach the motor
        5: at the end of the piece
    pos_w: int
        location of pos along axis_w (0,1,2,3). Symmetrical
        0: at the center of symmetry
        1: at the center of the rails (or holes) to attach the holder
        2: at the center of the holes to attach the motor
        3: at the end of the piece
    pos_h: int
        location of pos along axis_h (0,1,2,3,4)
        0: at the top (on the side of the motor axis)
        1: inside the motor wall
        2: Top end of the rail
        3: Bottom end of the rail
        4: Bottom end of the piece
    pos: FreeCAD.Vector
        position of the holder (considering ref_axis)
    """

    def __init__(self, nema_size = 17, wall_thick = 4., motor_thick = 4., reinf_thick = 4., motor_min_h = 10., motor_max_h = 20., motor_xtr_space = 2., bolt_wall_d = 3., bolt_wall_d_rail = 4., bolt_wall_sep = 30., rail = 1, chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1, pos_d = 3, pos_w = 0, pos = V0, name = ''):
        if axis_w is None or axis_w == V0:
           axis_w = axis_h.cross(axis_d) #vector product

        default_name = 'NemaMotorHolder'
        self.set_name(name, default_name, change = 0)
        Obj3D.__init__(self, axis_d, axis_w, axis_h, self.name)

        shp_clss.Obj3D.__init__(self, axis_d, axis_w, axis_h)
        
        # save the arguments as attributes
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

        # calculation of the bolt wall d
        self.boltwallshank_r_tol = kcomp.D912[bolt_wall_d]['shank_r_tol']
        self.boltwallhead_l = kcomp.D912[bolt_wall_d]['head_l']
        self.boltwallhead_r = kcomp.D912[bolt_wall_d]['head_r']
        self.washer_thick = kcomp.WASH_D125_T[bolt_wall_d]

        # calculation of the bolt wall d rail
        self.boltwallshank_r_tol_rail = kcomp.D912[bolt_wall_d_rail]['shank_r_tol']
        self.boltwallhead_l_rail = kcomp.D912[bolt_wall_d_rail]['head_l']
        self.boltwallhead_r_rail = kcomp.D912[bolt_wall_d_rail]['head_r']
        self.washer_thick_rail = kcomp.WASH_D125_T[bolt_wall_d_rail]

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
        shp_box = fcfun.shp_box_dir(box_w = self.tot_w, box_d = self.tot_d, box_h = self.tot_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.pos_o)

        # little chamfer at the corners, if fillet there are some problems
        shp_box = fcfun.shp_filletchamfer_dir(shp_box, self.axis_h, fillet = 0, radius = chmf_r)
        shp_box = shp_box.removeSplitter()

        # chamfer of the box to make a 'triangular' reinforcement
        chmf_reinf_r = min(self.tot_d - wall_thick, self.tot_h - motor_thick)
        shp_box = fcfun.shp_filletchamfer_dirpt(shp_box, self.axis_w, fc_pt = self.get_pos_dwh(5, 0, 4), fillet = 0, radius = chmf_reinf_r)
        shp_box = shp_box.removeSplitter()

        # holes
        holes = []

            # the space for the motor
        shp_motor = fcfun.shp_box_dir(box_w = self.motor_w + 2 * motor_xtr_space, box_d = self.tot_d + chmf_r, box_h = self.tot_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, pos = self.get_pos_dwh(1, 0, 1))
        shp_motor = fcfun.shp_filletchamfer_dir(shp_motor, self.axis_h, fillet = 0, radius = chmf_r)
        holes.append(shp_motor)

            # central circle of the motor 
        shp_hole = fcfun.shp_cylcenxtr(r = (self.motor_bolt_sep - self.motor_bolt_d + 8.)/2., h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_d(3))
        holes.append(shp_hole)

            # motor bolt holes
        for pt_d in (2, 4):
            for pt_w in (-2, 2):
                shp_hole = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol, h = motor_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(pt_d, pt_w, 0))
                holes.append(shp_hole)

            # rail holes
        for pt_w in (-1, 1):
            if rail == 1:
                shp_hole = fcfun.shp_box_dir_xtr(box_w = 2 * self.boltwallshank_r_tol_rail, box_d = wall_thick, box_h = motor_max_h - motor_min_h, fc_axis_h = self.axis_h, fc_axis_d = self.axis_d, cw = 1, cd = 0, ch = 0, xtr_d = 1, xtr_nd = 1, pos = self.get_pos_dwh(0, pt_w, 2))
                holes.append(shp_hole)
            
            # hole for the ending of the rails (4 semicircles)
            for pt_h in (2, 3):
                shp_hole = fcfun.shp_cylcenxtr(r = self.boltwallshank_r_tol_rail, h = wall_thick, normal = self.axis_d, ch = 0, xtr_top = 1, xtr_bot =1, pos = self.get_pos_dwh(0, pt_w, pt_h))
                holes.append(shp_hole)
            
        shp_holes = fcfun.fuseshplist(holes)
        shp_motorholder = shp_box.cut(shp_holes)
        shp_bracket = shp_motorholder.removeSplitter()
        self.shp = shp_bracket

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_nema = NemaMotorHolder(nema_size = 17, wall_thick = 6., motor_thick = 6., reinf_thick = 1., motor_min_h =10., motor_max_h =50., rail = 1, motor_xtr_space = 3., bolt_wall_d = 4., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 1,  pos_d = 3, pos_w = 0, pos = V0)