// Independent normalized text alpha equations; no native helpers involved.
export function textCurveReference(name,p){
 switch(name){
 case 'linear':return p;
 case 'ease-in':return p*p;
 case 'ease-out':return 2*p-p*p;
 case 'smooth':return 3*p*p-2*p**3;
 case 'smoother':return 6*p**5-15*p**4+10*p**3;
 case 'sine':return p===.5?.5:(1-Math.cos(Math.PI*p))/2;
 case 'step':return Number(p>=1);
 case 'cubic':return p<.5?4*p**3:1-4*(1-p)**3;
 case 'back':return 1+2.5*(p-1)**3+1.5*(p-1)**2;
 case 'bounce':if(p<4/11)return 121/16*p*p;
  if(p<8/11)return 121/16*(p-6/11)**2+.75;
  if(p<10/11)return 121/16*(p-9/11)**2+.9375;
  return 121/16*(p-21/22)**2+.984375;
 default:throw Error('Unknown text curve '+name);
 }
}
