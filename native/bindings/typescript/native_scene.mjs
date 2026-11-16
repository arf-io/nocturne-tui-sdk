const encoder = new TextEncoder(), decoder = new TextDecoder();
class NativeScene {
    exports;
    context;
    input;
    checkpoint;
    particleBuffer;
    snapshotSize;
    inputCapacity=1048576;
    modalAllocation=0;
    modalAllocationSize=0;
    modelAllocation=0;
    modelAllocationSize=0;
    promptAllocation=0;
    promptAllocationSize=0;
    renderAllocation=0;
    renderAllocationSize=0;
    constructor(exports, seed) {
        this.exports = exports;
        const size = exports.nrContextSize();
        this.context = exports.nrAlloc(size);
        this.input = exports.nrAlloc(1048576);
        this.snapshotSize = exports.nrSnapshotSize();
        this.checkpoint = exports.nrAlloc(this.snapshotSize);
        this.particleBuffer = exports.nrAlloc(48);
        if (!this.context || !this.input || !this.checkpoint || !this.particleBuffer || exports.nrInit(this.context, size, seed) !== 0)
            throw Error('Native context allocation failed');
    }
    /** Instantiate the exact native core. bytes are caller-loaded, never fetched. */
    static async create(bytes, seed = 2030) {
        if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff)
            throw RangeError('seed: uint32 required');
        const module = await WebAssembly.compile(bytes);
        const imports = WebAssembly.Module.imports(module);
        if (imports.length)
            throw Error('This runtime must have no WASM imports');
        const instance = await WebAssembly.instantiate(module, {});
        return new NativeScene(instance.exports, seed);
    }
    sourceStageOklch(lightness,chroma,hue) {
        if(!this.exports||![lightness,chroma,hue].every(Number.isInteger)||lightness<0||lightness>1000||chroma<0||chroma>4000||hue< -2147483648||hue>2147483647)throw RangeError('Original source color domain');
        return this.exports.nrSourceStageOklch(lightness,chroma,hue)>>>0;
    }
    sourceStageTween(from,to,elapsedMs,durationMs,easing=1) {
        const values=[from,to,durationMs,easing],bounds=[[-2147483648,2147483647],[-2147483648,2147483647],[0,4294967295],[0,3]];
        if(!this.exports||values.some((v,i)=>!Number.isSafeInteger(v)||v<bounds[i][0]||v>bounds[i][1])||!Number.isSafeInteger(elapsedMs)||elapsedMs<0)throw RangeError('Source Stage tween bounds');
        return this.exports.nrSourceStageTween(from,to,BigInt(elapsedMs),durationMs,easing);
    }
    sourceStageInkOpacity(ageMs,fadeMs,rowQ8,bandQ8,topMinimum) {
        const values=[ageMs,fadeMs,rowQ8,bandQ8,topMinimum],bounds=[[0,4294967295],[0,4294967295],[-2147483648,2147483647],[0,2147483647],[0,1000]];
        if(!this.exports||values.some((v,i)=>!Number.isSafeInteger(v)||v<bounds[i][0]||v>bounds[i][1]))throw RangeError('Source Stage opacity bounds');
        return this.exports.nrSourceStageInkOpacity(...values);
    }
    sourceStageHit(x,y) {
        if(!this.exports||[x,y].some(v=>!Number.isInteger(v)||v< -4096||v>4096))throw RangeError('Source Stage hit coordinates');
        const result=this.exports.nrSourceStageHit(this.context,x,y,this.checkpoint,2);
        if(result<0)throw RangeError('Source Stage hit rejected');
        if(!result)return null;const row=new Int32Array(this.exports.memory.buffer,this.checkpoint,2);return {id:row[0],item:row[1]};
    }
    string(pointer) {
        const data = new Uint8Array(this.exports.memory.buffer);
        let end = pointer;
        while (end < data.length && data[end] !== 0)
            end++;
        if (end >= data.length)
            throw Error('Unterminated native string');
        return decoder.decode(data.subarray(pointer, end));
    }
    /** Returns 1 when a bounded simulation batch has more catch-up work. */
    ensureRenderMemory() {
        const required=this.exports.nrRenderMemorySize(this.context);
        if(required<=this.exports.nrRenderMemoryCapacity(this.context))return;
        if(required>0xffffffffn)throw RangeError('Viewport exceeds WASM address space');
        const size=Number(required),pointer=this.renderAllocation?
            (this.exports.nrGrowLast(this.renderAllocation,this.renderAllocationSize,size)||this.exports.nrAlloc(size)):this.exports.nrAlloc(size);
        if(!pointer)throw Error('Viewport memory allocation failed');
        if(this.exports.nrSetRenderMemory(this.context,pointer,required))throw Error('Viewport render memory rejected');
        this.renderAllocation=pointer;this.renderAllocationSize=size;
    }
    ensurePromptMemory() {
        if(typeof this.exports.nrPromptMemorySize!=='function')throw Error('Core lacks dynamic prompt storage');
        const required=this.exports.nrPromptMemorySize(this.context),current=this.exports.nrPromptMemoryCapacity(this.context);
        if(required<=current)throw Error('Prompt storage request made no progress');
        if(required>0xffffffffn)throw RangeError('Prompt exceeds WASM address space');
        const size=Number(required),pointer=this.exports.nrAlloc(size);
        if(!pointer)throw Error('Prompt memory allocation failed');
        if(this.exports.nrSetPromptMemory(this.context,pointer,required))throw Error('Prompt storage rejected');
        this.promptAllocation=pointer;this.promptAllocationSize=size;
    }
    ensureModelMemory() {
        if(typeof this.exports.nrModelMemorySize!=='function')throw Error('Core lacks model storage');
        const required=this.exports.nrModelMemorySize(this.context),current=this.exports.nrModelMemoryCapacity(this.context);
        if(required<=current)throw Error('Model storage request made no progress');
        if(required>0xffffffffn)throw RangeError('Model exceeds WASM address space');
        const size=Number(required),pointer=this.exports.nrAlloc(size);
        if(!pointer)throw Error('Model memory allocation failed');
        if(this.exports.nrSetModelMemory(this.context,pointer,required))throw Error('Model storage rejected');
        this.modelAllocation=pointer;this.modelAllocationSize=size;
    }
    /** Atomic direct resource upload, separate from JSON transactions. */
    ensureModalMemory() {
        if(typeof this.exports.nrModalMemorySize!=='function')throw Error('Core lacks modal storage');
        const required=this.exports.nrModalMemorySize(this.context),current=this.exports.nrModalMemoryCapacity(this.context);
        if(required<=current)throw Error('Modal storage request made no progress');
        if(required>0xffffffffn)throw RangeError('Modal exceeds WASM address space');
        const size=Number(required),pointer=this.exports.nrAlloc(size);
        if(!pointer)throw Error('Modal memory allocation failed');
        if(this.exports.nrSetModalMemory(this.context,pointer,required))throw Error('Modal storage rejected');
        this.modalAllocation=pointer;this.modalAllocationSize=size;
    }
    /** Atomic direct resource upload, separate from JSON transactions. */
    setModelRecords(bytes) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!(bytes instanceof Uint8Array)||bytes.length%40||bytes.length>0xffffffff)throw RangeError('Model record length');
        if(typeof this.exports.nrModelSet!=='function')throw Error('Core lacks model storage');
        // Own the source before memory.grow can detach a caller's WASM view.
        bytes=bytes.slice();this.ensureInput(bytes.length);
        new Uint8Array(this.exports.memory.buffer,this.input,bytes.length).set(bytes);
        let code=this.exports.nrModelSet(this.context,this.input,bytes.length/40);
        while(code<0&&this.string(this.exports.nrError(this.context))==='Model storage required'){this.ensureModelMemory();code=this.exports.nrModelSet(this.context,this.input,bytes.length/40);}
        if(code)throw RangeError(this.string(this.exports.nrError(this.context)));
    }
    /** Owned canonical nine-Q8-coordinate/RGB records. */
    modelRecords() {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof this.exports.nrModelTriangleCount!=='function')throw Error('Core lacks model storage');
        const count=this.exports.nrModelTriangleCount(this.context);this.ensureCheckpoint(count*40);
        if(this.exports.nrModelCopy(this.context,this.checkpoint,count)!==count)throw Error('Model copy rejected');
        return new Uint8Array(this.exports.memory.buffer,this.checkpoint,count*40).slice();
    }
    ensureInput(size) {
        if(size<=this.inputCapacity)return;
        if(size>0x7fffffff)throw RangeError('Command exceeds native addressable length');
        const pointer=this.exports.nrGrowLast(this.input,this.inputCapacity,size)||this.exports.nrAlloc(size);
        if(!pointer)throw Error('Command memory allocation failed');this.input=pointer;this.inputCapacity=size;
    }
    ensureCheckpoint(size) {
        if(size<=this.snapshotSize)return;
        if(size>0xffffffff)throw RangeError('Output exceeds WASM address space');
        const pointer=this.exports.nrGrowLast(this.checkpoint,this.snapshotSize,size)||this.exports.nrAlloc(size);
        if(!pointer)throw Error('Output memory allocation failed');this.checkpoint=pointer;this.snapshotSize=size;
    }
    scalarString(pointer,count) {
        const values=new Uint32Array(this.exports.memory.buffer,pointer,count),parts=[];
        for(let i=0;i<count;i+=4096)parts.push(String.fromCodePoint(...values.subarray(i,Math.min(i+4096,count))));
        return parts.join('');
    }
    command(command) {if(!this.exports)throw Error('NativeScene is closed');
        const text = JSON.stringify(command, (_key, value) => { if (typeof value === 'number' && !Number.isFinite(value))
            throw RangeError('Nonfinite number'); return value; });
        const bytes = encoder.encode(text);
        this.ensureInput(bytes.length);
        new Uint8Array(this.exports.memory.buffer, this.input, bytes.length).set(bytes);
        let code = this.exports.nrCommand(this.context, this.input, bytes.length);
        while(code<0&&['Prompt storage required','Modal storage required'].includes(this.string(this.exports.nrError(this.context)))) {if(this.string(this.exports.nrError(this.context))==='Modal storage required')this.ensureModalMemory();else this.ensurePromptMemory();code=this.exports.nrCommand(this.context,this.input,bytes.length);}
        if(code<0&&this.string(this.exports.nrError(this.context))==='Viewport render memory required') {
            this.ensureRenderMemory();code=this.exports.nrCommand(this.context,this.input,bytes.length);
        }
        if (code < 0)
            throw RangeError(this.string(this.exports.nrError(this.context)));
        return code;
    }
    /** Synchronous convenience catch-up. Real hosts may yield between command batches. */
    advanceTo(timeUs) {if(!this.exports)throw Error('NativeScene is closed'); if (!Number.isSafeInteger(timeUs))
        throw RangeError('Integer microseconds required'); while (this.command({ op: 'time', timeUs }) === 1) { } }
    render() {if(!this.exports)throw Error('NativeScene is closed');
        this.ensureRenderMemory();
        const n = this.exports.nrRender(this.context);
        if (!n)
            throw Error('Native render failed');
        const ptr = this.exports.nrCells(this.context), bytes = new Uint8Array(this.exports.memory.buffer, ptr, n * 16).slice();
        return { width: this.exports.nrWidth(this.context), height: this.exports.nrHeight(this.context), bytes, cells: new Uint32Array(bytes.buffer) };
    }
    info() {if(!this.exports)throw Error('NativeScene is closed'); return JSON.parse(this.string(this.exports.nrInfo(this.context))); }
    /** Complete recovery; optional caller byte limit. Never call every animation frame. */
    infoComplete(maxBytes = null) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(maxBytes!==null&&(!Number.isInteger(maxBytes)||maxBytes<1||maxBytes>0xffffffff))throw RangeError('Metadata recovery limit');
        if(typeof this.exports.nrInfoPage!=='function')throw Error('Native core lacks nrInfoPage');
        let offset=0,total=0,checksum=0,crc=0xffffffff,data=null;
        const crc4=[0x00000000,0x1db71064,0x3b6e20c8,0x26d930ac,
          0x76dc4190,0x6b6b51f4,0x4db26158,0x5005713c,
          0xedb88320,0xf00f9344,0xd6d6a3e8,0xcb61b38c,
          0x9b64c2b0,0x86d3d2d4,0xa00ae278,0xbdbdf21c];
        // Synchronous ownership: no event-loop yield or user callback between pages.
        for(;;) {
            const status=this.exports.nrInfoPage(this.context,offset,this.input,65536,this.particleBuffer,4);
            if(status!==0&&status!==1)throw Error('Metadata page rejected');
            const [size,written,next,token]=new Uint32Array(this.exports.memory.buffer,this.particleBuffer,4);
            if(maxBytes!==null&&size>maxBytes)throw RangeError('Complete metadata exceeds recovery limit');
            if(size<offset||written!==Math.min(65536,size-offset)||next!==offset+written||status!==Number(next<size))throw Error('Invalid metadata page progress');
            if(data===null){total=size;checksum=token;data=new Uint8Array(size);}
            else if(total!==size||checksum!==token)throw Error('Metadata changed during recovery');
            const chunk=new Uint8Array(this.exports.memory.buffer,this.input,written);
            data.set(chunk,offset);
            for(const byte of chunk){let q=crc^byte;q=(q>>>4)^crc4[q&15];crc=(q>>>4)^crc4[q&15];}
            offset=next;if(status===0)break;
        }
        if(offset!==total||((crc^0xffffffff)>>>0)!==checksum)throw Error('Metadata recovery checksum mismatch');
        return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));
    }
    snapshot() {
        if(!this.exports)throw Error('NativeScene is closed');
        const size=typeof this.exports.nrSnapshotSizeFor==='function'?this.exports.nrSnapshotSizeFor(this.context):this.exports.nrSnapshotSize();
        if(!size)throw Error('Snapshot size exceeds addressable range');this.ensureCheckpoint(size);
        if(this.exports.nrSave(this.context,this.checkpoint,size))throw Error('Snapshot failed');
        return new Uint8Array(this.exports.memory.buffer,this.checkpoint,size).slice();
    }
    restore(bytes) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!(bytes instanceof Uint8Array)||bytes.length<24||bytes.length>0xffffffff||new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength).getUint32(16,true)!==bytes.length-24)throw RangeError('Snapshot size');
        this.ensureCheckpoint(bytes.length);new Uint8Array(this.exports.memory.buffer,this.checkpoint,bytes.length).set(bytes);
        let code=this.exports.nrLoad(this.context,this.checkpoint,bytes.length);
        while(code<0){const error=this.string(this.exports.nrError(this.context));if(error==='Prompt storage required')this.ensurePromptMemory();else if(error==='Model storage required')this.ensureModelMemory();else if(error==='Modal storage required')this.ensureModalMemory();else break;code=this.exports.nrLoad(this.context,this.checkpoint,bytes.length);}
        if(code)throw RangeError('Snapshot rejected atomically');
    }
    particles() {if(!this.exports)throw Error('NativeScene is closed'); const result = []; for (let i = 0; i < 2048; i++)
        if (this.exports.nrParticle(this.context, i, this.particleBuffer, 12) > 0)
            result.push(Array.from(new Int32Array(this.exports.memory.buffer, this.particleBuffer, 12))); return result; }
    bidiLines(text,ends,direction=2) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string'||!Array.isArray(ends)||ends.length>2048||![0,1,2].includes(direction))throw RangeError('Explicit bidi lines');
        const values=Array.from(text,c=>c.codePointAt(0));if(values.length>2048||ends.some(end=>!Number.isInteger(end)||end<=0||end>values.length))throw RangeError('Line boundary');
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const linePointer=this.input+values.length*4;new Uint32Array(this.exports.memory.buffer,linePointer,ends.length).set(ends);
        const count=this.exports.nrBidiClusterLines(this.input,values.length,linePointer,ends.length,direction,this.checkpoint,values.length);
        if(count<0)throw RangeError('Invalid grapheme or hard-break line boundary');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,count*7),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(words.subarray(i*7,i*7+7)));return rows;
    }
    scriptRuns(text) {
        if(!this.exports)throw Error('NativeScene is closed');if(typeof text!=='string')throw TypeError('Unicode string required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Script capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrScriptRuns(this.input,values.length,this.checkpoint,values.length);if(count<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,count*3),rows=[];
        for(let i=0;i<count;i++){const tag=words[3*i+2];rows.push([words[3*i],words[3*i+1],String.fromCharCode(tag>>>24,(tag>>>16)&255,(tag>>>8)&255,tag&255)]);}return rows;
    }
    lineBreaks(text) {if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Line-break capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrLineBreaks(this.input,values.length,this.checkpoint,values.length+1);
        if(count<0)throw RangeError('Invalid Unicode scalar');
        return Array.from(new Uint32Array(this.exports.memory.buffer,this.checkpoint,count));
    }
    lineBreakDetails(text) {if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Line-break capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrLineBreakDetails(this.input,values.length,this.checkpoint,values.length+1);
        if(count<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,count*2),rows=[];
        for(let i=0;i<count;i++)rows.push([words[2*i],words[2*i+1]]);return rows;
    }
    graphemeBoundaries(text) {if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Grapheme capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrGraphemeBreaks(this.input,values.length,this.checkpoint,values.length+1);
        if(count<0)throw RangeError('Invalid Unicode scalar');
        return Array.from(new Uint32Array(this.exports.memory.buffer,this.checkpoint,count));
    }
    graphemeWidths(text,ambiguous=1) {if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(ambiguous!==1&&ambiguous!==2)throw RangeError('Ambiguous width must be 1 or 2');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Grapheme capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrGraphemeWidths(this.input,values.length,ambiguous,this.checkpoint,values.length);
        if(count<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,count*3),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(words.subarray(i*3,i*3+3)));return rows;
    }
    graphemeLayout(text,columns,ambiguous=1) {if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(ambiguous!==1&&ambiguous!==2)throw RangeError('Ambiguous width must be 1 or 2');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff)throw RangeError('Positive uint32 columns required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Grapheme capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const count=this.exports.nrGraphemeLayout(this.input,values.length,ambiguous,columns,this.checkpoint,values.length);
        if(count<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,count*5),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(words.subarray(i*5,i*5+5)));return rows;
    }
    negotiateShortcuts(actions,candidates,host) {
        if(!this.exports)throw Error('NativeScene is closed');
        const words=(rows,width,max)=>{
            if(!Array.isArray(rows)||rows.length>max)throw RangeError('Shortcut table capacity');
            const flat=[];for(let row of rows){if(width===1)row=[row];
                if(!Array.isArray(row)||row.length!==width||row.some(v=>!Number.isInteger(v)||v<0||v>0xffffffff))throw RangeError('Shortcut uint32 rows required');flat.push(...row);
            }return flat;
        };
        const a=words(actions,1,64),c=words(candidates,3,256),h=words(host,3,256);
        new Uint32Array(this.exports.memory.buffer,this.input,a.length+c.length+h.length).set([...a,...c,...h]);
        const n=this.exports.nrNegotiateShortcuts(this.input,actions.length,this.input+a.length*4,candidates.length,this.input+(a.length+c.length)*4,host.length,this.checkpoint,actions.length);
        if(n<0)throw RangeError('Invalid shortcut capabilities/preferences');
        const data=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*4),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(data.subarray(i*4,i*4+4)));return rows;
    }
    textRunClusters(kind,id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(kind)||kind<0||kind>3||!Number.isInteger(id)||id<0||id>65535)throw RangeError('Invalid text run key');
        const n=this.exports.nrTextRunClusters(this.context,kind,id,0,0);
        if(n<0)throw RangeError('Missing or invalid text run');this.ensureCheckpoint(n*16);
        if(this.exports.nrTextRunClusters(this.context,kind,id,this.checkpoint,n)!==n)throw Error('Text source changed during read');
        if(n<0)throw RangeError('Missing or invalid text run');
        const data=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*4),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(data.subarray(i*4,i*4+4)));return rows;
    }
    textRunSource(kind,id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(kind)||kind<0||kind>3||!Number.isInteger(id)||id<0||id>65535)throw RangeError('Invalid text run key');
        const n=this.exports.nrTextRunSource(this.context,kind,id,0,0);
        if(n<0)throw RangeError('Missing or invalid text run');
        if(!Number.isSafeInteger(n))throw RangeError('Invalid text source length');
        if(n===0)return '';this.ensureCheckpoint(n*4);
        const written=this.exports.nrTextRunSource(this.context,kind,id,this.checkpoint,n);
        if(written!==n)throw Error('Text source changed during read');
        return this.scalarString(this.checkpoint,n);
    }
    textRunLayout(kind,id,columns,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(kind)||kind<0||kind>3||!Number.isInteger(id)||id<0||id>65535)throw RangeError('Invalid text run key');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        const n=this.exports.nrTextRunLayout(this.context,kind,id,ambiguous,columns,0,0);
        if(n<0)throw RangeError('Missing or invalid text run');this.ensureCheckpoint(n*28);
        if(this.exports.nrTextRunLayout(this.context,kind,id,ambiguous,columns,this.checkpoint,n)!==n)throw Error('Text source changed during read');
        if(n<0)throw RangeError('Missing or invalid text run');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*7),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(words.subarray(i*7,i*7+7)));return rows;
    }
    textRunHit(kind,id,columns,column,row,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(kind)||kind<0||kind>3||!Number.isInteger(id)||id<0||id>65535)throw RangeError('Invalid text run key');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        if(![column,row].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff))throw RangeError('Uint32 pointer coordinates required');
        const n=this.exports.nrTextRunHit(this.context,kind,id,ambiguous,columns,column,row);
        if(n<0)throw RangeError('Missing or invalid text run');return n;
    }
    textRunClip(kind,id,columns,x,y,width,height,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(kind)||kind<0||kind>3||!Number.isInteger(id)||id<0||id>65535)throw RangeError('Invalid text run key');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        if(![x,y,width,height].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff))throw RangeError('Uint32 viewport required');
        const n=this.exports.nrTextRunClip(this.context,kind,id,ambiguous,columns,x,y,width,height,0,0);
        if(n<0)throw RangeError('Missing or invalid text run');this.ensureCheckpoint(n*36);
        if(this.exports.nrTextRunClip(this.context,kind,id,ambiguous,columns,x,y,width,height,this.checkpoint,n)!==n)throw Error('Text source changed during read');
        if(n<0)throw RangeError('Missing or invalid text run');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*9),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(words.subarray(i*9,i*9+9)));return rows;
    }
    surfaceFoam(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id required');
        const count=this.exports.nrSurfaceFoam(this.context,id,this.checkpoint,256);
        if(count<0)throw RangeError('Invalid surface foam query');
        const data=new Float64Array(this.exports.memory.buffer,this.checkpoint,count*5),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(data.subarray(i*5,i*5+5)));return rows;
    }
    hullImmersion(vertices,faces,height) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Array.isArray(vertices)||vertices.length<4||vertices.length>128||!vertices.every(row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite))||!Array.isArray(faces)||faces.length<4||faces.length>256||!faces.every(row=>Array.isArray(row)&&row.length===3&&row.every(x=>Number.isInteger(x)&&x>=0&&x<vertices.length))||!Number.isFinite(height))throw RangeError('Invalid hull input');
        // Reserved command scratch is aligned and large enough for both arrays.
        const facePointer=this.input+vertices.length*24;
        new Float64Array(this.exports.memory.buffer,this.input,vertices.length*3).set(vertices.flat());
        new Uint32Array(this.exports.memory.buffer,facePointer,faces.length*3).set(faces.flat());
        if(this.exports.nrHullImmersion(this.input,vertices.length,facePointer,faces.length,height,this.particleBuffer,5)!==1)throw RangeError('Invalid convex hull');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,5));
    }
    angularDragExchange(bodyInertia,waterInertia,conductance,seconds,bodyOmega,waterOmega) {
        if(!this.exports)throw Error('NativeScene is closed');
        const rows=[bodyInertia,waterInertia,conductance,bodyOmega,waterOmega];
        if(!Number.isFinite(seconds)||!rows.every(row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite)))throw RangeError('Invalid angular exchange input');
        new Float64Array(this.exports.memory.buffer,this.input,15).set(rows.flat());
        if(this.exports.nrAngularDragExchange(this.input,this.input+24,this.input+48,seconds,this.input+72,this.input+96,this.checkpoint,10)!==1)throw RangeError('Invalid finite-inertia angular exchange');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,10));
    }
    fluidDragExchange(bodyMass,waterMass,conductance,seconds,bodyVelocity,waterVelocity) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(![bodyMass,waterMass,conductance,seconds].every(Number.isFinite)||![bodyVelocity,waterVelocity].every(row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite)))throw RangeError('Invalid finite-mass drag parameters');
        new Float64Array(this.exports.memory.buffer,this.input,6).set([...bodyVelocity,...waterVelocity]);
        if(this.exports.nrFluidDragExchange(bodyMass,waterMass,conductance,seconds,this.input,this.input+24,this.checkpoint,10)!==1)throw RangeError('Invalid finite-mass drag parameters');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,10));
    }
    hullImmersionPlane(vertices,faces,point,normal) {
        return this._hullPlaneQuery(vertices,faces,point,normal);
    }
    hullBuoyancyPlane(vertices,faces,point,normal,{density,gravity,mass,centerOfMass}) {
        return this._hullPlaneQuery(vertices,faces,point,normal,{density,gravity,mass,centerOfMass});
    }
    _hullPlaneQuery(vertices,faces,point,normal,wrench) {
        if(!this.exports)throw Error('NativeScene is closed');
        const vector=row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite);
        if(!Array.isArray(vertices)||vertices.length<4||vertices.length>128||!vertices.every(vector)||!Array.isArray(faces)||faces.length<4||faces.length>256||!faces.every(row=>Array.isArray(row)&&row.length===3&&row.every(index=>Number.isInteger(index)&&index>=0&&index<vertices.length))||!vector(point)||!vector(normal))throw RangeError('Invalid hull plane input');
        if(wrench&&(![wrench.density,wrench.gravity,wrench.mass].every(Number.isFinite)||!vector(wrench.centerOfMass)))throw RangeError('Invalid buoyancy input');
        const facePointer=this.input+vertices.length*24,pointPointer=Math.ceil((facePointer+faces.length*12)/8)*8,normalPointer=pointPointer+24,centerPointer=normalPointer+24;
        new Float64Array(this.exports.memory.buffer,this.input,vertices.length*3).set(vertices.flat());
        new Uint32Array(this.exports.memory.buffer,facePointer,faces.length*3).set(faces.flat());
        new Float64Array(this.exports.memory.buffer,pointPointer,3).set(point);new Float64Array(this.exports.memory.buffer,normalPointer,3).set(normal);
        let result,words=5;
        if(wrench){words=11;new Float64Array(this.exports.memory.buffer,centerPointer,3).set(wrench.centerOfMass);result=this.exports.nrHullBuoyancyPlane(this.input,vertices.length,facePointer,faces.length,pointPointer,normalPointer,wrench.density,wrench.gravity,wrench.mass,centerPointer,this.checkpoint,words);}
        else result=this.exports.nrHullImmersionPlane(this.input,vertices.length,facePointer,faces.length,pointPointer,normalPointer,this.checkpoint,words);
        if(result!==1)throw RangeError('Invalid convex hull or plane parameters');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,words));
    }
    hullMeshImmersion(vertices,faces,water) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Array.isArray(vertices)||vertices.length<4||vertices.length>128||!vertices.every(row=>Array.isArray(row)&&row.length===3&&row.every(Number.isFinite))||!Array.isArray(faces)||faces.length<4||faces.length>256||!faces.every(row=>Array.isArray(row)&&row.length===3&&row.every(x=>Number.isInteger(x)&&x>=0&&x<vertices.length))||!Array.isArray(water)||water.length<1||water.length>256||!water.every(row=>Array.isArray(row)&&row.length===9&&row.every(Number.isFinite)))throw RangeError('Invalid hull/surface input');
        const facePointer=this.input+vertices.length*24,waterPointer=Math.ceil((facePointer+faces.length*12)/8)*8;
        new Float64Array(this.exports.memory.buffer,this.input,vertices.length*3).set(vertices.flat());
        new Uint32Array(this.exports.memory.buffer,facePointer,faces.length*3).set(faces.flat());
        new Float64Array(this.exports.memory.buffer,waterPointer,water.length*9).set(water.flat());
        if(this.exports.nrHullMeshImmersion(this.input,vertices.length,facePointer,faces.length,waterPointer,water.length,this.particleBuffer,5)!==1)throw RangeError('Invalid hull/surface mesh');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,5));
    }
    surfaceFluidAngular(id) {
        if(!this.exports)throw Error('NativeScene is closed');if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id');
        const result=this.exports.nrSurfaceFluidAngular(this.context,id,this.checkpoint,12);
        if(result<0)throw RangeError('Invalid angular fluid query');return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,12)):null;
    }
    surfaceFluid(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id required');
        const result=this.exports.nrSurfaceFluid(this.context,id,this.checkpoint,15);
        if(result<0)throw RangeError('Invalid finite water query');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,15)):null;
    }
    floatHull(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535)throw RangeError('Float body id required');
        const result=this.exports.nrFloatHull(this.context,id,this.checkpoint,14);
        if(result<0)throw RangeError('Invalid hull query');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,14)):null;
    }
    promptLayout() {
        if(!this.exports)throw Error("NativeScene is closed");
        const n=this.exports.nrPromptLayout(this.context,0,0);if(n<0)throw RangeError("Invalid prompt layout");if(!n)return [];
        this.ensureCheckpoint(n*8*8);if(this.exports.nrPromptLayout(this.context,this.checkpoint,n)!==n)throw RangeError("Invalid prompt layout");
        const rows=Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,n*8));return Array.from({length:n},(_,i)=>rows.slice(i*8,i*8+8));
    }
    promptVisualLayout() {
        if(!this.exports)throw Error("NativeScene is closed");
        const n=this.exports.nrPromptVisualLayout(this.context,0,0);if(n<0)throw RangeError("Invalid prompt layout");if(!n)return [];
        this.ensureCheckpoint(n*10*8);if(this.exports.nrPromptVisualLayout(this.context,this.checkpoint,n)!==n)throw RangeError("Invalid prompt layout");
        const rows=Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,n*10));return Array.from({length:n},(_,i)=>rows.slice(i*10,i*10+10));
    }
    areaGeometry(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535)throw RangeError('Area id required');
        const result=this.exports.nrAreaGeometry(this.context,id,this.checkpoint,12);
        if(result<0)throw RangeError('Invalid area geometry');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,12)):null;
    }
    fieldSample(id,x,y) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>=0xffffffff||!Number.isFinite(x)||!Number.isFinite(y))throw RangeError('Field id and finite screen coordinates required');
        const result=this.exports.nrFieldSample(this.context,id,x,y,this.checkpoint,4);
        if(result<0)throw RangeError('Invalid field sample');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,4)):null;
    }
    waterSample(index) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(index)||index<0||index>=256)throw RangeError('Triangle index required');
        const result=this.exports.nrWaterSample(this.context,index,this.checkpoint,8);
        if(result<0)throw RangeError('Invalid water sample');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,8)):null;
    }
    thermalSample(index) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(index)||index<0||index>=256)throw RangeError('Triangle index required');
        const result=this.exports.nrThermalSample(this.context,index,this.checkpoint,10);
        if(result<0)throw RangeError('Invalid thermal sample');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,10)):null;
    }
    surfaceFoamTransport(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id required');
        const count=this.exports.nrSurfaceFoamTransport(this.context,id,this.checkpoint,256);
        if(count<0)throw RangeError('Invalid surface foam query');
        const data=new Float64Array(this.exports.memory.buffer,this.checkpoint,count*7),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(data.subarray(i*7,i*7+7)));return rows;
    }
    flowThickness(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id required');
        const result=this.exports.nrFlowThickness(this.context,id,this.checkpoint,6);
        if(result<0)throw RangeError('Invalid flow thickness query');
        return result?Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,6)):null;
    }
    surfaceTriangles(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16)throw RangeError('Surface id required');
        const count=this.exports.nrSurfaceTriangles(this.context,id,this.checkpoint,256);
        if(count<0)throw RangeError('Invalid surface geometry query');
        const data=new Float64Array(this.exports.memory.buffer,this.checkpoint,count*12),rows=[];
        for(let i=0;i<count;i++)rows.push(Array.from(data.subarray(i*12,i*12+12)));return rows;
    }
    floatBody(id) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535)throw RangeError('Float body id required');
        const result=this.exports.nrFloatBody(this.context,id,this.checkpoint,12);
        if(result<0)throw RangeError('Invalid float body query');
        return result===0?null:Array.from(new Float64Array(this.exports.memory.buffer,this.checkpoint,12));
    }
    surfaceWaveSample(id,x,z) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>16||typeof x!=='number'||typeof z!=='number')throw RangeError('Surface id and numeric coordinates required');
        if(this.exports.nrSurfaceWaveSample(this.context,id,x,z,this.particleBuffer,6)!==1)throw RangeError('Invalid surface wave sample');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,6));
    }
    pathSample(points,distance,{closed=false,mode='clamp'}={}) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Array.isArray(points)||points.length<2||points.length>129||points.some(row=>!Array.isArray(row)||row.length!==3||row.some(v=>typeof v!=='number'))||typeof distance!=='number'||typeof closed!=='boolean'||!['clamp','loop','reverse'].includes(mode))throw RangeError('Invalid path shape or mode');
        new Float64Array(this.exports.memory.buffer,this.input,points.length*3).set(points.flat());
        if(this.exports.nrPathSample(this.input,points.length,Number(closed),['clamp','loop','reverse'].indexOf(mode),distance,this.particleBuffer,8)!==1)throw RangeError('Invalid path parameters');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,8));
    }
    waveSample(waves,x,z,seconds) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(!Array.isArray(waves)||waves.length>32||waves.some(row=>!Array.isArray(row)||row.length!==5||row.some(v=>typeof v!=='number')))throw RangeError('At most 32 five-value waves required');
        if(![x,z,seconds].every(v=>typeof v==='number'))throw TypeError('Numeric coordinates and seconds required');
        const values=waves.flat();new Float64Array(this.exports.memory.buffer,this.input,values.length).set(values);
        if(this.exports.nrWaveSample(this.input,waves.length,x,z,seconds,this.particleBuffer,6)!==1)throw RangeError('Invalid wave field');
        return Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,6));
    }
    bidiVisual(text,direction=0) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(!Number.isInteger(direction)||direction<0||direction>2)throw RangeError('Invalid bidi direction');
        const values=Array.from(text,c=>c.codePointAt(0));if(values.length>2048)throw RangeError('Bidi capacity');
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const n=this.exports.nrBidiVisual(this.input,values.length,direction,this.checkpoint,2048);
        if(n<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*4),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(words.subarray(i*4,i*4+4)));return rows;
    }
    documentLayout(text,columns,direction=2,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(!Number.isInteger(direction)||direction<0||direction>2)throw RangeError('Invalid bidi direction');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        const values=Array.from(text,c=>c.codePointAt(0)),count=values.length;
        if(count>0x7fffffff)throw RangeError('Native scalar addressability');
        const outputWords=Math.max(1,count)*7,scratchWords=40*(count+1);
        this.ensureInput(Math.max(4,count*4));this.ensureCheckpoint((outputWords+scratchWords)*4);
        new Uint32Array(this.exports.memory.buffer,this.input,count).set(values);
        const n=this.exports.nrDocumentBidiClusterLayout(this.input,count,ambiguous,columns,direction,this.checkpoint,count,this.checkpoint+outputWords*4,BigInt(scratchWords));
        if(n<0)throw RangeError('Invalid Unicode scalar or document layout');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*7),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(words.subarray(i*7,i*7+7)));return rows;
    }
    documentBoundaries(text) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        const values=Array.from(text,c=>c.codePointAt(0)),count=values.length;
        if(count>0x7fffffff)throw RangeError('Native scalar addressability');
        this.ensureInput(Math.max(4,count*4));this.ensureCheckpoint((count+1)*4);
        new Uint32Array(this.exports.memory.buffer,this.input,count).set(values);
        const n=this.exports.nrGraphemeBreaks(this.input,count,this.checkpoint,count+1);
        if(n<0)throw RangeError('Invalid Unicode scalar');
        return Array.from(new Uint32Array(this.exports.memory.buffer,this.checkpoint,n));
    }
    _documentEdge(scalars,value,end) {
        const newline=[10,11,12,13,0x85,0x2028,0x2029].includes(scalars[value[0]]);
        return [newline?(end?0:value[2]):value[2]+((value[5]&1?!end:end)?value[4]:0),value[3]+Number(!!(end&&newline)),value[5]];
    }
    documentHit(text,columns,column,row,direction=2,ambiguous=1) {
        if(![column,row].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff))throw RangeError('Uint32 coordinates required');
        const rows=this.documentLayout(text,columns,direction,ambiguous),scalars=Array.from(text,c=>c.codePointAt(0));let selected=0,dy=Infinity,dx=Infinity;
        for(const value of rows)for(const end of [0,1]){const e=this._documentEdge(scalars,value,end),y=Math.abs(e[1]-row),x=Math.abs(e[0]-column),at=value[end];if(y<dy||y===dy&&(x<dx||x===dx&&at>selected)){selected=at;dy=y;dx=x;}}
        return selected;
    }
    documentCaret(text,columns,offset,affinity=1,direction=2,ambiguous=1) {
        const rows=this.documentLayout(text,columns,direction,ambiguous),scalars=Array.from(text,c=>c.codePointAt(0));
        if(!Number.isInteger(offset)||offset<0||offset>scalars.length||(affinity!==0&&affinity!==1)||!this.documentBoundaries(text).includes(offset))throw RangeError('Invalid caret offset or affinity');
        let chosen=[0,0,Number(direction===1)],found=false;
        for(const value of rows)for(const end of [0,1])if(value[end]===offset){chosen=this._documentEdge(scalars,value,end);found=true;if(end===Number(affinity===0))return chosen;}
        if(rows.length&&!found)throw RangeError('Invalid Unicode or caret boundary');return chosen;
    }
    bidiLayout(text,columns,direction=2,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(!Number.isInteger(direction)||direction<0||direction>2)throw RangeError('Invalid bidi direction');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        const values=Array.from(text,c=>c.codePointAt(0));if(values.length>2048)throw RangeError('Bidi capacity');
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const n=this.exports.nrBidiClusterLayout(this.input,values.length,ambiguous,columns,direction,this.checkpoint,2048);
        if(n<0)throw RangeError('Invalid Unicode scalar');
        const words=new Uint32Array(this.exports.memory.buffer,this.checkpoint,n*7),rows=[];
        for(let i=0;i<n;i++)rows.push(Array.from(words.subarray(i*7,i*7+7)));return rows;
    }
    _bidiMappingInput(text,columns,direction,ambiguous) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(!Number.isInteger(direction)||direction<0||direction>2)throw RangeError('Invalid bidi direction');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff||(ambiguous!==1&&ambiguous!==2))throw RangeError('Invalid text layout policy');
        const values=Array.from(text,c=>c.codePointAt(0));if(values.length>2048)throw RangeError('Bidi capacity');
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);return values.length;
    }
    bidiHit(text,columns,column,row,direction=2,ambiguous=1) {
        const count=this._bidiMappingInput(text,columns,direction,ambiguous);
        if(![column,row].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff))throw RangeError('Uint32 coordinates required');
        const n=this.exports.nrBidiClusterHit(this.input,count,ambiguous,columns,direction,column,row);
        if(n<0)throw RangeError('Invalid Unicode scalar');return n;
    }
    bidiCaret(text,columns,offset,affinity=1,direction=2,ambiguous=1) {
        const count=this._bidiMappingInput(text,columns,direction,ambiguous);
        if(!Number.isInteger(offset)||offset<0||offset>count||(affinity!==0&&affinity!==1))throw RangeError('Invalid caret offset or affinity');
        if(this.exports.nrBidiCaret(this.input,count,ambiguous,columns,direction,offset,affinity,this.checkpoint,3)<0)throw RangeError('Invalid Unicode or caret boundary');
        return Array.from(new Uint32Array(this.exports.memory.buffer,this.checkpoint,3));
    }
    selectedText() {
        if(!this.exports)throw Error('NativeScene is closed');
        const count=this.exports.nrPromptSelection(this.context,0,0);
        if(count<0)throw Error('Invalid selection export');this.ensureCheckpoint(count*4);
        if(this.exports.nrPromptSelection(this.context,this.checkpoint,count)!==count)throw Error('Selection changed during read');
        if(count<0)throw Error('Invalid selection export');
        if(!count)return null;
        return this.scalarString(this.checkpoint,count);
    }
    graphemeHit(text,columns,column,row,ambiguous=1) {
        if(!this.exports)throw Error('NativeScene is closed');
        if(typeof text!=='string')throw TypeError('Unicode string required');
        if(ambiguous!==1&&ambiguous!==2)throw RangeError('Ambiguous width must be 1 or 2');
        if(!Number.isInteger(columns)||columns<1||columns>0xffffffff)throw RangeError('Positive uint32 columns required');
        if(![column,row].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff))throw RangeError('Uint32 pointer coordinates required');
        const values=[];for(const c of text){if(values.length===2048)throw RangeError('Grapheme capacity');values.push(c.codePointAt(0));}
        new Uint32Array(this.exports.memory.buffer,this.input,values.length).set(values);
        const result=this.exports.nrGraphemeHit(this.input,values.length,ambiguous,columns,column,row);
        if(result<0)throw RangeError('Invalid Unicode scalar');return result;
    }
    particleMotions() {if(!this.exports)throw Error('NativeScene is closed');const result=[];for(let i=0;i<2048;i++)if(this.exports.nrParticleMotion(this.context,i,this.particleBuffer,6)>0){const values=Array.from(new Float64Array(this.exports.memory.buffer,this.particleBuffer,6));this.exports.nrParticle(this.context,i,this.particleBuffer,12);const id=new Uint32Array(this.exports.memory.buffer,this.particleBuffer,12)[0];result.push([id,...values]);}return result;}
    catalogue() {if(!this.exports)throw Error('NativeScene is closed'); return JSON.parse(this.string(this.exports.nrCatalogue())); }
    oklch(l, c, h) {if(!this.exports)throw Error('NativeScene is closed'); if (![l, c, h].every(Number.isFinite))
        throw RangeError('Nonfinite color'); const round = (x) => x < 0 ? -Math.round(-x) : Math.round(x); const color = this.exports.nrOklch(round(l * 1e6), round(c * 1e6), round(h * 1000)) >>> 0; if (color === 0xffffffff)
        throw RangeError('Color bounds'); return color; }
    textSample(id,index) {if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535||!Number.isInteger(index)||index<0||index>=2048)throw RangeError('Text sample bounds');
        if(this.exports.nrTextSample(this.context,id,index,this.particleBuffer,8))throw RangeError('Text run or index not found');
        const values=Array.from(new Int32Array(this.exports.memory.buffer,this.particleBuffer,8));values[2]>>>=0;return values;
    }
    textClusterSample(id,index) {if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535||!Number.isInteger(index)||index<0||index>=2048)throw RangeError('Text cluster bounds');
        if(this.exports.nrTextClusterSample(this.context,id,index,this.particleBuffer,8))throw RangeError('Text cluster not found');
        const values=Array.from(new Int32Array(this.exports.memory.buffer,this.particleBuffer,8));values[0]>>>=0;return values;
    }
    textTrailSample(id,index,trailIndex) {if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535||!Number.isInteger(index)||index<0||index>=2048||!Number.isInteger(trailIndex)||trailIndex<0||trailIndex>=8)throw RangeError('Text trail bounds');
        if(this.exports.nrTextTrailSample(this.context,id,index,trailIndex,this.particleBuffer,8))throw RangeError('Text trail not found');
        const values=Array.from(new Int32Array(this.exports.memory.buffer,this.particleBuffer,8));values[0]>>>=0;return values;
    }
    windowSample(id,u,v,visibility) {if(!this.exports)throw Error('NativeScene is closed');
        if(!Number.isInteger(id)||id<1||id>65535||[u,v,visibility].some(x=>!Number.isFinite(x)||x<0||x>1))throw RangeError('Window sample bounds');
        if(this.exports.nrWindowSample(this.context,id,Math.round(u*1e6),Math.round(v*1e6),Math.round(visibility*1e6),this.particleBuffer,5))throw RangeError('Window not found');
        return Array.from(new Int32Array(this.exports.memory.buffer,this.particleBuffer,5));
    }
    batch(commands) {return this.command({op:'batch',commands});}
    schedule(id,atUs,command) {return this.command({op:'schedule',id,atUs,command});}
    cancelScheduled(id) {return this.command({op:'cancel-schedule',id});}
    /** Release the per-scene WebAssembly instance. Already copied frames remain valid. */
    close() {this.exports=null;this.context=0;}
    /** Copy semantic metadata from the latest render; never render implicitly. */
    inspectCharacterCell(x,y) {
        if(!this.exports)throw Error('NativeScene is closed');
        if([x,y].some(v=>!Number.isInteger(v)||v< -2147483648||v>2147483647))throw RangeError('Cell coordinates');
        const status=this.exports.nrInspectCharacterCell(this.context,x,y,this.input,408);
        if(status===-2)throw Error('Render required before cell inspection');
        if(status!==0)throw RangeError('Cell inspection rejected');
        const words=new Uint32Array(this.exports.memory.buffer,this.input,5);
        return {glyph:words[0],foreground:words[1],background:words[2],id:words[3],index:words[4],role:this.string(this.input+20),state:this.string(this.input+149),path:this.string(this.input+278)};
    }
    /** Pure composition: 0 sRGB, 1 linear sRGB, 2 OKLab, 3 OKLCh. */
    compositeInSpace(base,source,space,baseAlpha=65535,sourceAlpha=65535,blend=0,operation=0,seed=0) {
        if(!this.exports)throw Error('NativeScene is closed');
        const values=[base,source,baseAlpha,sourceAlpha,blend,operation,seed,space];
        const bounds=[0xffffff,0xffffff,65535,65535,27,12,0xffffffff,3];
        if(values.some((v,i)=>!Number.isInteger(v)||v<0||v>bounds[i]))throw RangeError('Composition input range');
        if(this.exports.nrCompositeInSpace(...values,this.particleBuffer)<0)throw RangeError('Composition rejected');
        const out=new Uint32Array(this.exports.memory.buffer,this.particleBuffer,2);return {rgb:out[0],alpha:out[1]};
    }
    /** Pure encoded-RGB blend and independent alpha composition; no state mutation. */
    composite(base, source, baseAlpha = 65535, sourceAlpha = 65535, blend = 0, operation = 0, seed = 0) {if(!this.exports)throw Error('NativeScene is closed');
        const values = [base, source, baseAlpha, sourceAlpha, blend, operation, seed];
        const bounds = [0xffffff, 0xffffff, 65535, 65535, 27, 12, 0xffffffff];
        if (values.some((v, i) => !Number.isInteger(v) || v < 0 || v > bounds[i]))
            throw RangeError('Composition input range');
        if (this.exports.nrComposite(...values, this.particleBuffer) < 0)
            throw RangeError('Composition rejected');
        const out = new Uint32Array(this.exports.memory.buffer, this.particleBuffer, 2);
        return { rgb: out[0], alpha: out[1] };
    }
}


export { NativeScene };
