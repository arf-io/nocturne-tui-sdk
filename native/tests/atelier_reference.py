"""Independent host-math equations from preserved Atelier sampleBurst."""
import math
from kinetic_reference import random_at
DEFAULTS=dict(lifeMs=4200,count=64,speed=20,gravity=9,rise=10,drag=.22,turbulence=1.3,glitterHz=14,trailMs=100,branches=7,jaggedness=2.2,coreMs=280,coreRadius=3,ejecta=1,shockwave=0,intensity=.8,seed=4711,reducedMotion=False)
def sample(kind,age,event_id=1,**patch):
    o={**DEFAULTS,**patch};points=[];segments=[];glows=[];out=dict(points=points,segments=segments,glows=glows)
    if age<0 or age>=o['lifeMs'] or o['reducedMotion'] or o['intensity']==0:return out
    t=age/1000;p=age/o['lifeMs'];seed=(event_id^o['seed'])&0xffffffff;fade=(1-p)**1.8
    def point(x,y,glyph,alpha,heat):points.append([x,y,ord(glyph),max(0,min(1,alpha*o['intensity'])),max(0,min(1,heat))])
    def segment(x,y,xx,yy,alpha,heat):segments.append([x,y,xx,yy,max(0,min(1,alpha*o['intensity'])),max(0,min(1,heat))])
    if kind=='sparks':
        strike=min(o['lifeMs'],1100);a=max(0,min(1,1-age/strike))
        if a==0:return out
        flash=math.floor(age/max(34,1000/o['glitterHz']));jitter=.65+.35*random_at(seed,flash+901)
        for branch in range(o['branches']):
            angle=random_at(seed,branch*41)*math.tau;length=o['speed']*(.2+.8*random_at(seed,branch*41+1))*(.45+.55*min(1,t*8));x=y=0
            for j in range(1,9):
                q=j/8;kink=(random_at(seed^(branch+17),flash*97+j)-.5)*o['jaggedness']*math.sin(q*math.pi)
                xx=math.cos(angle)*length*q+math.sin(angle)*kink;yy=math.sin(angle)*length*q*.5-math.cos(angle)*kink*.5
                segment(x,y,xx,yy,a*jitter*(1-q*.4),.8+q*.2)
                if j in (4,6):
                    fork=angle+(.8 if j==4 else -.8);r=length*.28;segment(xx,yy,xx+math.cos(fork)*r,yy+math.sin(fork)*r*.5,a*.6,.65)
                x,y=xx,yy
            point(x,y,'✧' if flash%3==0 else '·',a,.98)
        glows.append([0,0,1.2,a*.3*o['intensity'],1,0]);return out
    if kind=='nova':
        core=max(0,min(1,1-age/o['coreMs'])) if o['coreMs'] else 0
        if core>0:glows.append([0,0,o['coreRadius']*(.5+age/max(1,o['coreMs'])),core*.8*o['intensity'],1,0])
        for j in range(math.floor(o['count']*o['ejecta'])):
            angle=random_at(seed,j*13)*math.tau;v=o['speed']*(.28+random_at(seed,j*13+1));r=v*(-math.expm1(-t*.7))/.7
            x=math.cos(angle)*r;y=math.sin(angle)*r*.5+.2*t*t;tail=max(0,t-o['trailMs']/1000);r0=v*(-math.expm1(-tail*.7))/.7
            flicker=random_at((seed+j)&0xffffffff,math.floor(t*o['glitterHz']));alpha=fade*(.25+.75*flicker);heat=max(0,min(1,1-p*.8-j/o['count']*.2))
            segment(math.cos(angle)*r0,math.sin(angle)*r0*.5,x,y,alpha,heat);point(x,y,'✧' if flicker>.94 else '∙' if flicker>.65 else '·',alpha,heat)
        for j in range(12):
            angle=j*math.tau/12+random_at(seed,j)*.2;r=o['speed']*t*.7
            segment(math.cos(angle)*r*.15,math.sin(angle)*r*.075,math.cos(angle)*r,math.sin(angle)*r*.5,math.exp(-t*5)*.75,1)
        if age<450:point(0,0,'✶' if age<90 else '✹' if age<180 else '✧',math.exp(-age/220),1)
        if age>180 and o['shockwave']>0:glows.append([0,0,o['speed']*t*1.1,fade*o['shockwave']*o['intensity'],.6,1])
        return out
    for j in range(o['count']):
        r=random_at(seed,j*5);r2=random_at(seed,j*5+1);q=random_at(seed,j*5+2);glint=random_at((seed+j)&0xffffffff,math.floor(t*o['glitterHz']));x=y=0;heat=.8;glyph='·'
        def ember(seconds):return ((r-.5)*o['speed']*seconds/(1+o['drag']*seconds)+math.sin(seconds*2+r2*math.tau)*o['turbulence']*seconds,-o['rise']*(.6+r2*.4)*seconds+o['gravity']*seconds**2/2)
        if kind=='embers':
            x,y=ember(t);heat=.25+.55*(1-p);glyph='✧' if glint>.9 else '∙' if glint>.5 else '·'
            if o['trailMs']:
                xx,yy=ember(max(0,t-o['trailMs']/1000));segment(xx,yy,x,y,fade*.3,heat)
        elif kind=='rain':x=(r-.5)*24+o['turbulence']*t;y=-r2*18+t*o['speed'];glyph='╱' if j%3 else '│';heat=.7
        elif kind=='snow':x=(r-.5)*32+math.sin(t*1.6+r2*math.tau)*o['turbulence']*2;y=-r2*20+t*o['speed']*.22;glyph='·' if q>.5 else '⋅';heat=.8
        else:raise ValueError(kind)
        point(x,y,glyph,fade*(.25+.75*glint if kind=='embers' else .7),heat)
    return out
