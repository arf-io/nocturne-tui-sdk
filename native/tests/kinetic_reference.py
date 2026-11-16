"""Independent host-math reference derived from preserved Kinetic source."""
import math
DEFAULTS=dict(count=52,lifeMs=5000,launchSpeed=12,gravity=8,drag=.65,wind=1.2,flickerHz=18,trailMs=90,branches=5,arcSegments=10,arcJitter=1.2,coreMs=260,shockwave=0,explosionForce=48,seed=2030,brightness=.85,glyphs='·∙⋅*+⠁⠂⠄',emberSpread=5,arcReach=17)
def random_at(seed,index):
    v=(seed^(((index+1)*0x9e3779b9)&0xffffffff))&0xffffffff
    v=((v^(v>>16))*0x7feb352d)&0xffffffff;v=((v^(v>>15))*0x846ca68b)&0xffffffff
    return (v^(v>>16))/4294967296
def sample(kind,age_ms,event_id=1,**patch):
    o={**DEFAULTS,**patch};seed=(o['seed']^((event_id*2654435761)&0xffffffff))&0xffffffff
    rand=lambda i,salt:random_at((seed^((salt*2246822519)&0xffffffff))&0xffffffff,i)
    points=[];segments=[];out=dict(points=points,segments=segments,core=0,radius=0,shockwave=0)
    if age_ms<0 or age_ms>=o['lifeMs']:return out
    t=age_ms/1000;fade=(1-age_ms/o['lifeMs'])**1.5;glyphs=list(o['glyphs'])
    def point(x,y,alpha,heat,glyph,size=1):points.append([x,y,max(0,min(1,alpha)),heat,ord(glyph),size])
    def segment(x,y,xx,yy,alpha,heat,branch=0):segments.append([x,y,xx,yy,max(0,min(1,alpha)),heat,branch])
    def decay(seconds):return -math.expm1(-o['drag']*seconds)/o['drag'] if o['drag'] else seconds
    def ember(i,age):
        seconds=max(0,age)/1000;vy=o['launchSpeed']*(.72+.55*rand(i,11));vx=(rand(i,12)-.5)*o['emberSpread']
        x=vx*decay(seconds)+o['wind']*seconds+.4*math.sin(seconds*3+rand(i,13)*6)*seconds
        y=-vy*seconds+.5*o['gravity']*seconds**2;life=o['lifeMs']*(.9+.1*rand(i,14));f=max(0,min(1,1-age/life))
        flicker=.35+.65*rand(i,math.floor(age*o['flickerHz']/1000)+201)
        return x,y,f**.65*flicker*o['brightness'],.1+.4*f,glyphs[math.floor(rand(i,16)*len(glyphs))]
    if kind=='embers':
        for i in range(o['count']):
            age=age_ms-rand(i,9)*180
            if age<0:continue
            x,y,alpha,heat,glyph=ember(i,age);point(x,y,alpha,heat,glyph)
            if o['trailMs'] and alpha>.02:
                xx,yy,*_=ember(i,max(0,age-o['trailMs']));segment(xx,yy,x,y,alpha*.25,heat)
    elif kind=='sparks':
        envelope=math.exp(-age_ms/max(100,o['lifeMs']*.22));phase=math.floor(age_ms*max(1,o['flickerHz'])/1000)
        flicker=.45+.55*rand(phase,43);out['core']=math.exp(-age_ms/max(1,o['coreMs']))*.65*o['brightness']
        for b in range(o['branches']):
            angle=rand(b,44)*math.tau;reach=o['arcReach']*(.5+.5*rand(b,45))*(.4+.6*min(1,age_ms/90));x=y=0
            for j in range(1,o['arcSegments']+1):
                u=j/o['arcSegments'];jitter=(rand(b*37+j,phase+51)-.5)*o['arcJitter']
                xx=math.cos(angle)*reach*u-math.sin(angle)*jitter;yy=(math.sin(angle)*reach*u+math.cos(angle)*jitter)*.5
                segment(x,y,xx,yy,envelope*flicker*o['brightness'],.85,b)
                if j%3==0:
                    a2=angle+(rand(j,b+71)-.5)*2.3;length=reach*.23
                    segment(xx,yy,xx+math.cos(a2)*length,yy+math.sin(a2)*length*.5,envelope*.65*o['brightness'],1,b+1)
                    point(xx,yy,envelope*flicker*o['brightness'],1,'*')
                x,y=xx,yy
        for i in range(min(o['count'],40)):
            a=rand(i,84)*math.tau;v=o['explosionForce']*(.3+.7*rand(i,85))
            point(math.cos(a)*v*t,math.sin(a)*v*t*.5+.6*t*t,fade*math.exp(-2*t)*o['brightness'],.75,glyphs[i%len(glyphs)])
    elif kind=='nova':
        out['core']=math.sqrt(max(0,min(1,1-age_ms/o['coreMs'])))*o['brightness'] if o['coreMs'] else 0
        out['radius']=o['explosionForce']*t;out['shockwave']=o['shockwave']*fade
        for i in range(o['count']):
            a=rand(i,91)*math.tau;v=o['explosionForce']*(.3+.9*rand(i,92));d=decay(t);x=math.cos(a)*v*d;y=math.sin(a)*v*d*.5
            previous=decay(max(0,t-o['trailMs']/1000));flicker=.4+.6*rand(i,math.floor(age_ms*o['flickerHz']/1000)+100);alpha=fade*flicker*o['brightness']
            point(x,y,alpha,.3+.7*fade,'*' if age_ms<150 else glyphs[i%len(glyphs)])
            segment(math.cos(a)*v*previous,math.sin(a)*v*previous*.5,x,y,alpha*.9,.7)
            if age_ms<o['coreMs']*2 and i<20:segment(x*.15,y*.15,x*1.4,y*1.4,math.exp(-age_ms/180)*o['brightness'],.95)
    elif kind in ('rain','snow'):
        for i in range(o['count']):
            seconds=(age_ms-rand(i,120)*o['lifeMs']*.6)/1000
            if seconds<0:continue
            v=o['launchSpeed']*(.4+rand(i,121));x=(rand(i,122)-.5)*24+o['wind']*seconds
            if kind=='snow':x+=math.sin(seconds*2+i)*1.7
            point(x,-8+v*seconds,fade*o['brightness'],.6,'·' if kind=='snow' else '│')
    else:raise ValueError(kind)
    return out
