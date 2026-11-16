"""Independent retained integer Studio nova envelope/ring arithmetic."""
import math

def smooth(p):
    p=max(0,min(1000,p));return p*p*(3000-2*p)//1000000

def core(age_ms,duration=3600,glyphs='·∙*✦✧'):
    if age_ms<0 or age_ms>=duration:return dict(envelope=0,glyph=0,index=0)
    phase=age_ms*1000//duration
    envelope=smooth(phase*1000//240 if phase<240 else (1000-phase)*1000//760)
    index=envelope*(len(glyphs)-1)//1000
    return dict(envelope=envelope,glyph=ord(glyphs[index]),index=index)

def ring(age_ms,x_q8,y_q8,duration=3600,speed=2560,width=384,rings=2,opacity=280,strength=850,aspect=2000):
    if age_ms<0 or age_ms>=duration:return 0
    # Signed integer division in preserved C truncates toward zero.
    dy=math.trunc(y_q8*aspect/1000);distance=math.isqrt(x_q8*x_q8+dy*dy)
    radius=age_ms*speed//1000;fade=smooth(1000-age_ms*1000//duration);peak=0
    for k in range(rings):
        r=radius-k*width*4
        if r<0:continue
        delta=abs(distance-r)
        if delta<width:
            a=smooth(1000-delta*1000//width);a=a*fade//1000;a=a*strength//1000;a=a*opacity//1000;a=a*1000//(1000+k*420);peak=max(peak,a)
    return peak

PALETTE=[0x28304f,0x785c89,0x367876,0xae7357,0x504565]
STAR_PALETTE=[0xb6a4c4,0x9fb9b0,0xc7bca7,0x9cacca,0xc6a0aa,0xadbdbb]
def mix(a,b,p):
    p=max(0,min(1000,p));out=0
    for shift in (16,8,0):
        aa=(a>>shift)&255;bb=(b>>shift)&255;out|=(aa+math.trunc((bb-aa)*p/1000))<<shift
    return out

def palette_color(phase,palette=None):
    colors=palette or PALETTE
    if len(colors)==1:return colors[0]
    p=(phase%1024)*len(colors);index=p//1024;f=smooth((p%1024)*1000//1024)
    return mix(colors[index],colors[(index+1)%len(colors)],f)

def ring_color(seed,x_q8,y_q8,aspect=2000,wave_scale=6144,palette=None):
    dy=math.trunc(y_q8*aspect/1000);distance=math.isqrt(x_q8*x_q8+dy*dy)
    return palette_color(seed%1024+distance*1024//wave_scale,palette)
