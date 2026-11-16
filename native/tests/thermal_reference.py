"""Independent host math for preserved sampleThermal, local world coordinates."""
import math
from kinetic_reference import random_at

def sample(kind,seed,age_ms,life_ms=6500):
    points=[];segments=[];out=dict(points=points,segments=segments)
    if age_ms<0 or age_ms>=life_ms:return out
    t=age_ms/1000
    clamp=lambda v,a,b:max(a,min(b,v))
    def rand(i):return random_at(seed,i)
    if kind=='embers':
        def at(i,u):
            rise=.5+rand(i*11)*.45;height=8+rand(i*11+1)*13;fall=2.9+rand(i*11+2)*1.6
            y=height*(1-(1-u/rise)**2) if u<rise else height*(1-clamp((u-rise)/fall,0,1)**1.6)
            drift=(rand(i*11+3)-.5)*4;swirl=rand(i*11+4)*math.tau
            return [drift*u*.55+math.sin(u*2.3+swirl)*min(2,u*.6),max(0,y),(rand(i*11+5)-.5)*u*2+math.cos(u+swirl)*u*.2]
        for i in range(88):
            u=t-rand(i*11+6)*.23
            if u<0:continue
            survivor=rand(i*11+7)<.12;burnout=life_ms/1000 if survivor else 1.25+rand(i*11+8)*3.1
            if u>burnout:continue
            p=at(i,u);ground=p[1]<.02;fade=clamp((burnout-u)/.65,0,1);flicker=.5+.5*random_at(seed+i,math.floor(u*12))
            alpha=fade*flicker*(.35 if ground else clamp(1-u*.075,.3,1));heat=clamp(1-u/6,0,1)
            glyph='·' if ground else '✧' if flicker>.92 else '∙' if flicker>.75 else '·'
            points.append(p+[ord(glyph),alpha,18+heat*38])
            if not ground:segments.append(at(i,max(0,u-.055))+p+[alpha*.45,28+heat*30])
    else:
        for i in range(20):
            u=t-rand(i*9)*.45
            if u<0:continue
            phase=rand(i*9+1)*math.tau;h=12+rand(i*9+2)*10;scale=1.1+rand(i*9+3)*1.1
            center=[(rand(i*9+4)-.5)*28+u*1.5+math.sin(u*1.7+phase)*2,max(0,h-u*(2.8+rand(i*9+5))),(rand(i*9+6)-.5)*17+math.sin(u*.8+phase)*3]
            yaw=phase+u*(.7+rand(i*9+7));roll=math.sin(u*2+phase)*1.15;ca,sa,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(roll),math.sin(roll)
            def vertex(x,y):return [center[0]+(x*ca-y*sa)*scale,center[1]+(x*sa+y*ca)*scale*cr,center[2]+(x*sa+y*ca)*scale*sr]
            alpha=clamp((life_ms/1000-u)/1.1,0,1)*(.65 if center[1]<.1 else 1);hue=28+rand(i*9+8)*60
            outline=[vertex(math.sin(k*math.tau/16)*.48*math.sin(k*math.pi/16),math.cos(k*math.tau/16)) for k in range(17)]
            for j in range(1,17):segments.append(outline[j-1]+outline[j]+[alpha*.85,hue])
            segments.append(vertex(0,-1.25)+vertex(0,.85)+[alpha*.9,hue+12])
            for v in (-.4,.15,.6):segments.append(vertex(0,v-.2)+vertex(.3,v+.05)+[alpha*.45,hue+6])
    return out

def projected_segments(rows,origin,camera,near=.1,far=200,span=100,width=100,height=40):
    """Independent zero-angle orthographic segment clipping, terminal coordinates."""
    out=[]
    for row in rows:
        a=[row[k]+origin[k]-camera[k] for k in range(3)]
        b=[row[k+3]+origin[k]-camera[k] for k in range(3)]
        za,zb=-a[2],-b[2];low,high=0.,1.
        if za==zb:
            if not near<=za<=far:continue
        else:
            t1,t2=(near-za)/(zb-za),(far-za)/(zb-za)
            low=max(0,min(t1,t2));high=min(1,max(t1,t2))
            if low>high:continue
        aa=[a[k]+(b[k]-a[k])*low for k in range(3)];bb=[a[k]+(b[k]-a[k])*high for k in range(3)]
        def project(v):return [width/2+v[0]*width/span,(height-3)/2-v[1]*width/(2*span),-v[2]]
        out.append(project(aa)+project(bb))
    return out
