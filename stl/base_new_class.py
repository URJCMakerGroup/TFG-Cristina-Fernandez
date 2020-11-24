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
    Creates a holder for a Nema motor. 

              axis_d
                 :
                 :
         ________:_________
        |  O            O  |
        |..................|
        |..................|
        |__________________|...............................> axis_w|


         __________________        _____________________________ .............................> axis_h
        |  ::          ::  |      |                             |            + base_d
        |__::__________::__|      |   _____________             |............                + base_motor_d
        |                  |      |..|             \____________|.............................
        |                  |      |__|             :
        |                  |                       :
        |__________________|                       :
        |                  |                     axis_d
        |                  |                       
        |                  |                       
        |                  |                       
        |                  |                       
        |                  |                       
        |                  |                       
        |__________________|                       
        ::       :                                 
         + reinf_thick                             
                 :                                 
                 v                               
               axis_h            


              axis_d
                 :
                 :
         ________4_________ 
        |  O     3      O  |
        |........2.........|
        |........1.........|
        |________o_________|...............................> axis_w|         
                 0    1 2  3 (axis_w)


         ________o_________ ....................................> axis_w
        |  ::          ::  |                                  :
        |__::____1_____::__|.........                         :
        |                  |                                  :
        |                  |                                  :
        |                  |                                  :
        |________2_________|......... + base_h                :
        |                  |                                  :
        |________3_________|....................              :
        |                  |....+ motor_min_h  :              :
        |        4         |                   :              +tot_h
        |  (o)   5    (o)  |                   + motor_max_h  :
        |  (o)   6    (o)  |                   :              :
        |        7         |...................:              :
        |________8_________|..................................:
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
    base_d: float
        height of the base (axis d)
    base_motor_d: float
        height of the motor base (axis d)
    base_h: float
        width of the intermediate gap (axis h)
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
    bolt1_wall_d: float
        metric of the bolts to attach the profile 
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
        location of pos along axis_d (0,1,2,3,4,5,6,7,8,9)
        0: at the beginning, touching the wall where it is attached
        1: in the possition of base_h
        2: side where the motor holder will be supported
        3: bolt holes to hold the profile 
        4: at the end of the piece
    pos_w: int
        location of pos along axis_w (0,1,2,3). Symmetrical
        0: at the center of symmetry
        1: at the center of the rails (or holes) to attach the holder
        2: at the center of the holes to attach the motor
        3: at the end of the piece
    pos_h: int
        location of pos along axis_h (0,1,2,3,4,5,6)
        0: at the top
        1: at the inner side of the side where it will be screwed
        2: at the top (on the side of the motor axis)
        3: inside the motor wall
        4: top end of the rail
        5: possition where the bolts are
        6: possition where the bolts are
        7: bottom end of the rail
        8: at the end of the piece
    pos: FreeCAD.Vector
        position of the holder (considering ref_axis)
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
        self.boltwallshank_r_tol = kcomp.D912[bolt_wall_d]['shank_r_tol']
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
        self.h_o[5] = self.vec_h(wall_thick + base_h + motor_thick + (motor_min_h + motor_max_h)/4.)
        self.h_o[6] = self.vec_h(wall_thick + base_h + motor_thick + 3 * (motor_min_h + motor_max_h)/4.)
        self.h_o[7] = self.vec_h(wall_thick + base_h + motor_thick + motor_max_h)
        self.h_o[8] = self.vec_h(self.tot_h)

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
        
        # holes to hold the profile
        shp_hole1 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(3, -2, 0)) 
        super().add_child(shp_hole1, 0, 'shp_hole1')
        shp_hole2 = fcfun.shp_cylcenxtr(r = self.boltshank_r_tol, h = wall_thick, normal = self.axis_h, ch = 0, xtr_top = 1, xtr_bot = 1, pos = self.get_pos_dwh(3, 2, 0)) 
        super().add_child(shp_hole2, 0, 'shp_hole2')

        # holes to hold the Nema Motor Holder
        shp_cen_bolt1 = fcfun.shp_bolt_dir(r_shank = self.boltwallshank_r_tol, l_bolt = base_motor_d, r_head = self.boltwallhead_r, l_head = self.boltwallhead_l, xtr_head = 1, xtr_shank = 1, fc_normal = self.axis_d, pos_n = 0, pos = self.get_pos_dwh(0, -1, 5))
        super().add_child(shp_cen_bolt1, 0, 'shp_cen_bolt1')
        shp_cen_bolt2 = fcfun.shp_bolt_dir(r_shank = self.boltwallshank_r_tol, l_bolt = base_motor_d, r_head = self.boltwallhead_r, l_head = self.boltwallhead_l, xtr_head = 1, xtr_shank = 1, fc_normal = self.axis_d, pos_n = 0, pos = self.get_pos_dwh(0, 1, 5))
        super().add_child(shp_cen_bolt2, 0, 'shp_cen_bolt2')
        shp_cen_bolt3 = fcfun.shp_bolt_dir(r_shank = self.boltwallshank_r_tol, l_bolt = base_motor_d, r_head = self.boltwallhead_r, l_head = self.boltwallhead_l, xtr_head = 1, xtr_shank = 1, fc_normal = self.axis_d, pos_n = 0, pos = self.get_pos_dwh(0, -1, 6))
        super().add_child(shp_cen_bolt3, 0, 'shp_cen_bolt3')
        shp_cen_bolt4 = fcfun.shp_bolt_dir(r_shank = self.boltwallshank_r_tol, l_bolt = base_motor_d, r_head = self.boltwallhead_r, l_head = self.boltwallhead_l, xtr_head = 1, xtr_shank = 1, fc_normal = self.axis_d, pos_n = 0, pos = self.get_pos_dwh(0, 1, 6))
        super().add_child(shp_cen_bolt4, 0, 'shp_cen_bolt4')
        
        super().make_parent(name)
        chmf_reinf_r = min(base_motor_d - base_d, base_h)
        self.shp = fcfun.shp_filletchamfer_dirpt(self.shp, self.axis_w, fc_pt = self.get_pos_dwh(2, 0, 2), fillet = 0, radius = (chmf_reinf_r - TOL))

        # Then the Part
        super().create_fco(name)
        self.fco.Placement.Base = FreeCAD.Vector(0, 0, 0)
        self.fco.Placement.Base = self.position

doc = FreeCAD.newDocument()
shpob_base = base(nema_size = 17, base_motor_d = 8., base_d = 6., base_h = 16., wall_thick = 6., motor_thick = 6., reinf_thick = 1., motor_min_h =10., motor_max_h =50., motor_xtr_space = 3., bolt_wall_d = 4., bolt1_wall_d = 5., bolt_wall_sep = 30., chmf_r = 1., axis_h = VZ, axis_d = VX, axis_w = None, pos_h = 0,  pos_d = 0, pos_w = 0, pos = V0)
