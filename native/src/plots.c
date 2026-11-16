#include "internal.h"
/* All plotted geometry is evaluated on the same 2x4 grid. No glyph-family change
 * is tied to speed, frame count, density, luminance or render duration. */
static const unsigned DOTS[8]={1,8,2,16,4,32,64,128};
static void plotDot(NrContext*c,int64_t px,int64_t py,uint32_t color) {
    if(px<0||py<0||px>=(int)nrView(c)->width*2||py>=(int)nrView(c)->height*4)return;
    int x=px/2,y=py/4;if(!nrInClip(c,x,y))return;
    int cell=y*(int)nrView(c)->width+x,k=(py%4)*2+px%2;
    c->plotMask[cell]|=(uint8_t)DOTS[k];c->plotColor[cell][k]=color;
}
/* Iterate the intersection, preserving the authored pixel coordinates. */
static void plotRect(NrContext*c,int64_t x,int64_t y,int64_t width,int64_t height,uint32_t color){
    int64_t right=x+width,bottom=y+height;
    int64_t loX=(int64_t)c->clip.x*2,loY=(int64_t)c->clip.y*4;
    int64_t hiX=loX+(int64_t)c->clip.width*2,hiY=loY+(int64_t)c->clip.height*4;
    if(loX<0)loX=0;if(loY<0)loY=0;
    if(hiX>(int64_t)nrView(c)->width*2)hiX=(int64_t)nrView(c)->width*2;
    if(hiY>(int64_t)nrView(c)->height*4)hiY=(int64_t)nrView(c)->height*4;
    if(x<loX)x=loX;if(y<loY)y=loY;
    if(right>hiX)right=hiX;if(bottom>hiY)bottom=hiY;
    for(int64_t yy=y;yy<bottom;yy++)for(int64_t xx=x;xx<right;xx++)plotDot(c,xx,yy,color);
}
/* Exact quotient/remainder without a wider integer type or overflowing a*b. */
static uint64_t roundedProduct(uint64_t a,uint64_t b,uint64_t denominator){
    uint64_t quotient=0,remainder=0;int bit=63;
    while(bit>0&&!(b&(UINT64_C(1)<<bit)))bit--;
    for(;bit>=0;bit--){
        uint64_t value=remainder*2+((b>>bit)&1?a:0);
        quotient=quotient*2+value/denominator;remainder=value%denominator;
    }
    return quotient+(remainder+denominator/2>=denominator);
}
static void plotLine(NrContext*c,int64_t x0,int64_t y0,int64_t x1,int64_t y1,uint32_t color){
    int64_t dx=x1>x0?x1-x0:x0-x1,dy=y1>y0?y1-y0:y0-y1;
    int sx=x0<x1?1:-1,sy=y0<y1?1:-1;
    if(!dx&&!dy){plotDot(c,x0,y0,color);return;}
    int horizontal=dx>=dy;int64_t major=horizontal?dx:dy,minor=horizontal?dy:dx;
    int64_t origin=horizontal?x0:y0;int direction=horizontal?sx:sy;
    int64_t lo=(int64_t)(horizontal?c->clip.x:c->clip.y)*(horizontal?2:4);
    int64_t hi=lo+(int64_t)(horizontal?c->clip.width:c->clip.height)*(horizontal?2:4)-1;
    int64_t first=direction>0?lo-origin:origin-hi,last=direction>0?hi-origin:origin-lo;
    if(first<0)first=0;if(last>major)last=major;
    for(int64_t k=first;k<=last;k++){
        int64_t offset=(int64_t)roundedProduct((uint64_t)minor,(uint64_t)k,(uint64_t)major);
        plotDot(c,x0+sx*(horizontal?k:offset),y0+sy*(horizontal?offset:k),color);
    }
}
static double angleAt(double x,double y) {
    double ax=nrAbs(x),ay=nrAbs(y),lo=0,hi=90;
    for(int k=0;k<16;k++){double middle=(lo+hi)*.5;if(ax*nrSin(middle)<ay*nrCos(middle))lo=middle;else hi=middle;}
    double angle=(lo+hi)*.5;if(x<0)angle=180-angle;if(y<0)angle=360-angle;return angle;
}
static uint32_t flatCell(const NrCell*c) {
    if(c->glyph==0x2580||c->glyph==0x2584)return nrMix(c->background,c->foreground,.5);
    if(c->glyph==0x2588)return c->foreground;
    if(c->glyph>=0x2800&&c->glyph<=0x28ff){unsigned mask=c->glyph-0x2800;int n=0;for(;mask;mask>>=1)n+=mask&1;return nrMix(c->background,c->foreground,n/8.0);}
    return c->background;
}
int nrDrawPlot(NrContext*c,const Widget*w,int x,int y,int width,int height,uint32_t color,double alpha,uint32_t id,double materialIndex) {
    if(alpha<=0)return 1;
    memset(c->plotMask,0,(size_t)nrView(c)->width*nrView(c)->height);
    /* An inherited or explicit hybrid plot is a braille object (MIXED-LAYERS.md). */
    int sampling=nrDictatedSampling(w->sampling<0?nrView(c)->sampling:w->sampling,2);
    int64_t wp=(int64_t)width*2,hp=(int64_t)height*4;
    double value=nrClamp((w->value-w->min)/(w->max-w->min),0,1);
    double reveal=w->revealUs?nrEase((nrView(c)->timeUs-w->revealAtUs)/(double)w->revealUs,3):1;
    if(reveal<=0)return 1;
    if(w->kind==8||w->kind==9){
        double total=0;uint32_t colors[128];
        for(int i=0;i<w->dataCount;i++){if(w->data[i]>0)total+=w->data[i];colors[i]=nrOklch(720000,90000,(i*79+180)%360*1000);}
        if(total<=0||reveal<=0||w->sweepAngle<=0)return 1;
        double radius=(width<height*w->cellAspect?width:height*w->cellAspect)-.5;
        double inner=w->kind==9?radius*w->innerRadius:0;
        int64_t px0=(int64_t)c->clip.x*2-(int64_t)x*2,py0=(int64_t)c->clip.y*4-(int64_t)y*4;
        int64_t px1=px0+(int64_t)c->clip.width*2,py1=py0+(int64_t)c->clip.height*4;
        if(px0<0)px0=0;if(py0<0)py0=0;if(px1>wp)px1=wp;if(py1>hp)py1=hp;
        for(int64_t py=py0;py<py1;py++)for(int64_t px=px0;px<px1;px++){
            double vx=px+.5-width,vy=(py+.5-(double)height*2)*w->cellAspect*.5,r2=vx*vx+vy*vy;
            if(r2>radius*radius||r2<inner*inner)continue;
            double angle=angleAt(vx,vy)-w->startAngle;angle-=360*nrFloor(angle/360);
            if(angle>=w->sweepAngle*reveal)continue;
            double target=angle/360*total,cumulative=0;int slice=-1;
            for(int i=0;i<w->dataCount;i++)if(w->data[i]>0){slice=i;cumulative+=w->data[i];if(target<cumulative)break;}
            if(slice>=0)plotDot(c,(int64_t)x*2+px,(int64_t)y*4+py,colors[slice]);
        }
    }else if(w->kind==11||w->kind==13){
        int points=w->kind==13?w->dataCount/2:w->dataCount;
        if(w->kind==13&&points==0){plotLine(c,(int64_t)x*2,(int64_t)y*4,(int64_t)x*2+wp-1,(int64_t)y*4+hp-1,color);}
        int64_t oldX=0,oldY=0;
        for(int i=0;i<points;i++){
            double u=w->kind==13?nrClamp(w->data[i*2],0,1):points>1?i/(double)(points-1):0;
            double v=w->kind==13?nrClamp(w->data[i*2+1],0,1):1-nrClamp(w->data[i],0,1);
            int64_t px=(int64_t)x*2+(int64_t)(u*(wp-1)+.5),py=(int64_t)y*4+(int64_t)(v*(hp-1)+.5);
            if(i)plotLine(c,oldX,oldY,px,py,color);else plotDot(c,px,py,color);oldX=px;oldY=py;
        }
    }else if(w->kind==12){
        static const unsigned digits[10]={0x3f,6,0x5b,0x4f,0x66,0x6d,0x7d,7,0x7f,0x6f};
        int digitWidth=width/2;if(digitWidth<4)return 1;
        int valueInteger=(int)nrAbs(w->value);
        for(int d=0;d<2;d++){
            unsigned mask=digits[d?valueInteger%10:valueInteger/10%10];int64_t left=((int64_t)x+d*(int64_t)digitWidth)*2,right=left+(int64_t)digitWidth*2-2,middle=(int64_t)y*4+hp/2;
            for(int segment=0;segment<7;segment++)if(mask&(1u<<segment)){
                uint32_t ink=nrOklch(780000,110000,(segment*47+d*90+(int)(nrView(c)->timeUs/20000))%360*1000);
                if(segment==0||segment==3||segment==6){int64_t yy=segment==0?(int64_t)y*4:segment==3?(int64_t)y*4+hp-2:middle;plotRect(c,left+2,yy,right-left-2,2,ink);}
                else{int64_t xx=(segment==1||segment==2)?right:left;int64_t lo=(segment==1||segment==5)?(int64_t)y*4+2:middle+2,hi=(segment==1||segment==5)?middle:(int64_t)y*4+hp-2;plotRect(c,xx,lo,2,hi-lo,ink);}
            }
        }
    }else if(w->kind==10){
        for(int i=0;i+1<w->dataCount;i+=2){
            int64_t px=(int64_t)x*2+(int64_t)(nrClamp(w->data[i],0,1)*(wp-1)+.5),py=(int64_t)y*4+(int64_t)((1-nrClamp(w->data[i+1],0,1))*(hp-1)+.5);
            plotDot(c,px,py,color);if(w->mode&1){plotDot(c,px-1,py,color);plotDot(c,px+1,py,color);plotDot(c,px,py-1,color);plotDot(c,px,py+1,color);}
        }
    }else if(w->kind==7){
        int n=w->dataCount;if(!n)return 1;int64_t barWidth=wp/n;if(barWidth<1)barWidth=1;
        for(int i=0;i<n&&i*barWidth<wp;i++){
            double level=nrClamp(w->data[i],0,1)*reveal;int64_t count=(int64_t)(level*hp+.5);
            uint32_t col=nrMix(color,0xe3e1cb,level*.3);
            plotRect(c,(int64_t)x*2+i*barWidth,(int64_t)y*4+hp-count,barWidth-(barWidth>2?2:0),count,col);
        }
    }else if(w->kind==6){
        int64_t count=(int64_t)(wp*value*reveal+.5);uint32_t col=nrMix(color,0xe4e8bf,value*.3);
        plotRect(c,(int64_t)x*2,(int64_t)y*4,count,4,col);
    }else return 0;
    for(int yy=c->clip.y;yy<c->clip.y+c->clip.height;yy++)for(int xx=c->clip.x;xx<c->clip.x+c->clip.width;xx++){
        if(xx<0||yy<0||xx>=(int)nrView(c)->width||yy>=(int)nrView(c)->height)continue;
        unsigned at=yy*nrView(c)->width+xx,mask=c->plotMask[at];
        if(w->kind>=10&&reveal<1)for(int i=0;i<8;i++)if((2.0*((double)xx-x)+i%2+.5)/wp>reveal)mask&=~DOTS[i];
        if(!mask)continue;
        NrCell*out=&c->cells[at];uint32_t base[8],pixels[8],background=flatCell(out);
        for(int i=0;i<8;i++){
            base[i]=pixels[i]=background;if(!(mask&DOTS[i]))continue;
            uint32_t dotColor=c->plotColor[at][i];
            if(w->material>=0&&w->material<NR_MATERIALS&&nrView(c)->materialPatterns[w->material].used){
                int64_t xQ8=(int64_t)xx*256+(i%2)*128+64;
                int64_t yQ8=(int64_t)yy*256+(i/2)*64+32;
                if(xQ8>INT32_MAX)xQ8=INT32_MAX;if(xQ8<INT32_MIN)xQ8=INT32_MIN;
                if(yQ8>INT32_MAX)yQ8=INT32_MAX;if(yQ8<INT32_MIN)yQ8=INT32_MIN;
                double materialAlpha=1;
                dotColor=nrPaintAt(nrView(c),w->material,nrView(c)->timeUs,
                                   (int32_t)xQ8,(int32_t)yQ8,materialIndex,&materialAlpha);
            }
            if(c->paintBlend){uint32_t mixed[2]={background,65535};nrComposite(background,dotColor,65535,(uint32_t)(nrClamp(alpha,0,1)*65535+.5),(uint32_t)c->paintBlend,0,at,mixed);pixels[i]=mixed[0];}
            else pixels[i]=nrMix(background,dotColor,alpha);
        }
        nrResolveSamples(out,pixels,base,mask,sampling==0?2:sampling);
        if(sampling==0)out->glyph=0x2588;
        out->id=id;
        c->characterIndices[at]=UINT32_MAX;
        c->characterOwners[at]=c->characterOwner;
    }
    return 1;
}
