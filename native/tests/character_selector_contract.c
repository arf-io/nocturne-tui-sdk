#include "../src/internal.h"
/* Independent predicate oracles. Build/run this with the complete API gate. */
int nrTestCharacterSelector(void){
    static Json json;static CharacterSelector selector;
    const char*source="{\"role\":[\"component\"],\"state\":\"selected\",\"pathPrefix\":\"/app\",\"ids\":[7],\"indices\":[2],\"glyphs\":\"A日\",\"rect\":{\"x\":10,\"y\":20,\"width\":3,\"height\":2},\"inkOnly\":true}";
    if(!nrParse(&json,source,(int)strlen(source))||!nrCompileCharacterSelector(&json,0,&selector))return 1;
    if(!nrCharacterSelectorMatches(&selector,"control","selected","/app/task",7,2,'A',10,20))return 2;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/apple",7,2,'A',10,20))return 3;
    if(nrCharacterSelectorMatches(&selector,"control","inactive","/app/task",7,2,'A',10,20))return 4;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/app/task",8,2,'A',10,20))return 5;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/app/task",7,3,'A',10,20))return 6;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/app/task",7,2,'B',10,20))return 7;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/app/task",7,2,'A',13,20))return 8;
    if(nrCharacterSelectorMatches(&selector,"control","selected","/app/task",7,2,'A',10,22))return 9;
    memset(&selector,0,sizeof(selector));selector.inkOnly=1;
    if(nrCharacterSelectorMatches(&selector,"","","",0,0,0x2801,0,0))return 10;
    if(!nrCharacterSelectorMatches(&selector,"","","",0,0,0x65e5,0,0))return 11;
    selector.hasRect=1;selector.x=2147483647;selector.y=0;selector.width=2147483647;selector.height=1;
    if(!nrCharacterSelectorMatches(&selector,"","","",0,0,'A',2147483647,0))return 12;
    selector.hasIds=1;selector.idCount=0;
    if(nrCharacterSelectorMatches(&selector,"","","",0,0,'A',2147483647,0))return 13;
    const char*invalid[]={
        "{\"unknown\":true}","{\"inkOnly\":1}","{\"ids\":[-1]}",
        "{\"indices\":[0.5]}","{\"role\":[]}","{\"state\":true}",
        "{\"rect\":{\"x\":0,\"y\":0,\"width\":-1,\"height\":1}}",
        "{\"rect\":{\"x\":0,\"y\":0,\"width\":1}}"
    };
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++){
        if(!nrParse(&json,invalid[i],(int)strlen(invalid[i])))return 14;
        static CharacterSelector before;before=selector;
        if(nrCompileCharacterSelector(&json,0,&selector))return 15;
        if(memcmp(&before,&selector,sizeof(selector)))return 18;
    }
    static CharacterSelector before;before=selector;
    if(nrCompileCharacterSelector(NULL,0,&selector)||memcmp(&before,&selector,sizeof(selector)))return 19;
    if(nrCompileCharacterSelector(&json,0,NULL))return 20;
    const char*empty="{\"ids\":[],\"glyphs\":\"\"}";
    if(!nrParse(&json,empty,(int)strlen(empty))||!nrCompileCharacterSelector(&json,0,&selector))return 16;
    if(nrCharacterSelectorMatches(&selector,"","","",0,0,'A',0,0))return 17;
    return 0;
}
