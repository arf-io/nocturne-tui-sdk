#ifndef NOCTURNE_WINDOW_SOURCE_MATH_H
#define NOCTURNE_WINDOW_SOURCE_MATH_H

/* Radian operations used by the original RC2 window equations. Keep these
 * separate from the ordinary renderer's intentionally interpolated sine table. */
/* Preserve the low part of pi when reflecting source geometry near pi.
 * Compensated summation avoids a three-ULP sine error that changes a half-way
 * RGB rounding decision in the original close-after-maximize composition. */
static inline double nrWindowSourceSinPrecise(double radians) {
    const double piLow=1.2246467991473532072e-16;
    double turns=nrFloor(radians/(2*NR_PI)+.5);
    radians=(radians-turns*(2*NR_PI))-turns*(2*piLow);
    if(radians>NR_PI/2)radians=(NR_PI-radians)+piLow;
    else if(radians< -NR_PI/2)radians=(-NR_PI-radians)-piLow;
    double square=radians*radians,term=radians,sum=radians,error=0;
    for(int i=1;i<=12;i++){
        term*=-square/((2*i)*(2*i+1));
        double add=term-error,next=sum+add;error=(next-sum)-add;sum=next;
    }
    return sum;
}
static inline double nrWindowSourceSin(double radians) {
    double tau=2*NR_PI;
    radians-=tau*nrFloor(radians/tau+.5);
    if(radians>NR_PI/2)radians=NR_PI-radians;
    else if(radians< -NR_PI/2)radians=-NR_PI-radians;
    double square=radians*radians,term=radians,sum=radians;
    for(int i=1;i<=12;i++){term*=-square/((2*i)*(2*i+1));sum+=term;}
    return sum;
}
static inline double nrWindowSourceCos(double radians) {
    double tau=2*NR_PI;
    radians-=tau*nrFloor(radians/tau+.5);
    double sign=1;
    if(radians>NR_PI/2){radians=NR_PI-radians;sign=-1;}
    else if(radians< -NR_PI/2){radians=-NR_PI-radians;sign=-1;}
    double square=radians*radians,term=1,sum=1;
    for(int i=1;i<=12;i++){term*=-square/((2*i-1)*(2*i));sum+=term;}
    return sign*sum;
}
#endif
