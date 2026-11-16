import type {NativeScene,NativeMetadata} from '../../bindings/typescript/native_scene.mjs';
export function recover(scene:NativeScene):NativeMetadata {
    const full=scene.infoComplete(16*1024*1024);
    const instant:number=full.clock.timeUs;
    const fov:number=full.camera.fov;
    const orthographic:boolean=full.camera.orthographic;
    void [instant,fov,orthographic];
    const abi:number=full.contract.abiVersion;
    const schema:number=full.contract.snapshotSchema;
    const profile:'nocturne.metadata/v1'=full.contract.metadataProfile;
    const features:string[]=full.contract.features;
    void [abi,schema,profile,features];
    // @ts-expect-error ABI version is numeric
    const textualABI:string=full.contract.abiVersion;
    void textualABI;
    for(const window of full.windows){
        const duration:number=window.durationUs;
        const position:readonly [number,number,number]=window.position;
        void [duration,position];
        // @ts-expect-error projected visibility is numeric
        const visible:boolean=window.visible;
        void visible;
    }
    for(const area of full.areas){
        const layout:'ordered'|'queue'|'direct'=area.layout;
        const hidden:boolean=area.hideEmpty;
        void [layout,hidden];
        // @ts-expect-error queue layout is named rather than numeric
        const index:number=area.layout;
        void index;
    }
    for(const widget of full.widgets){
        const width:number=widget.width;
        const enabled:boolean=widget.enabled;
        const series:number[]=widget.data;
        const sampling:'inherit'|'cell'|'half'|'braille'|'hybrid'=widget.plot.sampling;
        void [width,enabled,series,sampling];
        // @ts-expect-error source dimensions are numeric
        const textWidth:string=widget.width;
        // @ts-expect-error authored enabled state is a boolean
        const numericEnabled:number=widget.enabled;
        void [textWidth,numericEnabled];
    }
    // @ts-expect-error textual limits are not accepted
    scene.infoComplete('large');
    return full;
}
