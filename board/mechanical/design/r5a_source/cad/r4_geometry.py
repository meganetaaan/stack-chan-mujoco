#!/usr/bin/env python3
"""Create R4 geometry; does not carry forward the colliding R2 mechanism.
All custom mounting details are PROTOTYPE dimensions, not fabrication release.
Axes: +X forward, +Y robot left, +Z up. CAD millimetres, node frames from core.py.
"""
from __future__ import annotations
import sys,json,csv,math
from dataclasses import dataclass,field
from pathlib import Path
import numpy as np
import cadquery as cq
import trimesh
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tab5_biped.core import PARAMS as P, KIN,JOINT_TYPES,nominal,all_frames,motor_spec

C={'shell':(0.77,.81,.80),'frame':(.28,.34,.36),'motor':(.11,.16,.18),'horn':(.09,.49,.62),'sole':(.12,.16,.17),'glass':(.012,.022,.025),'face':(.94,.98,.96),'board':(.08,.35,.26),'battery':(.18,.22,.25)}

@dataclass
class Part:
    name:str
    link:str
    shape:cq.Shape
    role:str
    color:tuple
    mass:float|None=None
    collisions:list=field(default_factory=list)
    note:str=''

def box(size,pos=(0,0,0),r=0,edge='|Z'):
    w=cq.Workplane('XY').box(*size)
    if r:w=w.edges(edge).fillet(r)
    return w.val().translate(tuple(pos))

def cyl(r,length,pos,axis=(0,0,1)):
    return cq.Solid.makeCylinder(r,length,cq.Vector(*pos),cq.Vector(*axis))

def union(*xs):
    s=xs[0]
    for x in xs[1:]:s=s.fuse(x)
    return s.clean()

def CB(size,pos=(0,0,0)):
    return {'type':'box','size':list(np.array(size,float)/2000),'pos':list(np.array(pos,float)/1000)}

def CY(r,l,pos,axis):
    return {'type':'cylinder','size':[r/1000,l/2000],'pos':list(np.array(pos)/1000),'axis':list(axis)}

def posed(shape,T):
    r=Rotation.from_matrix(T[:3,:3]).as_rotvec();a=np.linalg.norm(r)
    s=shape
    if a>1e-12:s=s.rotate((0,0,0),tuple(r/a),math.degrees(a))
    return s.translate(tuple(T[:3,3]*1000))

def y_frame(L, sep=16.8, bridge_z=None):
    """Double-supported pitch linkage, side plates clear motor and shaft.
    Ends are on horn/bearing axis, not at the case centre.
    """
    plates=[]
    for y0 in (-sep-1.2,sep-1.2):
        s=union(box((17,2.4,L),(0,y0+1.2,-L/2)),cyl(10.5,2.4,(0,y0,0),(0,1,0)),cyl(10.5,2.4,(0,y0,-L),(0,1,0)))
        for z in (0,-L):
            s=s.cut(cyl(3.1,3,(0,y0-.3,z),(0,1,0)))
            for x in (-6.2,6.2):s=s.cut(cyl(1.15,3,(x,y0-.3,z),(0,1,0)))
        # Longitudinal lightening opening.
        s=s.cut(box((7,4,max(4,L-30)),(0,y0+1.2,-L/2),r=2,edge='|Y'))
        plates.append(s)
    bz=-L/2 if bridge_z is None else bridge_z
    bridge=box((3,2*sep+2.4,5),(12.5,0,bz))
    wings=[box((7,2.4,5),(11,yy,bz)) for yy in (-sep,sep)]
    return union(*plates,bridge,*wings)

def motor_shape(axis='y',long_up=False):
    # Exact overall manufacturer envelope W20 H34 D26, plus explicitly
    # conservative 5-mm shaft/bearing keepouts (spline not modelled).
    z=7 if long_up else -7
    if axis=='y':
        body=box((20,26,34),(0,0,z),r=.7)
        s=union(body,cyl(2.45,5,(0,13,0),(0,1,0)),cyl(2.45,5,(0,-13,0),(0,-1,0)))
        collision=CB((20,26,34),(0,0,z))
    else:
        body=box((26,20,34),(-13,0,z),r=.7)
        s=union(body,cyl(2.45,5,(0,0,0),(1,0,0)),cyl(2.45,5,(-26,0,0),(-1,0,0)))
        collision=CB((26,20,34),(-13,0,z))
    return s,[collision]

def frame_link(L,sep=16.8,th=2.4,dy=0,bridge_z=None):
    """Two planar-bearing cheek plates, optionally dog-legged in lateral Y."""
    plates=[]
    for sy in (-1,1):
        y=sy*sep
        wa=cq.Workplane('XY',origin=(0,y,0)).rect(17,th).val()
        wb=cq.Workplane('XY',origin=(0,y+dy,-L)).rect(17,th).val()
        plate=union(cq.Solid.makeLoft([wa,wb]),cyl(10.5,th,(0,y-th/2,0),(0,1,0)),cyl(10.5,th,(0,y+dy-th/2,-L),(0,1,0)))
        for yy,z in ((y,0),(y+dy,-L)):
            plate=plate.cut(cyl(3.1,th+1,(0,yy-th/2-.5,z),(0,1,0)))
            for xx in (-6.2,6.2):plate=plate.cut(cyl(1.15,th+1,(xx,yy-th/2-.5,z),(0,1,0)))
        # Window is a slanted loft; wall thickness is constant at endpoints.
        zl=-L/2-max(3,L-30)/2;zh=-L/2+max(3,L-30)/2
        wa=cq.Workplane('XY',origin=(0,y-dy*zh/L,zh)).rect(6,th+2).val()
        wb=cq.Workplane('XY',origin=(0,y-dy*zl/L,zl)).rect(6,th+2).val()
        plate=plate.cut(cq.Solid.makeLoft([wa,wb]))
        plates.append(plate)
    bz=-L/2 if bridge_z is None else bridge_z;yy=-dy*bz/L
    bridge=box((3,2*sep+th,4),(12.5,yy,bz))
    wings=[box((7,th,4),(11,s*sep+yy,bz)) for s in (-1,1)]
    return union(*plates,bridge,*wings)

def shin_frame(side):
    # A 6mm lateral ankle displacement. Doglegs are confined to the gap
    # between the knee-case sweep and the ankle-pitch case; not through them.
    sg=1 if side=='left' else -1;L=KIN['shin_mm'];dy=sg*KIN['shin_outset_y_mm']
    pairs=[(sg*(-14.5),dy+sg*(-18.5)),(sg*19.6,dy+sg*15.6)];plates=[]
    for yu,yl in pairs:
        wires=[cq.Workplane('XY',origin=(0,y,z)).rect(17,2).val() for y,z in [(yu,0),(yu,-14),(yl,-20),(yl,-L)]]
        ss=union(*[cq.Solid.makeLoft([wires[i],wires[i+1]]) for i in range(3)],cyl(10.5,2,(0,yu-1,0),(0,1,0)),cyl(10.5,2,(0,yl-1,-L),(0,1,0)))
        for y,z in [(yu,0),(yl,-L)]:
            ss=ss.cut(cyl(3.1,3,(0,y-1.5,z),(0,1,0)))
            for x in (-6.2,6.2):ss=ss.cut(cyl(1.15,3,(x,y-1.5,z),(0,1,0)))
        ss=ss.cut(box((6,12,L-30),(0,(yu+yl)/2,-L/2),r=2,edge='|Y'));plates.append(ss)
    ys=sorted([p[0] for p in pairs]);mid=sum(ys)/2;wide=ys[1]-ys[0]+2;bz=-13
    return union(*plates,box((3,wide,4),(12.5,mid,bz)),*[box((7,2,4),(11,y,bz)) for y in ys])

def profile_y(points,thick,ycenter):
    pl=cq.Plane(origin=(0,ycenter+thick/2,0),xDir=(1,0,0),normal=(0,-1,0))
    return cq.Workplane(pl).polyline(points).close().extrude(thick).val()

def boot_shell(side):
    sg=1 if side=='left' else -1
    yy=sg*KIN['foot_outset_y_mm'];width=KIN['foot_width_mm']
    # Rigid fairing: not a fictitious soft membrane or a collision-disabled hull.
    points=[(-39,-15.8),(55,-15.8),(55,0),(51,12),(46,22),(38,37),(-29,37),(-39,24)]
    inner=[(-37,-18),(53,-18),(53,-1),(49,10.7),(44.5,20.8),(36.5,35),(-27.5,35),(-37,23.2)]
    out=profile_y(points,width,yy)
    out=cq.Workplane(obj=out).edges('|Y').fillet(1.2).val()
    inside=profile_y(inner,width-4,yy)
    out=out.cut(inside)
    # Open collar for the shin sweep. No pretending a closed roof can bend.
    out=out.cut(box((74,50,45),(7,0,48),r=4,edge='|Z'))
    # Inboard sweep channel: the two-axis ankle needs lateral clearance.
    # This is a real opening in the rigid boot, not a collision exemption.
    # The uninterrupted outboard wall and toe retain the cartoon boot silhouette.
    out=out.cut(box((77,8,32),(5.5,-sg*22,14),r=3,edge='|Y'))
    # Four paired M2.2 clearance holes on base plate / boot ledges.
    for xx in (-34,40):
        for sy in (-1,1):
            y=yy+sy*(width/2-3.5)
            lug=box((7,7,3.2),(xx,y,-14.2),r=1)
            out=out.fuse(lug).cut(cyl(1.15,6,(xx,y,-17)))
    # Toe and upper rear vent slits, both physical cuts.
    for sy in (-1,1):
        for xx in (-19,-10,-1):
            out=out.cut(box((3,6,8),(xx,yy+sy*(width/2),17),r=.7,edge='|Y'))
    return out.clean()

def build():
    out=[]
    def add(name,link,s,role,col,mass=None,collisions=None,note=''):
        if not s.isValid() or s.Volume()<=0:raise ValueError(name+' invalid shape')
        out.append(Part(name,link,s.clean(),role,C[col],mass,collisions or [],note))
    w=P['body']['wall_mm'];front=27.6;back=-38.2
    outer=box((front-back,80,128),((front+back)/2,0,64),r=.5,edge='|X')
    cavity=box((front-back+2,80-2*w,128-2*w),((front+back)/2,0,64))
    shell=outer.cut(cavity)
    # A non-load-bearing lower side skirt uses 1mm skins for hip clearance.
    shell=shell.cut(box((front-back+2,78,50),((front+back)/2,0,24)))
    # Open underside, exactly level with the Tab5 lower edge at z=0.
    shell=shell.cut(box((front-back-2*w,76,6),((front+back)/2,0,0)))
    # Lateral, rearward knee reliefs. The front Tab5 edge remains at z=0.
    for sg in (-1,1):
        shell=shell.cut(box((59.6,8,25),(-5.2,sg*40,10),r=3,edge='|Y'))
        # Hip-carrier top corners require small side service / clearance ports.
        shell=shell.cut(box((32,8,10),(13,sg*40,46.5),r=2,edge='|Y'))
    for y in (-36,36):
        for z in (4,124):
            start=24.9 if z==4 else 21.6
            shell=shell.fuse(cyl(3.7,27.6-start,(start,y,z),(1,0,0))).cut(cyl(1.7,8,(20.6,y,z),(1,0,0)))
    for y in (-35,35):
        for z in (8,120):
            shell=shell.fuse(cyl(4.6,5,(back,y,z),(1,0,0))).cut(cyl(1.25,5.5,(back-.1,y,z),(1,0,0)))
    col=[CB((front-back,w,128),((front+back)/2,s*(40-w/2),64)) for s in (-1,1)]
    col.append(CB((front-back,80,w),((front+back)/2,0,128-w/2)))
    add('body_shroud','base',shell,'custom','shell',collisions=col,note='80x80x128; flush lower edge; four M3 clearance bosses. Tab5 thread depth and assembly details provisional.')
    lid=box((1.8,80,128),(-39.1,0,64),r=.5,edge='|X')
    for y in (-35,35):
        for z in (8,120):lid=lid.cut(cyl(1.65,3,(-40.5,y,z),(1,0,0)))
    for z in (102,108,114):lid=lid.cut(box((3,32,2.2),(-39.1,0,z),r=1,edge='|X'))
    add('rear_cover','base',lid,'custom','shell',collisions=[CB((1.8,80,128),(-39.1,0,64))])
    tab=box((12,80,128),(34,0,64),r=4,edge='|X')
    screen=box((.3,62.4,110.7),(39.85,0,61.15),r=.25,edge='|X');tab=tab.cut(screen)
    for y in (-36,36):
        for z in (4,124):tab=tab.cut(cyl(1.45,3,(28,y,z),(1,0,0)))
    lens=cyl(2.5,.3,(39.7,0,123.55),(1,0,0));tab=tab.cut(lens)
    add('Tab5','base',tab,'hardware','shell',P['body']['tab5_mass_kg'],[CB((12,80,128),(34,0,64))],'Envelope only; original mounting pattern retained, no verified thread engagement')
    face=[];plane=cq.Plane(origin=(39.9,0,0),xDir=(0,1,0),normal=(1,0,0))
    for y in (-12,12):face.append(cq.Workplane(plane).center(y,91).ellipse(3.3,4.5).extrude(.1).val())
    face.append(cq.Workplane(plane).moveTo(-5.6,80).threePointArc((0,74.4),(5.6,80)).lineTo(4.2,80).threePointArc((0,75.8),(-4.2,80)).close().extrude(.1).val())
    for i,g in enumerate(face):screen=screen.cut(g);add('face_'+str(i),'base',g,'visual','face',0)
    add('screen','base',screen,'visual','glass',0);add('camera','base',lens,'visual','glass',0)
    add('battery_2S_reservation','base',box((23,66,38),(-4,0,100),r=2),'hardware','battery',P['mass_assumptions']['upper_2s_battery_kg'],note='70g assumption / 23x66x38mm; not a selected certified battery')
    for name,size,pos,mass in [('dedicated_5V_converter',(12,36,20),(18,0,73),P['mass_assumptions']['converter_kg']),('TTL_interface',(5,24,20),(-28,0,94),P['mass_assumptions']['interface_kg']),('cables_and_fasteners',(8,10,16),(-25,0,50),P['mass_assumptions']['cables_fasteners_kg'])]:
        add(name,'base',box(size,pos,r=.5),'hardware','board',mass,note='Relocated mass/space reservation, not cable routing or an exact PCB')
    for side,sgn in [('left',1),('right',-1)]:
        y=sgn*KIN['hip_half_spacing_mm'];zr=KIN['hip_roll_height_mm'];xr=KIN['hip_roll_x_mm']
        s,c=motor_shape('x',True);s=s.translate((xr,y,zr))
        for k in c:k['pos']=list(np.array(k['pos'])+np.array([xr,y,zr])/1000)
        add(side+'_hip_roll_motor','base',s,'hardware','motor',motor_spec('hip_roll')['mass_kg'],c)
        holder=box((30,24,38),(xr-13,y,zr+8),r=.6)
        holder=holder.cut(box((28,20.8,35),(xr-13,y,zr+7)))
        holder=holder.cut(cyl(5,34,(xr-30,y,zr),(1,0,0)))
        holder=holder.cut(box((34,21.2,39),(xr-13,y,zr+5)))
        # Two short bridges from the rear frame to the fixed servo cradle.
        holder=union(holder,*[box((6.2,24,2.4),(-35.1,y,z)) for z in (zr+26,zr-9.5)])
        add(side+'_fixed_roll_cradle','base',holder,'custom','frame',note='Fixed screw bracket; bearing/servo case screw details not a manufacturing release')
        roll=f'{side}_hip_roll';pitch=f'{side}_hip_pitch';knee=f'{side}_knee';ap=f'{side}_ankle_pitch';ar=f'{side}_ankle_roll'
        hp=np.array(KIN['hip_pitch_offset_mm'],float)
        ring=cyl(11,2.4,(5.6,0,0),(1,0,0)).cut(cyl(3.1,3,(5.3,0,0),(1,0,0)))
        spine=box((2.4,30.2,39),(8.5,0,hp[2]+7.5))
        cheeks=[box((26.4,1.8,36),(20,yy,hp[2]+7),r=.5,edge='|Y') for yy in (-14.2,14.2)]
        strap=box((20,30.2,2.4),(20,0,hp[2]+25.2))
        carrier=union(ring,spine,*cheeks,strap)
        for yy in (-18,13):carrier=carrier.cut(cyl(6,5,(hp[0],yy,hp[2]),(0,1,0)))
        add(side+'_roll_to_pitch_carrier',roll,carrier,'custom','frame',note='Hip pitch case upright above axis; entire carrier raised into body')
        s,c=motor_shape('y',True);s=s.translate(tuple(hp))
        for k in c:k['pos']=list(np.array(k['pos'])+hp/1000)
        add(side+'_hip_pitch_motor',roll,s,'hardware','motor',P['motor']['mass_kg'],c)
        L=KIN['thigh_mm']
        add(side+'_thigh_yoke',pitch,frame_link(L,bridge_z=-L/2-2.5),'custom','frame',collisions=[CB((17,2.4,L),(0,yy,-L/2)) for yy in (-16.8,16.8)])
        s,c=motor_shape('y',True);s=s.translate((0,0,-L))
        for k in c:k['pos'][2]-=L/1000
        add(side+'_knee_motor',pitch,s,'hardware','motor',motor_spec('knee')['mass_kg'],c,note='Direct-drive knee retained; rearward-folded thigh moves case beneath/inside lower body')
        L=KIN['shin_mm'];dy=sgn*KIN['shin_outset_y_mm']
        add(side+'_shin_yoke',knee,shin_frame(side),'custom','frame',note='6mm lateral dogleg gives ankle housings room without widening upper body')
        s,c=motor_shape('y',True);s=s.translate((0,dy,-L))
        for k in c:k['pos']=list(np.array(k['pos'])+np.array([0,dy,-L])/1000)
        add(side+'_ankle_pitch_motor',knee,s,'hardware','motor',P['motor']['mass_kg'],c)
        off=np.array(KIN['ankle_roll_offset_mm'],float)
        s,c=motor_shape('x',True);s=s.translate(tuple(off))
        for k in c:k['pos']=list(np.array(k['pos'])+off/1000)
        add(side+'_ankle_roll_motor',ap,s,'hardware','motor',P['motor']['mass_kg'],c,note='Fore-aft offset replaces tall vertical stack; still an actuated roll joint')
        cheeks=[]
        for yy in (sgn*(-14.5),sgn*18.4):
            outline=[(-7,8),(-44,19),(-55,19),(-55,-20),(-49,-20),(-49,-17),(-49,13),(-8,2)]
            ss=union(profile_y(outline,2.0,yy),cyl(10.5,2.0,(0,yy-1.0,0),(0,1,0)))
            ss=ss.cut(cyl(3.1,3,(0,yy-1.5,0),(0,1,0)))
            cheeks.append(ss)
        gimbal=union(*cheeks,box((8,34.9,2.4),(-42,sgn*1.95,15.2)),box((2.4,34.9,2.4),(-55,sgn*1.95,-18.8)))
        add(side+'_ankle_gimbal',ap,gimbal,'custom','frame',note='Orthogonal two-axis ankle; motors packaged fore-aft rather than stacked vertically')
        fs=KIN['foot_length_mm'];fw=KIN['foot_width_mm'];cx=KIN['foot_center_x_mm'];cy=sgn*KIN['foot_outset_y_mm']
        plate=box((fs,fw,3),(cx,cy,-17.5),r=3)
        sideparts=[]
        for xx in (5.6,-34.0):
            ss=union(cyl(10.2,2.4,(xx,0,0),(1,0,0)),box((2.4,18,17),(xx+1.2,0,-8.5)))
            ss=ss.cut(cyl(3.1,3,(xx-.3,0,0),(1,0,0)))
            sideparts.append(ss)
        foot=union(plate,*sideparts)
        for xx in (-34,40):
            for sy in (-1,1):foot=foot.cut(cyl(1.15,4,(xx,cy+sy*(fw/2-3.5),-19.5)))
        add(side+'_foot_yoke',ar,foot,'custom','frame',collisions=[CB((fs,fw,3),(cx,cy,-17.5))])
        add(side+'_boot_shell',ar,boot_shell(side),'custom','shell',note='Rigid hollow 94x52x59mm stylized boot; top opening, not a passive ankle')
        sole=box((fs,fw,3),(cx,cy,-20.5),r=3)
        add(side+'_sole_TPU',ar,sole,'custom','sole',collisions=[CB((fs,fw,3),(cx,cy,-20.5))],note='Flat support patch retained, chamfered appearance only; no passive rocker')
    return out

def mass_properties(p):
    V=p.shape.Volume()
    m=p.mass if p.mass is not None else V*1e-9*P['mass_assumptions']['printed_density_kg_m3']
    center=np.array(p.shape.Center().toTuple())/1000
    I=np.array(cq.Shape.matrixOfInertia(p.shape))*m/V*1e-6
    return m,center,I

def export(parts):
    for folder in ['models/meshes','cad/step','cad/stl_prototype','preview/meshes','reports']:(ROOT/folder).mkdir(exist_ok=True,parents=True)
    q,base=nominal();frames=all_frames(q,base)
    asm=cq.Assembly(name='Tab5_R4_10DOF_Concealed')
    records=[]
    for p in parts:
        world=posed(p.shape,frames[p.link]);asm.add(world,name=p.name,color=cq.Color(*p.color))
        path=ROOT/'models/meshes'/f'{p.name}.stl'
        cq.exporters.export(p.shape,str(path),tolerance=.09,angularTolerance=.15)
        cq.exporters.export(world,str(ROOT/'preview/meshes'/f'{p.name}.stl'),tolerance=.09,angularTolerance=.15)
        if p.role=='custom':
            cq.exporters.export(p.shape,str(ROOT/'cad/step'/f'{p.name}.step'))
            b=p.shape.BoundingBox();ground=p.shape.translate((0,0,-b.zmin))
            cq.exporters.export(ground,str(ROOT/'cad/stl_prototype'/f'{p.name}.stl'),tolerance=.07,angularTolerance=.12)
        mass,com,I=mass_properties(p)
        b=world.BoundingBox()
        records.append({'name':p.name,'link':p.link,'role':p.role,'color':list(p.color),'mass_kg':mass,'com_m':com.tolist(),'inertia_kg_m2':I.tolist(),'mesh':'meshes/'+p.name+'.stl','collisions':p.collisions,'note':p.note,'world_bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'solid_count':len(p.shape.Solids()),'brep_valid':p.shape.isValid(),'volume_mm3':p.shape.Volume()})
    asm.export(str(ROOT/'cad/step/assembly.step'))
    d={'revision':P['revision'],'nominal_q':q.tolist(),'nominal_base':base.tolist(),'parts':records,'manufacturing_release':False}
    (ROOT/'models/components.json').write_text(json.dumps(d,indent=2))
    # Each link gets a consistent exact CAD mass and inertia (servo COM remains
    # a uniform-envelope approximation, battery/PCB masses remain assumptions).
    links={}
    for ln in frames:
        rs=[r for r in records if r['link']==ln and r['mass_kg']>0]
        m=sum(r['mass_kg'] for r in rs);c=sum(r['mass_kg']*np.array(r['com_m']) for r in rs)/m
        I=np.zeros((3,3))
        for r in rs:
            v=np.array(r['com_m'])-c
            I+=np.array(r['inertia_kg_m2'])+r['mass_kg']*((v@v)*np.eye(3)-np.outer(v,v))
        links[ln]={'mass_kg':m,'com_m':c.tolist(),'inertia_kg_m2':I.tolist()}
    (ROOT/'models/inertials.json').write_text(json.dumps(links,indent=2))
    with (ROOT/'hardware/parts.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['name','link','role','mass_kg','note'])
        w.writerows([[r['name'],r['link'],r['role'],r['mass_kg'],r['note']] for r in records])
    print('Exported',len(records),'parts; total mass kg',sum(r['mass_kg'] for r in records),flush=True)
    return d

if __name__=='__main__':export(build())
