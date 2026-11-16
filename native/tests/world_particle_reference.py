"""Independent original world sample equations, local3D source geometry."""
import math

def seeded_unit(seed,index):
    v=(seed^(((index+1)*0x9e3779b1)&0xffffffff))&0xffffffff
    v=((v^(v>>16))*0x7feb352d)&0xffffffff;v=((v^(v>>15))*0x846ca68b)&0xffffffff
    return (v^(v>>16))/4294967296

def sample(kind,age_ms,seed=2030,count=64,scale=1,life_ms=5000,gravity=2.6):
    out=dict(points=[],segments=[])
    if age_ms<0 or age_ms>=life_ms:return out
    age=age_ms/1000;life=life_ms/1000;count=math.floor(max(1,min(1200,count)))
    def soft(x):x=max(0,min(1,x));return x*x*(3-2*x)
    fade=soft((1-age/life)*2);rise=soft(age/.12)
    for i in range(count):
        a,b,r=[seeded_unit(seed,i*4+k) for k in range(3)]
        flicker=.7+.3*math.sin(age*(9+12*a)+b*60)**2;alpha=fade*rise;previous=None
        if kind=='firework':
            theta=a*math.tau;lat=b*2-1;rr=math.sqrt(1-lat*lat);speed=scale*(4+r*12)
            def at(t):return [math.cos(theta)*rr*speed*t,lat*speed*t-gravity*t*t*.5,math.sin(theta)*rr*speed*t]
            p=at(age);previous=at(max(0,age-.045));hue=a*360;alpha*=flicker;glyph=0x2219
        elif kind in ('embers','leaves'):
            vx=(a-.5)*scale*4;vy=scale*(3+5*b);vz=(r-.5)*scale*4
            def at(t):return [vx*t+math.sin(t*2+b*20)*scale*.4,vy*t-gravity*t*t*.5,vz*t]
            p=at(age);previous=at(max(0,age-.06));alpha*=flicker
            hue=35+b*95 if kind=='leaves' else 15+b*60;glyph=(0x2312 if math.sin(age*4+a*50)>0 else 0x223c) if kind=='leaves' else 0x2219
        elif kind=='sparks':
            branches=max(3,count//14);branch=i%branches;segment=i//branches;t=segment/math.ceil(count/branches);angle=seeded_unit(seed,branch+800)*math.tau
            def at(v):return [math.cos(angle)*scale*18*v+math.sin(v*45+branch*3+math.floor(age*16))*scale*.5,math.sin(angle)*scale*18*v+math.sin(v*63+branch*5)*scale*.6,math.sin(branch*7)*v*scale*7]
            p=at(t);previous=at(max(0,t-.1));hue=205+b*100;alpha*=max(0,1-age/min(life,.85))*flicker;glyph=0x22c6 if segment%3==0 else 0xb7
        else:
            p=[(a-.5)*50*scale,(b-.5)*30*scale-age*(17 if kind=='rain' else 4),(r-.5)*30*scale];alpha*=flicker
            hue=205 if kind=='rain' else 240;glyph=0x2571 if kind=='rain' else 0xb7
            if kind=='snow':p[0]+=math.sin(age*1.6+b*22)*3
        out['points'].append(p+[glyph,alpha,hue])
        if previous is not None:out['segments'].append(previous+p+[alpha,hue])
    return out
