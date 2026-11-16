
/* @(#)s_sin.c 1.3 95/01/18 */
/*
 * ====================================================
 * Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
 *
 * Developed at SunSoft, a Sun Microsystems, Inc. business.
 * Permission to use, copy, modify, and distribute this
 * software is freely granted, provided that this notice 
 * is preserved.
 * ====================================================
 */

/* nrOriginalSin(x)
 * Return sine function of x.
 *
 * kernel function:
 *	nrOriginalKernelSin		... sine function on [-pi/4,pi/4]
 *	nrOriginalKernelCos		... cose function on [-pi/4,pi/4]
 *	nrOriginalRemPi2	... argument reduction routine
 *
 * Method.
 *      Let S,C and T denote the nrOriginalSin, nrOriginalCos and nrOriginalTan respectively on 
 *	[-PI/4, +PI/4]. Reduce the argument x to y1+y2 = x-k*pi/2 
 *	in [-pi/4 , +pi/4], and let n = k mod 4.
 *	We have
 *
 *          n        nrOriginalSin(x)      nrOriginalCos(x)        nrOriginalTan(x)
 *     ----------------------------------------------------------
 *	    0	       S	   C		 T
 *	    1	       C	  -S		-1/T
 *	    2	      -S	  -C		 T
 *	    3	      -C	   S		-1/T
 *     ----------------------------------------------------------
 *
 * Special cases:
 *      Let trig be any of nrOriginalSin, nrOriginalCos, or nrOriginalTan.
 *      trig(+-INF)  is NaN, with signals;
 *      trig(NaN)    is that NaN;
 *
 * Accuracy:
 *	TRIG(x) returns trig(x) nearly rounded 
 */

#include "original_math.h"

#ifdef __STDC__
	double nrOriginalSin(double x)
#else
	double nrOriginalSin(x)
	double x;
#endif
{
	double y[2],z=0.0;
	int n, ix;

    /* High word of x. */
	ix = nrOriginalHI(x);

    /* |x| ~< pi/4 */
	ix &= 0x7fffffff;
	if(ix <= 0x3fe921fb) return nrOriginalKernelSin(x,z,0);

    /* nrOriginalSin(Inf or NaN) is NaN */
	else if (ix>=0x7ff00000) return x-x;

    /* argument reduction needed */
	else {
	    n = nrOriginalRemPi2(x,y);
	    switch(n&3) {
		case 0: return  nrOriginalKernelSin(y[0],y[1],1);
		case 1: return  nrOriginalKernelCos(y[0],y[1]);
		case 2: return -nrOriginalKernelSin(y[0],y[1],1);
		default:
			return -nrOriginalKernelCos(y[0],y[1]);
	    }
	}
}
