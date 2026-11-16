
/** Optional WebGPU projection benchmark. Never blocks the immediate-input path.
 * It includes host upload/readback costs; it is not the default renderer. */
export class ProjectionProbe {
    constructor() {
        this.device = null;
        this.pipeline = null;
        this.busy = false;
    }
    /** Initialize explicitly after a user action. False means an ordinary CPU fallback. */
    async initialize(gpu) {
        if (!gpu?.requestAdapter)
            return false;
        const adapter = await gpu.requestAdapter();
        if (!adapter)
            return false;
        this.device = await adapter.requestDevice();
        this.pipeline = this.device.createComputePipeline({ layout: 'auto', compute: { module: this.device.createShaderModule({ code: `
struct Points { values: array<vec4<f32>> }; @group(0) @binding(0) var<storage,read> positions:Points;
@group(0) @binding(1) var<storage,read_write> projected:Points;
@compute @workgroup_size(64) fn main(@builtin(global_invocation_id) id:vec3<u32>) {
 let i=id.x; if(i>=arrayLength(&positions.values)){return;} let p=positions.values[i];
 let z=max(0.01,p.z); projected.values[i]=vec4<f32>(p.x/z,p.y/z,z,1.0);
}` }), entryPoint: 'main' } });
        return true;
    }
    /** Benchmark normalized projection of camera-relative XYZ/W vectors. This probe
     * measures transfer overhead; full scene acceleration requires a separate design.
     * One outstanding request only. Caller owns input and output arrays. */
    async project(points) {
        if (!this.device || !this.pipeline)
            throw Error('GPU not initialized');
        if (this.busy)
            throw Error('GPU request already in flight');
        if (points.length % 4 || points.length < 4 || points.length > 400000)
            throw RangeError('1..100000 vec4 points');
        this.busy = true;
        let input, output, readback;
        try {
            input = this.device.createBuffer({ size: points.byteLength, usage: 128 | 8 });
            output = this.device.createBuffer({ size: points.byteLength, usage: 128 | 4 });
            readback = this.device.createBuffer({ size: points.byteLength, usage: 1 | 8 });
            this.device.queue.writeBuffer(input, 0, points);
            const bind = this.device.createBindGroup({ layout: this.pipeline.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: input } }, { binding: 1, resource: { buffer: output } }] }), encoder = this.device.createCommandEncoder(), pass = encoder.beginComputePass();
            pass.setPipeline(this.pipeline);
            pass.setBindGroup(0, bind);
            pass.dispatchWorkgroups(Math.ceil(points.length / 4 / 64));
            pass.end();
            encoder.copyBufferToBuffer(output, 0, readback, 0, points.byteLength);
            this.device.queue.submit([encoder.finish()]);
            await readback.mapAsync(1);
            const result = new Float32Array(readback.getMappedRange().slice(0));
            readback.unmap();
            return result;
        }
        finally {
            input?.destroy();
            output?.destroy();
            readback?.destroy();
            this.busy = false;
        }
    }
    dispose() { this.device?.destroy(); this.device = null; this.pipeline = null; }
}

