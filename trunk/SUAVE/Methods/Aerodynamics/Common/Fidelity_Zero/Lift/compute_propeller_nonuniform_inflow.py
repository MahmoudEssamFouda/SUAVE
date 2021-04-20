import numpy as np
import scipy as sp
from SUAVE.Methods.Geometry.Three_Dimensional import  orientation_product, orientation_transpose


def compute_propeller_nonuniform_inflow(prop, upstream_wake,conditions):
    """ Computes the 
    
    Inputs:
       prop
       upstream_wake
       conditions
       lambdaw
       
    Outputs:
       Va
       Vt
       Vr
    """
    # unpack propeller parameters
    Vv       = conditions.frames.inertial.velocity_vector 
    R        = prop.tip_radius    
    rotation = prop.rotation
    theta    = prop.thrust_angle 
    c        = prop.chord_distribution
    Na       = prop.number_azimuthal_stations 
    Nr       = len(c)
    
    ua_wing  = upstream_wake.u_velocities
    uv_wing  = upstream_wake.v_velocities
    uw_wing  = upstream_wake.w_velocities
    VD       = upstream_wake.VD
    
    # Velocity in the Body frame
    T_body2inertial = conditions.frames.body.transform_to_inertial
    T_inertial2body = orientation_transpose(T_body2inertial)
    V_body          = orientation_product(T_inertial2body,Vv)
    body2thrust     = np.array([[np.cos(theta), 0., np.sin(theta)],[0., 1., 0.], [-np.sin(theta), 0., np.cos(theta)]])
    T_body2thrust   = orientation_transpose(np.ones_like(T_body2inertial[:])*body2thrust)  
    V_thrust        = orientation_product(T_body2thrust,V_body) 
    
    
    # azimuth distribution 
    psi       = np.linspace(0,2*np.pi,Na+1)[:-1]
    psi_2d    = np.tile(np.atleast_2d(psi).T,(1,Nr))   

    # 2 dimensiona radial distribution non dimensionalized
    chi     = prop.radius_distribution /R
    
    # Reframe the wing induced velocities:
    y_center = prop.origin[0][1] 
    
    # New points to interpolate data: (corresponding to r,phi locations on propeller disc)
    points  = np.array([[VD.YC[i], VD.ZC[i]] for i in range(len(VD.YC))])
    ycoords = np.reshape(R*chi*np.cos(psi_2d),(Nr*Na,))
    zcoords = prop.origin[0][2]  + np.reshape(R*chi*np.sin(psi_2d),(Nr*Na,))
    xi      = np.array([[y_center+ycoords[i],zcoords[i]] for i in range(len(ycoords))])
    
    ua_w = sp.interpolate.griddata(points,ua_wing,xi,method='linear')
    uv_w = sp.interpolate.griddata(points,uv_wing,xi,method='linear')
    uw_w = sp.interpolate.griddata(points,uw_wing,xi,method='linear') 
    
    ua_wing = np.reshape(ua_w,(Na,Nr))
    uw_wing = np.reshape(uw_w,(Na,Nr))
    uv_wing = np.reshape(uv_w,(Na,Nr))    
    
    if rotation == [1]:
        Vt_2d =  V_thrust[:,0]*( -np.array(uw_wing)*np.cos(psi_2d) + np.array(uv_wing)*np.sin(psi_2d)  )  # velocity tangential to the disk plane, positive toward the trailing edge eqn 6.34 pg 165           
        Vr_2d =  V_thrust[:,0]*( -np.array(uw_wing)*np.sin(psi_2d) - np.array(uv_wing)*np.cos(psi_2d)  )  # radial velocity , positive outward   eqn 6.35 pg 165                 
        Va_2d =  V_thrust[:,0]*   np.array(ua_wing)                                                       # velocity perpendicular to the disk plane, positive downward  eqn 6.36 pg 166  
    else:     
        Vt_2d =  V_thrust[:,0]*(  np.array(uw_wing)*np.cos(psi_2d) - np.array(uv_wing)*np.sin(psi_2d)  )  # velocity tangential to the disk plane, positive toward the trailing edge eqn 6.34 pg 165           
        Vr_2d =  V_thrust[:,0]*( -np.array(uw_wing)*np.sin(psi_2d) - np.array(uv_wing)*np.cos(psi_2d)  )  # radial velocity , positive outward   eqn 6.35 pg 165                 
        Va_2d =  V_thrust[:,0]*   np.array(ua_wing)                                                       # velocity perpendicular to the disk plane, positive downward  eqn 6.36 pg 166   
    
    # Append velocities to propeller
    prop.tangential_velocities_2d = Vt_2d
    prop.radial_velocities_2d     = Vr_2d
    prop.axial_velocities_2d      = Va_2d    
    
    return prop
