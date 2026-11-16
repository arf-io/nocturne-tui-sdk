/* Nocturne world v1: deterministic Q8 dioramas and an owned half-cell z-buffer.
 * Flat-shaded meshes, perspective-correct depth, near-plane clipping and
 * ordered translucent light. This is art-directed geometry, not fluid/GR physics. */
#include "nocturne_world.h"
#include "world_fields.inc"
typedef struct WPoint {
    int32_t x , y , z ;
}
WPoint ;
typedef struct WScreen {
    int32_t x , y , z ;
}
WScreen ;
typedef struct WCanvas {
    const NsWorldConfig * config ;
    const NsWorldDetail * detail ;
    int32_t width , height ;
    uint32_t * color ;
    int32_t * depth ;
    int32_t sy , cy , sp , cp , sr , cr , focal ;
    uint64_t time ;
    uint32_t triangles , points ;
}
WCanvas ;
static int32_t wSin ( int64_t angle ) {
    int32_t q = modI ( angle , 360 * 256 ) ;
    int64_t phase = ( int64_t ) q * 1024 ;
    int32_t k = ( int32_t ) ( phase / ( 360 * 256 ) ) , r = ( int32_t ) ( phase % ( 360 * 256 ) ) ;
    return sinI ( k ) + ( int32_t ) ( ( int64_t ) ( sinI ( k + 1 ) - sinI ( k ) ) * r / ( 360 * 256 ) ) ;
}
static int32_t wCos ( int64_t a ) {
    return wSin ( a + 90 * 256 ) ;
}
static int32_t wWave ( int64_t phase ) {
    return sinI ( phase ) ;
}
static uint32_t wMix ( uint32_t a , uint32_t b , int32_t t ) {
    t = clampI ( t , 0 , 1000 ) ;
    return rgbI ( ( redI ( a ) * ( 1000 - t ) + redI ( b ) * t ) / 1000 , ( greenI ( a ) * ( 1000 - t ) + greenI ( b ) * t ) / 1000 , ( blueI ( a ) * ( 1000 - t ) + blueI ( b ) * t ) / 1000 ) ;
}
static uint32_t wShade ( uint32_t a , int32_t t ) {
    return wMix ( 0 , a , t ) ;
}
static WPoint wP ( int32_t x , int32_t y , int32_t z ) {
    WPoint p = {
        x , y , z
    }
    ;
    return p ;
}
static WPoint wV ( int32_t x , int32_t y , int32_t z ) {
    return wP ( x * 256 , y * 256 , z * 256 ) ;
}
static WPoint wCamera ( const WCanvas * c , WPoint p ) {
    const int32_t * v = c -> config -> v ;
    int64_t x = ( int64_t ) p . x - v [ NSW_CAMERA_X ] , y = ( int64_t ) p . y - v [ NSW_CAMERA_Y ] , z = ( int64_t ) p . z - v [ NSW_CAMERA_Z ] ;
    int64_t a = ( x * c -> cy - z * c -> sy ) / 1000 , b = ( x * c -> sy + z * c -> cy ) / 1000 ;
    int64_t u = ( y * c -> cp - b * c -> sp ) / 1000 , d = ( y * c -> sp + b * c -> cp ) / 1000 ;
    return wP ( ( int32_t ) ( ( a * c -> cr + u * c -> sr ) / 1000 ) , ( int32_t ) ( ( u * c -> cr - a * c -> sr ) / 1000 ) , ( int32_t ) d ) ;
}
static WScreen wProject ( const WCanvas * c , WPoint p ) {
    WScreen s ;
    s . z = p . z ;
    if ( c -> config -> v [ NSW_PROJECTION ] ) {
        int32_t span = c -> config -> v [ NSW_SPAN ] ;
        s . x = c -> width * 8 + ( int32_t ) ( ( int64_t ) p . x * c -> width * 16 / span ) ;
        s . y = c -> height * 8 - ( int32_t ) ( ( int64_t ) p . y * c -> width * 16 / span ) ;
    }
    else {
        s . x = c -> width * 8 + ( int32_t ) ( ( int64_t ) p . x * c -> focal / p . z ) ;
        s . y = c -> height * 8 - ( int32_t ) ( ( int64_t ) p . y * c -> focal / p . z ) ;
    }
    return s ;
}
static int32_t wDepth ( const WCanvas * c , int32_t z ) {
    return c -> config -> v [ NSW_PROJECTION ] ? 268435456 - z : ( 1 << 26 ) / z ;
}
static int64_t wEdge ( WScreen a , WScreen b , int32_t x , int32_t y ) {
    return ( int64_t ) ( x - a . x ) * ( b . y - a . y ) - ( int64_t ) ( y - a . y ) * ( b . x - a . x ) ;
}
static void wRaster ( WCanvas * c , WPoint a , WPoint b , WPoint d , uint32_t color , int32_t alpha ) {
    WScreen p = wProject ( c , a ) , q = wProject ( c , b ) , r = wProject ( c , d ) ;
    int64_t area = wEdge ( p , q , r . x , r . y ) ;
    if ( ! area ) return ;
    if ( area < 0 ) {
        WScreen t = q ;
        q = r ;
        r = t ;
        area = - area ;
    }
    int32_t x0 = clampI ( ( p . x < q . x ? ( p . x < r . x ? p . x : r . x ) : ( q . x < r . x ? q . x : r . x ) ) / 16 , 0 , c -> width - 1 ) , x1 = clampI ( ( p . x > q . x ? ( p . x > r . x ? p . x : r . x ) : ( q . x > r . x ? q . x : r . x ) ) / 16 + 1 , 0 , c -> width - 1 ) ;
    int32_t y0 = clampI ( ( p . y < q . y ? ( p . y < r . y ? p . y : r . y ) : ( q . y < r . y ? q . y : r . y ) ) / 16 , 0 , c -> height - 1 ) , y1 = clampI ( ( p . y > q . y ? ( p . y > r . y ? p . y : r . y ) : ( q . y > r . y ? q . y : r . y ) ) / 16 + 1 , 0 , c -> height - 1 ) ;
    int32_t ip = wDepth ( c , p . z ) , iq = wDepth ( c , q . z ) , ir = wDepth ( c , r . z ) ;
    for ( int32_t y = y0 ; y <= y1 ; y ++ ) for ( int32_t x = x0 ; x <= x1 ; x ++ ) {
        int64_t e0 = wEdge ( q , r , x * 16 + 8 , y * 16 + 8 ) , e1 = wEdge ( r , p , x * 16 + 8 , y * 16 + 8 ) , e2 = wEdge ( p , q , x * 16 + 8 , y * 16 + 8 ) ;
        if ( e0 < 0 || e1 < 0 || e2 < 0 ) continue ;
        int32_t z = ( int32_t ) ( ( e0 * ip + e1 * iq + e2 * ir ) / area ) ;
        uint32_t i = ( uint32_t ) y * c -> width + x ;
        if ( z >= c -> depth [ i ] ) {
            c -> color [ i ] = alpha >= 1000 ? color : wMix ( c -> color [ i ] , color , alpha ) ;
            if ( alpha >= 750 ) c -> depth [ i ] = z ;
        }
    }
    c -> triangles ++ ;
}
/* Five-plane clipping keeps projected coordinates and integer barycentric
 * products bounded, including hostile cameras beside the near plane. */
static int64_t wPlane ( const WCanvas * c , WPoint p , int plane ) {
    if ( plane == 0 ) return p . z - 384 ;
    if ( c -> config -> v [ NSW_PROJECTION ] ) {
        int64_t half = c -> config -> v [ NSW_SPAN ] / 2 ;
        switch ( plane ) {
            case 1 : return p . x + half ;
            case 2 : return half - p . x ;
            case 3 : return ( int64_t ) p . y * c -> width + half * c -> height ;
            default : return half * c -> height - ( int64_t ) p . y * c -> width ;
        }
    }
    switch ( plane ) {
        case 1 : return ( int64_t ) p . x * c -> focal + ( int64_t ) p . z * c -> width * 8 ;
        case 2 : return ( int64_t ) p . z * c -> width * 8 - ( int64_t ) p . x * c -> focal ;
        case 3 : return ( int64_t ) p . y * c -> focal + ( int64_t ) p . z * c -> height * 8 ;
        default : return ( int64_t ) p . z * c -> height * 8 - ( int64_t ) p . y * c -> focal ;
    }
}
static void wTriangle ( WCanvas * c , WPoint a , WPoint b , WPoint d , uint32_t color , int32_t alpha ) {
    WPoint p [ 12 ] , q [ 12 ] ;
    p [ 0 ] = wCamera ( c , a ) ;
    p [ 1 ] = wCamera ( c , b ) ;
    p [ 2 ] = wCamera ( c , d ) ;
    int count = 3 ;
    for ( int plane = 0 ; plane < 5 && count >= 3 ; plane ++ ) {
        int n = 0 ;
        for ( int i = 0 ; i < count ; i ++ ) {
            WPoint u = p [ i ] , v = p [ ( i + 1 ) % count ] ;
            int64_t du = wPlane ( c , u , plane ) , dv = wPlane ( c , v , plane ) ;
            if ( du >= 0 && n < 12 ) q [ n ++ ] = u ;
            if ( ( du >= 0 ) != ( dv >= 0 ) && n < 12 ) {
                int64_t t = du * 65536 / ( du - dv ) ;
                q [ n ++ ] = wP ( u . x + ( int32_t ) ( ( ( int64_t ) v . x - u . x ) * t / 65536 ) , u . y + ( int32_t ) ( ( ( int64_t ) v . y - u . y ) * t / 65536 ) , u . z + ( int32_t ) ( ( ( int64_t ) v . z - u . z ) * t / 65536 ) ) ;
            }
        }
        count = n ;
        for ( int i = 0 ; i < n ; i ++ ) p [ i ] = q [ i ] ;
    }
    if ( count >= 3 ) for ( int i = 1 ; i < count - 1 ; i ++ ) if ( p [ 0 ] . z >= 384 && p [ i ] . z >= 384 && p [ i + 1 ] . z >= 384 ) wRaster ( c , p [ 0 ] , p [ i ] , p [ i + 1 ] , color , alpha ) ;
}
static void wQuad ( WCanvas * c , WPoint a , WPoint b , WPoint d , WPoint e , uint32_t color , int32_t alpha ) {
    wTriangle ( c , a , b , d , color , alpha ) ;
    wTriangle ( c , a , d , e , color , alpha ) ;
}
static void wDot ( WCanvas * c , WPoint p , uint32_t color , int32_t alpha , int32_t radius ) {
    p = wCamera ( c , p ) ;
    for ( int plane = 0 ; plane < 5 ; plane ++ ) if ( wPlane ( c , p , plane ) < 0 ) return ;
    WScreen s = wProject ( c , p ) ;
    int32_t cx = s . x / 16 , cy = s . y / 16 , iz = wDepth ( c , p . z ) ;
    for ( int32_t y = cy - radius ; y <= cy + radius ; y ++ ) for ( int32_t x = cx - radius ; x <= cx + radius ; x ++ ) {
        if ( x < 0 || y < 0 || x >= c -> width || y >= c -> height ) continue ;
        if ( radius && ( ( x - cx ) * ( x - cx ) + ( y - cy ) * ( y - cy ) > radius * radius ) ) continue ;
        uint32_t i = ( uint32_t ) y * c -> width + x ;
        if ( iz >= c -> depth [ i ] ) {
            c -> color [ i ] = wMix ( c -> color [ i ] , color , alpha ) ;
            if ( alpha >= 950 ) c -> depth [ i ] = iz ;
        }
    }
    c -> points ++ ;
}
static void wLine ( WCanvas * c , WPoint a , WPoint b , uint32_t color , int32_t alpha ) {
    WPoint u = wCamera ( c , a ) , v = wCamera ( c , b ) ;
    for ( int plane = 0 ; plane < 5 ; plane ++ ) {
        int64_t a0 = wPlane ( c , u , plane ) , b0 = wPlane ( c , v , plane ) ;
        if ( a0 < 0 && b0 < 0 ) return ;
        if ( ( a0 >= 0 ) != ( b0 >= 0 ) ) {
            int64_t t = a0 * 65536 / ( a0 - b0 ) ;
            WPoint p = wP ( u . x + ( int32_t ) ( ( ( int64_t ) v . x - u . x ) * t / 65536 ) , u . y + ( int32_t ) ( ( ( int64_t ) v . y - u . y ) * t / 65536 ) , u . z + ( int32_t ) ( ( ( int64_t ) v . z - u . z ) * t / 65536 ) ) ;
            if ( a0 < 0 ) u = p ;
            else v = p ;
        }
    }
    if ( u . z < 384 || v . z < 384 ) return ;
    WScreen p = wProject ( c , u ) , q = wProject ( c , v ) ;
    int32_t dx = q . x - p . x , dy = q . y - p . y , n = clampI ( ( ( dx < 0 ? - dx : dx ) > ( dy < 0 ? - dy : dy ) ? ( dx < 0 ? - dx : dx ) : ( dy < 0 ? - dy : dy ) ) / 12 + 1 , 1 , 2048 ) ;
    for ( int32_t k = 0 ; k <= n ; k ++ ) {
        int32_t x = ( int32_t ) ( p . x + ( int64_t ) dx * k / n ) / 16 , y = ( int32_t ) ( p . y + ( int64_t ) dy * k / n ) / 16 ;
        if ( x < 0 || y < 0 || x >= c -> width || y >= c -> height ) continue ;
        int32_t iz = ( int32_t ) ( ( ( int64_t ) wDepth ( c , u . z ) * ( n - k ) + ( int64_t ) wDepth ( c , v . z ) * k ) / n ) ;
        uint32_t i = ( uint32_t ) y * c -> width + x ;
        if ( iz >= c -> depth [ i ] ) {
            c -> color [ i ] = wMix ( c -> color [ i ] , color , alpha ) ;
            if ( alpha >= 950 ) c -> depth [ i ] = iz ;
        }
    }
}
static void wBox ( WCanvas * c , int32_t x , int32_t y , int32_t z , int32_t sx , int32_t sy , int32_t sz , uint32_t color ) {
    WPoint a = wP ( x - sx , y , z - sz ) , b = wP ( x + sx , y , z - sz ) , d = wP ( x + sx , y , z + sz ) , e = wP ( x - sx , y , z + sz ) , u = wP ( x - sx , y - sy , z - sz ) , v = wP ( x + sx , y - sy , z - sz ) , w = wP ( x + sx , y - sy , z + sz ) , t = wP ( x - sx , y - sy , z + sz ) ;
    wQuad ( c , a , b , d , e , color , 1000 ) ;
    wQuad ( c , u , v , b , a , wShade ( color , 600 ) , 1000 ) ;
    wQuad ( c , v , w , d , b , wShade ( color , 460 ) , 1000 ) ;
    wQuad ( c , w , t , e , d , wShade ( color , 730 ) , 1000 ) ;
    wQuad ( c , t , u , a , e , wShade ( color , 820 ) , 1000 ) ;
}
static void wTree ( WCanvas * c , int32_t x , int32_t y , int32_t z , int32_t h , uint32_t color ) {
    wLine ( c , wP ( x , y , z ) , wP ( x , y + h , z ) , 0x81705e , 1000 ) ;
    for ( int k = 0 ; k < 3 ; k ++ ) {
        int32_t b = y + h * k / 4 , rad = h * ( 4 - k ) / 10 ;
        WPoint top = wP ( x , b + h / 2 , z ) , a = wP ( x - rad , b , z - rad ) , d = wP ( x + rad , b , z - rad ) , e = wP ( x + rad , b , z + rad ) , f = wP ( x - rad , b , z + rad ) ;
        wTriangle ( c , a , d , top , wShade ( color , 730 ) , 1000 ) ;
        wTriangle ( c , d , e , top , wShade ( color , 600 ) , 1000 ) ;
        wTriangle ( c , e , f , top , color , 1000 ) ;
        wTriangle ( c , f , a , top , wShade ( color , 900 ) , 1000 ) ;
    }
}
static WPoint wWaterPoint ( int x , int j , int64_t phase ) {
    return wP ( x * 256 , ( 25 - j ) * 256 , ( - 3 + x * x / 150 ) * 256 + wWave ( x * 43 + j * 23 + phase / 6 ) / 18 ) ;
}
static void wWaterfall ( WCanvas * c ) {
    const int32_t * v = c -> config -> v ;
    uint32_t rock = v [ NSW_SECONDARY ] ? ( uint32_t ) v [ NSW_SECONDARY ] : 0x35434d , accent = v [ NSW_ACCENT ] ? ( uint32_t ) v [ NSW_ACCENT ] : 0x86cfc5 , foam = v [ NSW_INK ] ? ( uint32_t ) v [ NSW_INK ] : 0xdde9d7 ;
    int64_t phase = ( int64_t ) ( c -> time % 3600000 ) * v [ NSW_FLOW ] / 1000 ;
    /* Striated crescent escarpment: independent basalt columns cast side planes. */
    for ( int z = 32 ; z >= 8 ; z -= 8 ) for ( int x = - 36 ; x <= 36 ; x += 6 ) {
        uint32_t h = hashI ( ( uint32_t ) ( x * 993 + z * 719 ) ^ v [ NSW_SEED ] ) ;
        int32_t y = ( 21 + ( int32_t ) ( h % 4 ) ) * 256 ;
        wBox ( c , x * 256 , y , z * 256 , 3 * 256 , ( ( int32_t ) ( h % 5 ) + 32 ) * 256 , 4 * 256 , wMix ( rock , 0x74847a , ( int32_t ) ( h % 230 ) ) ) ;
    }
    for ( int x = - 36 ; x <= 36 ; x += 4 ) {
        int32_t z = ( 4 + x * x / 140 ) * 256 ;
        uint32_t h = hashI ( ( uint32_t ) ( x + 55 ) * 717 + v [ NSW_SEED ] ) ;
        wBox ( c , x * 256 , ( 21 + ( int32_t ) ( h % 3 ) ) * 256 , z , 2 * 256 , ( 30 + ( int32_t ) ( h % 6 ) ) * 256 , 4 * 256 , wMix ( rock , 0x97a99b , ( int32_t ) ( h % 260 ) ) ) ;
        for ( int k = 0 ; k < 5 ; k ++ ) wLine ( c , wP ( ( x - 2 ) * 256 , ( 15 - k * 5 ) * 256 , z - 4 * 256 - 8 ) , wP ( ( x + 2 ) * 256 , ( 15 - k * 5 ) * 256 , z - 4 * 256 - 8 ) , wShade ( 0x92aba7 , 300 + k * 25 ) , 600 ) ;
    }
    /* Lower basin has volume and a chipped basalt edge, not a floating ellipse. */
    for ( int a = 0 ; a < 64 ; a ++ ) {
        int an = a * 360 * 256 / 64 , bn = ( a + 1 ) * 360 * 256 / 64 ;
        WPoint p = wP ( wCos ( an ) * 32 * 256 / 1000 , - 11 * 256 , wSin ( an ) * 32 * 256 / 1350 - 20 * 256 ) , q = wP ( wCos ( bn ) * 32 * 256 / 1000 , - 11 * 256 , wSin ( bn ) * 32 * 256 / 1350 - 20 * 256 ) ;
        wQuad ( c , p , q , wP ( q . x , - 18 * 256 , q . z ) , wP ( p . x , - 18 * 256 , p . z ) , wShade ( rock , 850 ) , 1000 ) ;
        wQuad ( c , p , q , wP ( wCos ( bn ) * 29 * 256 / 1000 , - 11 * 256 , wSin ( bn ) * 29 * 256 / 1350 - 20 * 256 ) , wP ( wCos ( an ) * 29 * 256 / 1000 , - 11 * 256 , wSin ( an ) * 29 * 256 / 1350 - 20 * 256 ) , wShade ( rock , 900 ) , 1000 ) ;
        if ( a % 4 == 0 ) wBox ( c , p . x , - 10 * 256 , p . z , 256 , 3 * 256 , 256 , wMix ( rock , 0x687f72 , 350 ) ) ;
    }
    /* Basin bowl and upper river. */
    for ( int ring = 10 ; ring >= 1 ; ring -- ) for ( int a = 0 ; a < 64 ; a ++ ) {
        int32_t r = ring * 3 * 256 ;
        int32_t an = a * 360 * 256 / 64 , bn = ( a + 1 ) * 360 * 256 / 64 ;
        WPoint center = wV ( 0 , - 10 , - 20 ) , p = wP ( wCos ( an ) * r / 1000 , - 10 * 256 , wSin ( an ) * r / 1350 - 20 * 256 ) , q = wP ( wCos ( bn ) * r / 1000 , - 10 * 256 , wSin ( bn ) * r / 1350 - 20 * 256 ) ;
        uint32_t co = wMix ( 0x142b37 , accent , 110 + ring * 10 ) ;
        wTriangle ( c , center , p , q , co , 1000 ) ;
    }
    for ( int z = 36 ; z >= 5 ; z -- ) for ( int x = - 11 ; x < 11 ; x ++ ) {
        int wave = wWave ( ( int64_t ) x * 37 + z * 29 - phase / 7 ) ;
        uint32_t co = wMix ( 0x244454 , accent , 300 + wave / 6 ) ;
        wQuad ( c , wV ( x , 25 , z ) , wV ( x + 1 , 25 , z ) , wV ( x + 1 , 25 , z + 1 ) , wV ( x , 25 , z + 1 ) , co , 1000 ) ;
    }
    if (c->detail && c->detail->v[7]) {
        for (int x=-12;x<12;x++) {
            WPoint a=wWaterPoint(x,0,phase), b=wWaterPoint(x+1,0,phase);
            wQuad(c,wV(x,25,5),wV(x+1,25,5),b,a,
                wMix(0x244454,accent,380+wWave(x*37-phase/7)/6),1000);
        }
    }
    /* Hanging ribbons with independently advected highlights; flow=0 closes gate. */
    if ( v [ NSW_FLOW ] > 0 ) for ( int x = - 12 ; x < 12 ; x ++ ) for ( int j = 0 ; j < 36 ; j ++ ) {
        WPoint a = wWaterPoint ( x , j , phase ) , b = wWaterPoint ( x + 1 , j , phase ) , d = wWaterPoint ( x + 1 , j + 1 , phase ) , e = wWaterPoint ( x , j + 1 , phase ) ;
        int streak = ( wWave ( x * 77 + j * 41 + phase / 4 ) + 1000 ) / 2 ;
        uint32_t co = wMix ( accent , foam , streak * 3 / 5 ) ;
        wQuad ( c , a , b , d , e , co , v [ NSW_WATER_ALPHA ] ) ;
    }
    /* Surface caustics and expanding foam at the plunge pool. */
    for ( int n = 0 ; n < 25 ; n ++ ) {
        int32_t r = ( int32_t ) ( ( phase * 3 + n * 339 ) % 5000 ) + 700 ;
        for ( int a = 0 ; a < 48 ; a ++ ) {
            int an = a * 360 * 256 / 48 ;
            WPoint p = wP ( wCos ( an ) * r / 1000 , - 10 * 256 + 20 , - 6 * 256 + wSin ( an ) * r / 1800 ) ;
            wDot ( c , p , wMix ( accent , foam , 400 ) , clampI ( 600 - r / 12 , 30 , 500 ) , 0 ) ;
        }
    }
    for ( int n = 0 ; n < 160 && v [ NSW_FLOW ] > 0 ; n ++ ) {
        uint32_t h = hashI ( ( uint32_t ) n * 9941 + v [ NSW_SEED ] ) ;
        int age = ( int ) ( ( phase + ( h % 3500 ) ) % 3500 ) ;
        WPoint p = wP ( ( ( int32_t ) ( h % 6000 ) - 3000 ) + wWave ( n * 47 + age / 8 ) / 4 , - 9 * 256 + age / 2 , - 3 * 256 - age / 6 + ( int32_t ) ( h % 1100 ) ) ;
        wDot ( c , p , foam , clampI ( ( 3500 - age ) / 9 , 0 , 350 ) , 0 ) ;
    }
    for ( int i = 0 ; i < 18 ; i ++ ) {
        uint32_t h = hashI ( i * 1811 + v [ NSW_SEED ] ) ;
        int x = ( i % 2 ? - 1 : 1 ) * ( 18 + ( int ) ( h % 17 ) ) , z = 12 + ( int ) ( h % 21 ) ;
        wTree ( c , x * 256 , 25 * 256 , z * 256 , ( 7 + ( int ) ( h % 5 ) ) * 256 , wMix ( 0x347769 , 0x94ad7b , ( int ) ( h % 350 ) ) ) ;
    }
    /* Narrow timber crossing supplies human scale without becoming a UI box. */
    for ( int x = - 15 ; x <= 15 ; x ++ ) {
        int32_t y = ( 27 * 256 ) - ( x * x * 256 / 130 ) ;
        wBox ( c , x * 256 , y , 24 * 256 , 110 , 70 , 2 * 256 , 0x988369 ) ;
        if ( x % 3 == 0 ) {
            wLine ( c , wP ( x * 256 , y , 22 * 256 ) , wP ( x * 256 , y + 3 * 256 , 22 * 256 ) , 0xb9a785 , 1000 ) ;
            wLine ( c , wP ( x * 256 , y , 26 * 256 ) , wP ( x * 256 , y + 3 * 256 , 26 * 256 ) , 0xb9a785 , 1000 ) ;
        }
    }
}
static int32_t wTerrain ( int32_t x , int32_t z ) {
    int32_t ridge = ( wWave ( x * 9 + z * 3 ) + 1000 ) * 7 / 1000 + ( wWave ( z * 13 - x * 3 ) + 1000 ) * 4 / 1000 ;
    int32_t trench = clampI ( 15 - ( x < 0 ? - x : x ) , 0 , 15 ) ;
    return ( - 18 + ridge - trench / 2 ) * 256 ;
}
static int32_t wRoadX ( int32_t zQ8 ) {
    return wWave ( ( int64_t ) zQ8 * 6 / 256 ) * 23 * 256 / 1000 ;
}
static int32_t wRoadY ( int32_t zQ8 ) {
    return 6 * 256 + wWave ( ( int64_t ) zQ8 * 2 / 256 ) * 5 * 256 / 1000 ;
}
static void wLandscape ( WCanvas * c , int road ) {
    const int32_t * v = c -> config -> v ;
    uint32_t sand = v [ NSW_ACCENT ] ? ( uint32_t ) v [ NSW_ACCENT ] : 0xb48672 ;
    for ( int z = 60 ; z > - 64 ; z -= 4 ) for ( int x = - 60 ; x < 64 ; x += 4 ) {
        WPoint a = wP ( x * 256 , wTerrain ( x , z ) , z * 256 ) , b = wP ( ( x + 4 ) * 256 , wTerrain ( x + 4 , z ) , z * 256 ) , d = wP ( ( x + 4 ) * 256 , wTerrain ( x + 4 , z - 4 ) , ( z - 4 ) * 256 ) , e = wP ( x * 256 , wTerrain ( x , z - 4 ) , ( z - 4 ) * 256 ) ;
        int sh = clampI ( 450 + ( a . y + 18 * 256 ) / 14 + ( a . y - b . y ) / 9 + ( a . y - e . y ) / 10 , 240 , 840 ) ;
        uint32_t co = wMix ( 0x292e4b , sand , sh ) ;
        wTriangle ( c , a , b , d , co , 1000 ) ;
        wTriangle ( c , a , d , e , wShade ( co , 940 ) , 1000 ) ;
        if ( x == - 60 ) wQuad ( c , a , e , wP ( e . x , - 32 * 256 , e . z ) , wP ( a . x , - 32 * 256 , a . z ) , wShade ( co , 450 ) , 1000 ) ;
        if ( x == 60 ) wQuad ( c , b , d , wP ( d . x , - 32 * 256 , d . z ) , wP ( b . x , - 32 * 256 , b . z ) , wShade ( co , 380 ) , 1000 ) ;
        if ( z == - 60 ) wQuad ( c , e , d , wP ( d . x , - 32 * 256 , d . z ) , wP ( e . x , - 32 * 256 , e . z ) , wShade ( co , 460 ) , 1000 ) ;
    }
    if ( ! road ) {
        for ( int z = - 60 ; z < 60 ; z ++ ) {
            int32_t x = wWave ( z * 5 ) * 6 * 256 / 1000 , y = wTerrain ( x / 256 , z ) + 50 ;
            wQuad ( c , wP ( x - 3 * 256 , y , z * 256 ) , wP ( x + 3 * 256 , y , z * 256 ) , wP ( x + 3 * 256 , y , ( z + 2 ) * 256 ) , wP ( x - 3 * 256 , y , ( z + 2 ) * 256 ) , wMix ( 0x255361 , 0x9ac7b8 , ( wWave ( z * 34 - ( int64_t ) c -> time / 11 ) + 1000 ) / 6 ) , 1000 ) ;
        }
        return ;
    }
    int64_t travel = v [ NSW_TRAVEL ] ;
    for ( int z = - 62 ; z < 62 ; z += 2 ) {
        int32_t z1 = z * 256 , z2 = ( z + 2 ) * 256 , x1 = wRoadX ( z1 ) , x2 = wRoadX ( z2 ) , y1 = wRoadY ( z1 ) , y2 = wRoadY ( z2 ) ;
        WPoint a = wP ( x1 - 6 * 256 , y1 , z1 ) , b = wP ( x1 + 6 * 256 , y1 , z1 ) , d = wP ( x2 + 6 * 256 , y2 , z2 ) , e = wP ( x2 - 6 * 256 , y2 , z2 ) ;
        wQuad ( c , a , b , d , e , 0x343f51 , 1000 ) ;
        wQuad ( c , a , e , wP ( e . x , e . y - 512 , e . z ) , wP ( a . x , a . y - 512 , a . z ) , 0x798081 , 1000 ) ;
        wQuad ( c , b , d , wP ( d . x , d . y - 512 , d . z ) , wP ( b . x , b . y - 512 , b . z ) , 0x42475b , 1000 ) ;
        for ( int side = - 1 ; side <= 1 ; side += 2 ) {
            wLine ( c , wP ( x1 + side * 5 * 256 , y1 + 40 , z1 ) , wP ( x2 + side * 5 * 256 , y2 + 40 , z2 ) , 0xdfbc9c , 1000 ) ;
            if ( z % 8 == 0 ) {
                wLine ( c , wP ( x1 + side * 6 * 256 , y1 , z1 ) , wP ( x1 + side * 6 * 256 , y1 + 2 * 256 , z1 ) , 0xc7b6a6 , 1000 ) ;
                wDot ( c , wP ( x1 + side * 6 * 256 , y1 + 2 * 256 , z1 ) , side < 0 ? 0xe6d7a8 : 0xbe887c , 900 , 0 ) ;
            }
        }
        if ( z % 16 == 0 ) for ( int side = - 1 ; side <= 1 ; side += 2 ) wBox ( c , x1 + side * 4 * 256 , y1 - 512 , z1 , 180 , y1 - 512 - wTerrain ( ( x1 + side * 4 * 256 ) / 256 , z ) , 180 , 0x5b6874 ) ;
    }
    for ( int d = 0 ; d < 11 ; d ++ ) {
        int32_t z1 = modI ( ( int64_t ) d * 12 * 256 - travel , 132 * 256 ) - 66 * 256 , z2 = z1 + 5 * 256 ;
        if ( z1 < - 62 * 256 || z2 > 62 * 256 ) continue ;
        int32_t x1 = wRoadX ( z1 ) , x2 = wRoadX ( z2 ) , y1 = wRoadY ( z1 ) + 48 , y2 = wRoadY ( z2 ) + 48 ;
        wQuad ( c , wP ( x1 - 60 , y1 , z1 ) , wP ( x1 + 60 , y1 , z1 ) , wP ( x2 + 60 , y2 , z2 ) , wP ( x2 - 60 , y2 , z2 ) , 0xe9d9a5 , 1000 ) ;
    }
}
static WPoint wDiscPoint ( int32_t r , int32_t angle , int32_t tilt , int32_t height ) {
    int32_t x = wCos ( angle ) * r / 1000 , z = wSin ( angle ) * r / 1000 ;
    return wP ( x , height + wSin ( tilt ) * z / 1000 , wCos ( tilt ) * z / 1000 ) ;
}
static void wAccretion ( WCanvas * c ) {
    const int32_t * v = c -> config -> v ;
    int tilt = v [ NSW_DISC_TILT ] , time = ( int ) ( c -> time % 7200000 ) ;
    uint32_t gold = v [ NSW_ACCENT ] ? ( uint32_t ) v [ NSW_ACCENT ] : 0xebbb7a ;
    /* Black sphere is a depth-writing solid, not a circular screen overlay. */
    for ( int lat = - 90 ; lat < 90 ; lat += 10 ) for ( int lon = 0 ; lon < 360 ; lon += 10 ) {
        WPoint p [ 4 ] ;
        int aa [ 4 ] = {
            lat , lat , lat + 10 , lat + 10
        }
        , bb [ 4 ] = {
            lon , lon + 10 , lon + 10 , lon
        }
        ;
        for ( int k = 0 ; k < 4 ; k ++ ) {
            int32_t r = wCos ( aa [ k ] * 256 ) * 9 * 256 / 1000 ;
            p [ k ] = wP ( wCos ( bb [ k ] * 256 ) * r / 1000 , wSin ( aa [ k ] * 256 ) * 9 * 256 / 1000 , wSin ( bb [ k ] * 256 ) * r / 1000 ) ;
        }
        wQuad ( c , p [ 0 ] , p [ 1 ] , p [ 2 ] , p [ 3 ] , 0x07090f , 1000 ) ;
    }
    int segments = v [ NSW_DETAIL ] == 2 ? 192 : ( v [ NSW_DETAIL ] == 1 ? 128 : 80 ) ;
    for ( int ring = 0 ; ring < 25 ; ring ++ ) {
        int32_t r = ( 10 * 256 ) + ring * 310 , outer = r + 310 ;
        for ( int j = 0 ; j < segments ; j ++ ) {
            int32_t a = j * 360 * 256 / segments , b = ( j + 1 ) * 360 * 256 / segments ;
            int wave = wSin ( ( int64_t ) a * 2 - ring * 6800 - time * 2 ) ;
            int bright = clampI ( 930 - ring * 24 + wave / 8 , 150 , 1000 ) ;
            uint32_t co = wMix ( 0x61304c , gold , bright ) ;
            int32_t radialVelocity = ( - wSin ( a ) * c -> sy + wCos ( a ) * wSin ( tilt ) / 1000 * c -> sp + wCos ( a ) * wCos ( tilt ) / 1000 * c -> cy * c -> cp / 1000 ) / 1000 ;
            int recede = clampI ( ( radialVelocity + 1000 ) / 2 , 0 , 1000 ) ;
            co = wMix ( co , 0xcc593f , recede * v [ NSW_REDSHIFT ] / 1300 ) ;
            co = wMix ( co , 0xe5e8ff , ( 1000 - recede ) * v [ NSW_REDSHIFT ] / 2400 ) ;
            wQuad ( c , wDiscPoint ( r , a , tilt , 0 ) , wDiscPoint ( outer , a , tilt , 0 ) , wDiscPoint ( outer , b , tilt , 0 ) , wDiscPoint ( r , b , tilt , 0 ) , wShade ( co , bright ) , 1000 ) ;
        }
    }
    for ( int n = 0 ; n < 520 ; n ++ ) {
        uint32_t h = hashI ( ( uint32_t ) n * 1297u + ( uint32_t ) v [ NSW_SEED ] ) ;
        int age = ( int ) ( ( c -> time + ( h % 18000 ) ) % 18000 ) ;
        int32_t radius = 50 * 256 - age * 40 * 256 / 18000 , angular = ( int ) ( h % ( 360 * 256 ) ) + age * 5 + ( int32_t ) ( ( int64_t ) age * ( 50 * 256 - radius ) / 1024 ) ;
        WPoint p = wDiscPoint ( radius , angular , tilt , ( int32_t ) ( h % 180 ) - 90 ) ;
        int alpha = clampI ( age * 3 , 0 , 1000 ) ;
        alpha = clampI ( ( 18000 - age ) * 2 , 0 , alpha ) ;
        wDot ( c , p , wMix ( gold , 0xf5e7d0 , ( int ) ( h % 600 ) ) , alpha , 0 ) ;
        if ( n % 2 == 0 ) wLine ( c , wDiscPoint ( radius + 24 , angular - 700 , tilt , 0 ) , p , wShade ( gold , 700 ) , alpha * 3 / 4 ) ;
    }
    /* Thin photon torus accent, with occlusion supplied by the sphere itself. */
    for ( int a = 0 ; a < 360 * 256 ; a += 256 ) {
        WPoint p = wDiscPoint ( 10 * 256 , a , tilt , 30 ) ;
        wDot ( c , p , 0xf3dfad , 950 , 0 ) ;
    }
}
static int32_t wOceanY ( int x , int z , int64_t t ) {
    return ( wWave ( x * 15 + z * 5 - t / 8 ) * 190 + wWave ( z * 23 - x * 7 + t / 11 ) * 95 ) / 1000 ;
}
/* Five explicit components: a long primary swell, crossing swell, two shorter
 * wind waves and a low-frequency modulation. Every sample uses the same time;
 * speed=0 freezes vertices AND crest highlights. Fixed-point throughout. */
static WPoint wOceanDetailPoint(const WCanvas *c,int x,int z,int64_t t) {
    const int32_t *d=c->detail->v;
    const int angle[5]={0,71,-39,127,19};
    const int weight[5]={1000,480,260,160,110};
    const int frequency[5]={1000,1340,2130,2710,630};
    const int rate[5]={1000,850,690,530,1280};
    int64_t yy=0,xx=0,zz=0;
    for(int k=0;k<5;k++){
        int32_t a=d[2]+angle[k]*256,sn=wSin(a),cs=wCos(a);
        int32_t amplitude=(int32_t)((int64_t)d[0]*weight[k]/2010);
        if(k) amplitude=(int32_t)((int64_t)amplitude*d[3]/480);
        int64_t distance=((int64_t)x*cs+(int64_t)z*sn)*256/1000;
        int64_t phase=distance*1024*frequency[k]/d[1]/1000-t*rate[k]/8000;
        int32_t si=wWave(phase),co=wWave(phase+256);
        yy+=(int64_t)si*amplitude/1000;
        xx+=(int64_t)co*amplitude*d[4]/1000*cs/1000000;
        zz+=(int64_t)co*amplitude*d[4]/1000*sn/1000000;
    }
    return wP(x*256+(int32_t)xx,(int32_t)yy,z*256+(int32_t)zz);
}
static void wOcean ( WCanvas * c ) {
    const int32_t * v = c -> config -> v ;
    int64_t t = ( int64_t ) ( c -> time % 3600000 ) * v [ NSW_FLOW ] / 1000 ;
    if(c->detail) t=t*c->detail->v[6]/1000;
    uint32_t teal = v [ NSW_ACCENT ] ? ( uint32_t ) v [ NSW_ACCENT ] : 0x79bcb8 ;
    for ( int z = 60 ; z > - 60 ; z -= 2 ) for ( int x = - 60 ; x < 60 ; x += 2 ) {
        int32_t y = wOceanY ( x , z , t ) ;
        WPoint a = wP ( x * 256 , y , z * 256 ) , b = wP ( ( x + 2 ) * 256 , wOceanY ( x + 2 , z , t ) , z * 256 ) , d = wP ( ( x + 2 ) * 256 , wOceanY ( x + 2 , z - 2 , t ) , ( z - 2 ) * 256 ) , e = wP ( x * 256 , wOceanY ( x , z - 2 , t ) , ( z - 2 ) * 256 ) ;
        if(c->detail){a=wOceanDetailPoint(c,x,z,t);b=wOceanDetailPoint(c,x+2,z,t);
            d=wOceanDetailPoint(c,x+2,z-2,t);e=wOceanDetailPoint(c,x,z-2,t);y=a.y;}
        int light = 150 + clampI ( ( int ) ( y + 200 ) , 0 , 400 ) ;
        uint32_t co = wMix ( 0x142c40 , teal , light ) ;
        wTriangle ( c , a , b , d , co , 1000 ) ;
        wTriangle ( c , a , d , e , wShade ( co , 850 ) , 1000 ) ;
        if ( y > 235 ) wLine ( c , a , b , 0xc5dbca , c->detail ? c->detail->v[5] : 800 ) ;
    }
    for ( int i = 0 ; i < 7 ; i ++ ) {
        int x = 25 + i * 2 , z = 15 + i ;
        wBox ( c , x * 256 , ( 7 + ( i % 3 ) * 3 ) * 256 , z * 256 , 3 * 256 , 12 * 256 , 4 * 256 , wMix ( 0x283345 , 0x8b8980 , i * 70 ) ) ;
    }
    /* A quiet standing sail gives waves a scale reference in space. */
    wLine ( c , wV ( - 12 , 0 , - 10 ) , wV ( - 12 , 21 , - 10 ) , 0xb7c7c2 , 1000 ) ;
    wTriangle ( c , wV ( - 12 , 20 , - 10 ) , wV ( - 12 , 3 , - 10 ) , wV ( - 3 , 3 , - 10 ) , 0xcfbfad , 1000 ) ;
    wTriangle ( c , wV ( - 13 , 15 , - 10 ) , wV ( - 13 , 3 , - 10 ) , wV ( - 20 , 3 , - 10 ) , 0x8199b2 , 1000 ) ;
    wBox ( c , - 12 * 256 , 128 , - 10 * 256 , 7 * 256 , 2 * 256 , 2 * 256 , 0x796c65 ) ;
}
NS_API uint32_t nsWorldVersion ( void ) {
    return 1 ;
}
NS_API uint32_t nsWorldConfigSize ( void ) {
    return ( uint32_t ) sizeof ( NsWorldConfig ) ;
}
NS_API void nsWorldDefaults ( NsWorldConfig * c ) {
    if ( ! c ) return ;
    for ( int i = 0 ; i < 24 ; i ++ ) c -> v [ i ] = WORLD_DEFAULT [ i ] ;
}
static int32_t wRender ( const NsWorldConfig * config , uint64_t timeMs , NsCell * out , uint32_t capacity , uint32_t * colors , int32_t * depth , uint32_t scratchCapacity, const NsWorldDetail *detail, const NsWorldTriangle *mesh, uint32_t meshCount, int isMesh ) {
    if ( ! config ) return - 1 ;
    const int32_t * v = config -> v ;
    int w = v [ 0 ] , h = v [ 1 ] ;
    if ( timeMs > 9007199254740991ULL ) return - 1 ;
    for ( int k = 0 ; k < 24 ; k ++ ) if ( v [ k ] < WORLD_MIN [ k ] || v [ k ] > WORLD_MAX [ k ] ) return - 1 ;
    uint32_t cells = ( uint32_t ) w * h ;
    int sx = v [ NSW_SAMPLING ] ? 2 : 1 , sy = v [ NSW_SAMPLING ] ? 4 : 2 ;
    uint32_t samples = cells * sx * sy ;
    if ( cells > capacity || samples > scratchCapacity || ( ! out && cells ) || ( ! colors && cells ) || ( ! depth && cells ) ) return - 1 ;
    if ( ! cells ) return 0 ;
    WCanvas c ;
    c . config = config ;
    c . detail = detail ;
    c . width = w * sx ;
    c . height = h * sy ;
    c . color = colors ;
    c . depth = depth ;
    c . sy = wSin ( v [ NSW_YAW ] ) ;
    c . cy = wCos ( v [ NSW_YAW ] ) ;
    c . sp = wSin ( v [ NSW_PITCH ] ) ;
    c . cp = wCos ( v [ NSW_PITCH ] ) ;
    c . sr = wSin ( v [ NSW_ROLL ] ) ;
    c . cr = wCos ( v [ NSW_ROLL ] ) ;
    c . focal = c . width * 8 * wCos ( v [ NSW_FOV ] / 2 ) / wSin ( v [ NSW_FOV ] / 2 ) ;
    c . time = timeMs ;
    c . points = 0 ;
    c . triangles = 0 ;
    for ( uint32_t i = 0 ; i < samples ; i ++ ) {
        colors [ i ] = ( uint32_t ) v [ NSW_BACKGROUND ] ;
        depth [ i ] = 0 ;
    }
    if(isMesh) {
        for(uint32_t k=0;k<meshCount;k++) {
            const int32_t *t=mesh[k].vertices;
            wTriangle(&c,wP(t[0],t[1],t[2]),wP(t[3],t[4],t[5]),wP(t[6],t[7],t[8]),mesh[k].color,1000);
        }
    } else switch ( v [ 2 ] ) {
        case 0 : wWaterfall ( & c ) ;
        break ;
        case 1 : wLandscape ( & c , 1 ) ;
        break ;
        case 2 : wAccretion ( & c ) ;
        break ;
        case 3 : wOcean ( & c ) ;
        break ;
        case 4 : wLandscape ( & c , 0 ) ;
        break ;
    }
    /* Hybrid raster: full interior cells keep two color samples. Silhouettes,
 * mist and high-contrast subcell detail use eight braille coverage bits. */
    for ( int y = 0 ; y < h ; y ++ ) for ( int x = 0 ; x < w ; x ++ ) {
        uint32_t i = ( uint32_t ) y * w + x ;
        if ( ! v [ NSW_SAMPLING ] ) {
            uint32_t a = ( uint32_t ) y * 2 * w + x , b = a + w ;
            out [ i ] . glyph = colors [ a ] == colors [ b ] ? 32 : 0x2580 ;
            out [ i ] . fg = colors [ a ] ;
            out [ i ] . bg = colors [ b ] ;
            out [ i ] . flags = ( depth [ a ] || depth [ b ] ) ? 1 : 0 ;
            continue ;
        }
        uint32_t col [ 8 ] , rs = 0 , gs = 0 , bs = 0 ;
        int occupied = 0 , low = 1000 , high = 0 ;
        uint8_t mask = 0 ;
        const uint8_t bits [ 8 ] = {
            1 , 8 , 2 , 16 , 4 , 32 , 64 , 128
        }
        ;
        for ( int k = 0 ; k < 8 ; k ++ ) {
            uint32_t at = ( uint32_t ) ( y * 4 + k / 2 ) * c . width + x * 2 + k % 2 ;
            col [ k ] = colors [ at ] ;
            int lum = redI ( col [ k ] ) + greenI ( col [ k ] ) + blueI ( col [ k ] ) ;
            if ( lum < low ) low = lum ;
            if ( lum > high ) high = lum ;
            if ( col [ k ] != ( uint32_t ) v [ NSW_BACKGROUND ] ) {
                occupied ++ ;
                mask |= bits [ k ] ;
                rs += redI ( col [ k ] ) ;
                gs += greenI ( col [ k ] ) ;
                bs += blueI ( col [ k ] ) ;
            }
        }
        out [ i ] . flags = occupied ? 1 : 0 ;
        if ( ! occupied ) {
            out [ i ] . glyph = 32 ;
            out [ i ] . fg = ( uint32_t ) v [ NSW_BACKGROUND ] ;
            out [ i ] . bg = ( uint32_t ) v [ NSW_BACKGROUND ] ;
            continue ;
        }
        if ( occupied < 8 ) {
            out [ i ] . glyph = 0x2800u + mask ;
            out [ i ] . fg = rgbI ( rs / occupied , gs / occupied , bs / occupied ) ;
            out [ i ] . bg = ( uint32_t ) v [ NSW_BACKGROUND ] ;
            continue ;
        }
        if ( high - low > 180 ) {
            int threshold = ( high + low ) / 2 , n = 0 ;
            uint32_t r0 = 0 , g0 = 0 , b0 = 0 , r1 = 0 , g1 = 0 , b1 = 0 ;
            mask = 0 ;
            for ( int k = 0 ; k < 8 ; k ++ ) {
                if ( redI ( col [ k ] ) + greenI ( col [ k ] ) + blueI ( col [ k ] ) > threshold ) {
                    n ++ ;
                    mask |= bits [ k ] ;
                    r1 += redI ( col [ k ] ) ;
                    g1 += greenI ( col [ k ] ) ;
                    b1 += blueI ( col [ k ] ) ;
                }
                else {
                    r0 += redI ( col [ k ] ) ;
                    g0 += greenI ( col [ k ] ) ;
                    b0 += blueI ( col [ k ] ) ;
                }
            }
            out [ i ] . glyph = 0x2800u + mask ;
            out [ i ] . fg = rgbI ( r1 / n , g1 / n , b1 / n ) ;
            out [ i ] . bg = rgbI ( r0 / ( 8 - n ) , g0 / ( 8 - n ) , b0 / ( 8 - n ) ) ;
            continue ;
        }
        uint32_t r0 = 0 , g0 = 0 , b0 = 0 , r1 = 0 , g1 = 0 , b1 = 0 ;
        for ( int k = 0 ; k < 4 ; k ++ ) {
            r0 += redI ( col [ k ] ) ;
            g0 += greenI ( col [ k ] ) ;
            b0 += blueI ( col [ k ] ) ;
            r1 += redI ( col [ k + 4 ] ) ;
            g1 += greenI ( col [ k + 4 ] ) ;
            b1 += blueI ( col [ k + 4 ] ) ;
        }
        out [ i ] . fg = rgbI ( r0 / 4 , g0 / 4 , b0 / 4 ) ;
        out [ i ] . bg = rgbI ( r1 / 4 , g1 / 4 , b1 / 4 ) ;
        out [ i ] . glyph = out [ i ] . fg == out [ i ] . bg ? 32 : 0x2580 ;
    }
    return ( int32_t ) cells ;
}

#include "world_detail_fields.inc"
NS_API uint32_t nsWorldExtensionVersion(void){return 1;}
NS_API void nsWorldDetailDefaults(NsWorldDetail *d){if(d)for(int i=0;i<8;i++)d->v[i]=WDETAIL_DEFAULT[i];}
NS_API int32_t nsWorldRender(const NsWorldConfig *c,uint64_t t,NsCell *o,uint32_t n,uint32_t *colors,int32_t *depth,uint32_t cap){return wRender(c,t,o,n,colors,depth,cap,0,0,0,0);}
NS_API int32_t nsWorldRenderDetailed(const NsWorldConfig *c,uint64_t t,const NsWorldDetail *d,NsCell *o,uint32_t n,uint32_t *colors,int32_t *depth,uint32_t cap){
    if(!d)return -1;
    for(int i=0;i<8;i++)if(d->v[i]<WDETAIL_MIN[i]||d->v[i]>WDETAIL_MAX[i])return -1;
    return wRender(c,t,o,n,colors,depth,cap,d,0,0,0);
}
NS_API int32_t nsWorldRenderMesh(const NsWorldConfig *c,uint64_t t,const NsWorldTriangle *mesh,uint32_t count,NsCell *o,uint32_t n,uint32_t *colors,int32_t *depth,uint32_t cap){
    if(count>NSW_MAX_TRIANGLES||(!mesh&&count))return -1;
    for(uint32_t i=0;i<count;i++){
        if(mesh[i].color>0xffffff)return -1;
        for(int k=0;k<9;k++)if(mesh[i].vertices[k]<-NSW_MESH_LIMIT||mesh[i].vertices[k]>NSW_MESH_LIMIT)return -1;
    }
    return wRender(c,t,o,n,colors,depth,cap,0,mesh,count,1);
}
