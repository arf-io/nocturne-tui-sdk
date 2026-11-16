#include "internal.h"
/* Bounded exact rational conversion. Binary64 midpoints have at most 768
 * significant decimal digits. Retain 800 significant digits plus a sticky tail;
 * leading zeroes and decimal exponents adjust scale without growing scratch. */
#define WORDS 160
#define SIGNIFICANT_DIGITS 800
typedef struct {int count;uint32_t words[WORDS];} Big;
static void normalize(Big*a){while(a->count&&a->words[a->count-1]==0)a->count--;}
static int multiply(Big*a,unsigned factor,unsigned add){
    uint64_t carry=add;
    for(int i=0;i<a->count;i++){uint64_t value=(uint64_t)a->words[i]*factor+carry;a->words[i]=(uint32_t)value;carry=value>>32;}
    if(carry){if(a->count>=WORDS)return 0;a->words[a->count++]=(uint32_t)carry;}return 1;
}
static int shift(const Big*a,int bits,Big*out){
    if(bits<0)return 0;memset(out,0,sizeof(*out));if(!a->count)return 1;
    int word=bits/32,part=bits%32;if(a->count+word+(part!=0)>WORDS)return 0;
    for(int i=0;i<a->count;i++){uint64_t value=(uint64_t)a->words[i]<<part;
        out->words[i+word]|=(uint32_t)value;if(part)out->words[i+word+1]|=(uint32_t)(value>>32);}
    out->count=a->count+word+(part!=0);normalize(out);return 1;
}
static int compare(const Big*a,const Big*b){
    if(a->count!=b->count)return a->count>b->count?1:-1;
    for(int i=a->count-1;i>=0;i--)if(a->words[i]!=b->words[i])return a->words[i]>b->words[i]?1:-1;
    return 0;
}
static void subtract(Big*a,const Big*b){
    uint64_t borrow=0;
    for(int i=0;i<a->count;i++){uint64_t right=(i<b->count?(uint64_t)b->words[i]:0)+borrow,left=a->words[i];
        a->words[i]=(uint32_t)(left-right);borrow=left<right;}
    normalize(a);
}
static int bitLength(const Big*a){
    if(!a->count)return 0;uint32_t top=a->words[a->count-1];int bits=0;
    while(top){bits++;top>>=1;}return (a->count-1)*32+bits;
}
int nrDecimalNumber(const char*text,int length,double*out){
    if(!text||!out||length<1)return 0;
    Big numerator={0},denominator={.count=1,.words={1}},scaled,divisor,temp;
    int pos=0,negative=0,fraction=0,sticky=0,significant=0,discarded=0;
    if(text[pos]=='-'){negative=1;pos++;}
    int integers=0;
    while(pos<length&&text[pos]>='0'&&text[pos]<='9'){
        unsigned digit=(unsigned)(text[pos++]-'0');integers++;
        if(!significant&&!digit)continue;
        if(significant<SIGNIFICANT_DIGITS){if(!multiply(&numerator,10,digit))return 0;significant++;}
        else{discarded++;if(digit)sticky=1;}
    }
    if(!integers)return 0;
    if(pos<length&&text[pos]=='.'){
        pos++;int digits=0;
        while(pos<length&&text[pos]>='0'&&text[pos]<='9'){
            unsigned digit=(unsigned)(text[pos++]-'0');digits++;fraction++;
            if(!significant&&!digit)continue;
            if(significant<SIGNIFICANT_DIGITS){if(!multiply(&numerator,10,digit))return 0;significant++;}
            else{discarded++;if(digit)sticky=1;}
        }
        if(!digits)return 0;
    }
    int exponent=0,exponentNegative=0;
    if(pos<length&&(text[pos]=='e'||text[pos]=='E')){
        pos++;if(pos<length&&(text[pos]=='-'||text[pos]=='+'))exponentNegative=text[pos++]=='-';
        int digits=0;
        while(pos<length&&text[pos]>='0'&&text[pos]<='9'){
            digits++;int digit=text[pos++]-'0';if(exponent<1000000){exponent=exponent*10+digit;if(exponent>1000000)exponent=1000000;}
        }
        if(!digits)return 0;
    }
    if(pos!=length)return 0;
    uint64_t sign=negative?0x8000000000000000ull:0;
    if(!fraction&&!exponent&&!discarded&&numerator.count<=2){
        uint64_t integer=numerator.count?numerator.words[0]:0;
        if(numerator.count==2)integer|=(uint64_t)numerator.words[1]<<32;
        if(integer<=9007199254740992ull){double value=(double)integer;*out=negative?-value:value;return 1;}
    }
    if(!numerator.count){memcpy(out,&sign,sizeof(sign));return 1;}
    int decimalPower=(exponentNegative?-exponent:exponent)-fraction+discarded;
    int order=decimalPower+significant-1;
    if(order>100)return 0;
    if(order < -400){memcpy(out,&sign,sizeof(sign));return 1;}
    for(int k=0;k<(decimalPower<0?-decimalPower:decimalPower);k++)if(!multiply(decimalPower<0?&denominator:&numerator,10,0))return 0;
    int power=bitLength(&numerator)-bitLength(&denominator);
    if(power>=0){if(!shift(&denominator,power,&temp))return 0;if(compare(&numerator,&temp)<0)power--;}
    else{if(!shift(&numerator,-power,&temp))return 0;if(compare(&temp,&denominator)<0)power--;}
    if(power < -1075){memcpy(out,&sign,sizeof(sign));return 1;}
    int scale=power < -1022?1074:52-power;
    if(scale>=0){if(!shift(&numerator,scale,&scaled))return 0;divisor=denominator;}
    else{scaled=numerator;if(!shift(&denominator,-scale,&divisor))return 0;}
    uint64_t mantissa=0;
    for(int bit=52;bit>=0;bit--){
        if(!shift(&divisor,bit,&temp))return 0;
        if(compare(&scaled,&temp)>=0){subtract(&scaled,&temp);mantissa|=1ull<<bit;}
    }
    if(!shift(&scaled,1,&temp))return 0;
    int rounding=compare(&temp,&divisor);
    if(rounding>0||(rounding==0&&(sticky||(mantissa&1))))mantissa++;
    uint64_t bits;
    if(power < -1022)bits=mantissa;
    else{
        if(mantissa==(1ull<<53)){mantissa>>=1;power++;}
        if(power>1023)return 0;
        bits=((uint64_t)(power+1023)<<52)|(mantissa-(1ull<<52));
    }
    bits|=sign;double value;memcpy(&value,&bits,sizeof(value));
    if(!(value>=-1e100&&value<=1e100))return 0;
    *out=value;return 1;
}
/* Exact finite decimal spelling of the binary value, rather than a fixed
 * precision display formatter. At most 1077 bytes including sign and point. */
int nrJsonNumber(double value,char*out,int cap){
    if(!out||cap<2||!(value>=-1e100&&value<=1e100))return -1;
    uint64_t bits;memcpy(&bits,&value,sizeof(bits));int negative=(int)(bits>>63),exponent=(int)((bits>>52)&2047);
    uint64_t mantissa=bits&0xfffffffffffffull;
    if(exponent)mantissa|=1ull<<52;
    if(!mantissa){const char*zero=negative?"-0.0":"0";int length=negative?4:1;if(cap<=length)return -1;memcpy(out,zero,(size_t)length+1);return length;}
    int power=exponent?exponent-1023-52:-1074;
    uint8_t digits[1200]={0};int count=0;
    while(mantissa){digits[count++]=(uint8_t)(mantissa%10);mantissa/=10;}
    int iterations=power<0?-power:power,factor=power<0?5:2;
    for(int k=0;k<iterations;k++){
        unsigned carry=0;
        for(int i=0;i<count;i++){unsigned next=digits[i]*(unsigned)factor+carry;digits[i]=(uint8_t)(next%10);carry=next/10;}
        while(carry){if(count>=1200)return -1;digits[count++]=(uint8_t)(carry%10);carry/=10;}
    }
    int fraction=power<0?-power:0;
    while(fraction&&count>1&&digits[0]==0){memmove(digits,digits+1,(size_t)--count);fraction--;}
    int size=negative+(fraction>=count?2+fraction:count+(fraction>0));
    if(size>=cap)return -1;
    int at=0;if(negative)out[at++]='-';
    if(fraction>=count){out[at++]='0';out[at++]='.';for(int k=0;k<fraction-count;k++)out[at++]='0';}
    for(int i=count-1;i>=0;i--){out[at++]=(char)('0'+digits[i]);if(fraction>0&&fraction<count&&i==fraction)out[at++]='.';}
    out[at]=0;return at;
}
