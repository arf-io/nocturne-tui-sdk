# Spatial Atelier / interaction field guide

## Start with the right file

Open `START-HERE.html` from the v0.5 archive. Its default scene tile, scene dropdown and canvas title all name **Oblique Hyperlane**. No recipe dropdown is needed. The build badge distinguishes it from Observatory v0.4; previous galleries remain usable but are not this update.

## Look, move, travel

1. Drag the canvas or press the Look arrows. Switch **Look** to **Orbit** to turn around the selected target instead of turning the view in place.
2. Shift-drag or press the Move arrows to strafe. Forward/back translates the rig; Zoom changes its target distance. Roll rotates the horizon.
3. Change **Velocity**, **Heading** and **Elevation** to steer starflight. Looking and flying are independent. **Aim along view** transfers the current view direction once; **Brake** stops flight while stars remain visible; **Reverse** changes its sign. **Reset flight** restores the named entry composition.
4. **Home** resets the camera; **Frame all** finds the current graph. Use exact XYZ/angle/FOV inputs for reproducible placement.

Shortcuts apply only while the canvas has focus, not while typing in a field. On the browser canvas: arrows look; Shift-arrows strafe; W/S move forward/back; Q/E roll; H resets; +/- zoom. Space holds decorative motion. The terminal uses Alt-modified camera keys so normal text can be typed, and exposes all actions through Ctrl+G.

## Layout without inventing a tree

Open Graph Observatory, choose 2D/3D and layered/force/radial, then **Arrange**. The force job yields between work slices in the browser/terminal host; animation does not solve the graph each frame. Selected node inspection lists its original parents. Pin a node, rerun, and unpin when it should move again.

The example cyclic graph demonstrates SCC disclosure. Condense groups cycles for ranking while keeping original edges/nodes in the returned layout. Reject reports the problem and leaves the existing graph intact. Import and export expose graph data and generated coordinates. The current layout limit is 256 nodes/2,048 edges; this is an interactive bounded solver, not a million-node engine.

## Electrical Garden

Each button creates a named burst at a visible location. Clicking empty scene space emits the chosen weather. Select **nova** for a brief core, bright spokes and ejecta; shockwave is a separate secondary control. **Sparks** branch and fork with seeded jitter. **Embers** rise, slow at the apex, and return under gravity; adjust rise/gravity/lifetime together so the return occurs before expiry. Glitter is brightness variation, not glyph replacement every frame.

Motion reduction suppresses weather without suppressing typing. Intensity and count can be lowered independently. Rapid flashes are confined effects; avoid extreme settings for light-sensitive viewers.

## Typography Foundry

Enter the original text in the source field. Choose an entrance and an exit separately, then Reveal/Conceal. Replay resets a completed study; changing direction without replay starts from its current appearance. Original accessible text is always available.

Rain uses independent initial position, drift, delayed batches and speed variation. Flipboard advances an ordered user-supplied alphabet; scramble uses seeded substitutions. Batched sweeps deliver 1..N characters together, with independent delay/stagger. Hides include reverse sweeps, rain/fall, fade, fold, blank-target flipboard and marquee exits.

Original studies include **Comet Stitch** (a luminous moving seam resolves the line), **Prism Weave** (opposing colored ribbons settle into reading order), **Ink Tide** (a spatial wave deposits/restores ink), **Constellation** (distributed positions converge), and **Zipper**. These are creative designs, not a claim that no artist has ever used a similar animation.

## Impossible Windows

The default controls have 6×2 source-cell hit pads, color-coded per action. Browser companion buttons remain large regardless of 3D distance. Customize pad dimensions, action order, glyphs and colors. mac/windows/gnome are arrangement presets, not emulators of those desktop environments.

Drag a window body to move it; Alt-drag rotates the workspace. Select a window in the sidebar to change its depth, yaw, pitch, roll and source dimensions. A distant surface becomes smaller and can be faded independently. The camera Frame/Home controls and dock are recovery mechanisms.

Minimize/Close preserve the object. Every surface remains in the dock; clicking it restores visibility, opacity and the rolled body. Roll is its own reversible body tween, so it can be combined with fading. Expand/minimize/maximize transitions use the selected geometric effect. Genie travels toward that window's dock slot. Bounce and overshoot are optional, bounded controls.

Bodies may be ellipse, hexagon, diamond, capsule, ticket, cloud, rounded, rectangle or custom polygon. The full-width chrome floats above the body mask deliberately. Important content may need padding or an internal rectangular plane. Projected planes use painter ordering rather than a solid-object depth buffer; intersecting planes are artistic composition, not guaranteed CAD-style occlusion.

## Bring application data

Use `setWindowPainter(windowId,painter)` to paint a body's owned cell frame with your widgets/data. The same transform, mask, alpha and hit mapping applies to it. `examples/atelier_embed.mjs` is the complete runnable example.

Visual settings include the graph, camera, effects and window intent, not private transcripts. Import validates a new model atomically, preserves the gallery's current notes/draft/scratch content, then restarts visual time. This is not a full session replay format.
