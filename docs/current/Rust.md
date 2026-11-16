# Rust reference

The `nocturne_native` crate in `native/bindings/rust` owns context, payload and presentation buffers around the C ABI. Use a path dependency for a local SDK. The shared project exporter writes Cargo.toml and a complete main.rs with that dependency.

## Scene lifecycle

```rust
use nocturne_native::NativeScene;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut scene = NativeScene::new(2030)?;
    scene.command(r#"{"op":"draft","text":"Ready","caret":5}"#)?;
    scene.advanceTo(500_000)?;
    let frame = scene.render()?;
    let checkpoint = scene.snapshot()?;
    scene.restore(&checkpoint)?;
    println!("{} bytes", frame.bytes.len());
    Ok(())
}
```

Commands take UTF-8 JSON and return a pending-work boolean on success. Propagate Result errors. Frames and snapshots are owned. `infoComplete` returns complete JSON text; parsing into an application DTO belongs to the host.

The Ratatui host maps native cells to terminal buffer updates and owns raw mode, alternate screen, mouse and paste. Restore terminal settings on failure. The final executable needs a runtime search path for the native library. A linker argument set by a dependency does not provide one.

## Runtime contract

Commands are native transactions. Rejection preserves authoritative state; catch-up pending means more work remains. Serialize operations on one scene. The binding returns copied frames, snapshots and complete metadata. Supply integer microseconds; rendering does not advance time.

The binding grows prompt, model, modal and render storage. Resource IDs and bounded emitter/window/node pools retain their declared native domains; those are separate from document length. Keep the core and binding from a compatible SDK. Use complete metadata when source exceeds ordinary readback capacity.

![Progress component](images/widget-progress-default.png)

## Public method index

The shipped binding declares the following methods. Geometry, text and resource query names correspond to the [C declarations](C.md).

- `new(seed:u32)->Result<Self,String>`
- `command(&mut self,json:&str)->Result<bool,String>`
- `advanceTo(&mut self,timeUs:u64)->Result<(),String>`
- `render(&mut self)->Result<Frame,String>`
- `inspectCharacterCell(&mut self,x:i32,y:i32)->Result<CharacterCellInfo,String>`
- `info(&mut self)->String`
- `infoComplete(&mut self)->Result<String,String>`
- `catalogue(&self)->String`
- `snapshot(&self)->Result<Vec<u8>,String>`
- `restore(&mut self,bytes:&[u8])->Result<(),String>`
- `script_runs(&self,text:&str)->Result<Vec<ScriptRun>,String>`
- `bidi_lines(&self,text:&str,ends:&[u32],direction:u32)->Result<Vec<[u32;7]>,String>`
- `line_breaks(&self,text:&str)->Result<Vec<u32>,String>`
- `line_break_details(&self,text:&str)->Result<Vec<[u32;2]>,String>`
- `grapheme_boundaries(&self,text:&str)->Result<Vec<u32>,String>`
- `grapheme_widths(&self,text:&str,ambiguous:u32)->Result<Vec<[u32;3]>,String>`
- `grapheme_layout(&self,text:&str,columns:u32,ambiguous:u32)->Result<Vec<[u32;5]>,String>`
- `text_run_clusters(&self,kind:u32,id:u32)->Result<Vec<[u32;4]>,String>`
- `text_run_source(&self,kind:u32,id:u32)->Result<String,String>`
- `text_run_layout(&self,kind:u32,id:u32,columns:u32,ambiguous:u32)->Result<Vec<[u32;7]>,String>`
- `text_run_hit(&self,kind:u32,id:u32,columns:u32,column:u32,row:u32,ambiguous:u32)->Result<u32,String>`
- `text_run_clip(&self,kind:u32,id:u32,columns:u32,x:u32,y:u32,width:u32,height:u32,ambiguous:u32)->Result<Vec<[u32;9]>,String>`
- `surface_foam(&self,id:u32)->Result<Vec<[f64;5]>,String>`
- `angular_drag_exchange(&self,body_inertia:[f64;3],water_inertia:[f64;3],conductance:[f64;3],seconds:f64,body_omega:[f64;3],water_omega:[f64;3])->Result<[f64;10],String>`
- `fluid_drag_exchange(&self,body_mass:f64,water_mass:f64,conductance:f64,seconds:f64,body_velocity:[f64;3],water_velocity:[f64;3])->Result<[f64;10],String>`
- `hull_immersion_plane(&self,vertices:&[[f64;3]],faces:&[[u32;3]],point:[f64;3],normal:[f64;3])->Result<[f64;5],String>`
- `hull_buoyancy_plane(&self,vertices:&[[f64;3]],faces:&[[u32;3]],point:[f64;3],normal:[f64;3],density:f64,gravity:f64,mass:f64,center_of_mass:[f64;3])->Result<[f64;11],String>`
- `hull_immersion(&self,vertices:&[[f64;3]],faces:&[[u32;3]],height:f64)->Result<[f64;5],String>`
- `hull_mesh_immersion(&self,vertices:&[[f64;3]],faces:&[[u32;3]],water:&[[f64;9]])->Result<[f64;5],String>`
- `surface_fluid_angular(&self,id:u32)->Result<Option<[f64;12]>,String>`
- `surface_fluid(&self,id:u32)->Result<Option<[f64;15]>,String>`
- `float_hull(&self,id:u32)->Result<Option<[f64;14]>,String>`
- `prompt_layout(&self)->Result<Vec<[f64;8]>,String>`
- `prompt_visual_layout(&self)->Result<Vec<[f64;10]>,String>`
- `source_stage_tween(&self,from:i32,to:i32,elapsed:u64,duration:u32,easing:i32)->Result<i32,String>`
- `source_stage_ink_opacity(&self,age:u32,fade:u32,row:i32,band:i32,minimum:i32)->Result<i32,String>`
- `source_stage_hit(&self,x:i32,y:i32)->Result<Option<[i32;2]>,String>`
- `area_geometry(&self,id:u32)->Result<Option<[f64;12]>,String>`
- `field_sample(&self,id:u32,x:f64,y:f64)->Result<Option<[f64;4]>,String>`
- `water_sample(&self,index:u32)->Result<Option<[f64;8]>,String>`
- `thermal_sample(&self,index:u32)->Result<Option<[f64;10]>,String>`
- `surface_foam_transport(&self,id:u32)->Result<Vec<[f64;7]>,String>`
- `flow_thickness(&self,id:u32)->Result<Option<[f64;6]>,String>`
- `surface_triangles(&self,id:u32)->Result<Vec<[f64;12]>,String>`
- `float_body(&self,id:u32)->Result<Option<[f64;12]>,String>`
- `surface_wave_sample(&self,id:u32,x:f64,z:f64)->Result<[f64;6],String>`
- `path_sample(&self,points:&[[f64;3]],distance:f64,closed:bool,mode:u32)->Result<[f64;8],String>`
- `wave_sample(&self,waves:&[[f64;5]],x:f64,z:f64,seconds:f64)->Result<[f64;6],String>`
- `bidi_visual(&self,text:&str,direction:u32)->Result<Vec<[u32;4]>,String>`
- `bidi_layout(&self,text:&str,columns:u32,direction:u32,ambiguous:u32)->Result<Vec<[u32;7]>,String>`
- `bidi_hit(&self,text:&str,columns:u32,column:u32,row:u32,direction:u32,ambiguous:u32)->Result<u32,String>`
- `bidi_caret(&self,text:&str,columns:u32,offset:u32,affinity:u32,direction:u32,ambiguous:u32)->Result<[u32;3],String>`
- `selected_text(&self)->Result<Option<String>,String>`
- `grapheme_hit(&self,text:&str,columns:u32,column:u32,row:u32,ambiguous:u32)->Result<u32,String>`
- `particle_motions(&self)->Vec<[f64;7]>`
- `particles(&self)->Vec<[i32;12]>`
- `textClusterSample(&self,id:u32,index:u32)->Result<[i32;8],String>`
- `textTrailSample(&self,id:u32,index:u32,trail:u32)->Result<[i32;8],String>`
- `textSample(&self,id:u32,index:u32)->Result<[i32;8],String>`
- `windowSample(&self,id:u32,u:u32,v:u32,visibility:u32)->Result<[i32;5],String>`
- `oklch(lightness:i32,chroma:i32,hue:i32)->Result<u32,String>`
- `composite(base:u32,source:u32,baseAlpha:u32,sourceAlpha:u32,blend:u32,operator:u32,seed:u32)->Result<[u32;2],String>`
- `compositeInSpace(base:u32,source:u32,baseAlpha:u32,sourceAlpha:u32,blend:u32,operator:u32,seed:u32,space:u32)->Result<[u32;2],String>`
- `negotiate_shortcuts(actions:&[u32],candidates:&[[u32;3]],host:&[[u32;3]])->Result<Vec<[u32;4]>,String>`

## Runnable example

[rust/src/main.rs](examples/rust/src/main.rs), [rust/Cargo.toml](examples/rust/Cargo.toml) use [the panel transaction](examples/panel.json). Run from the example directory beside the SDK source. The Go example uses the shared library; Rust builds its native archive.

[Common command field reference](Commands.md).
