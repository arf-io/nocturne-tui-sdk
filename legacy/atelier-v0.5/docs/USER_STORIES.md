# User stories / 36 integration recipes

These map working primitives and mock scenes to applications. A demonstrated visual interaction is not a finished backend product. The last column names the application work that remains. No story implies a network service or agent action was connected.

| # | Story | User-visible goal | Building blocks | Playable/reference entry | Host integration still needed |
|---:|---|---|---|---|---|
| 1 | Agent workbench | See running/queued/blocked state without delaying actual task data. | item,progress,cursor | controls | Wire authenticated agent state and authorized actions. |
| 2 | Fleet wall | Click an agent tile for context while activity light continues. | box,progress,line | fleet | Replace mock nodes with fleet telemetry. |
| 3 | Multi-parent DAG | Select synthesis and inspect both contributing parents. | edge,item,box | fleet | General layout/large-graph virtualization remain host work. |
| 4 | Critical path | Trace predecessor identity without duplicating shared nodes. | edge,text | fleet | Compute actual path semantics externally. |
| 5 | Agent party line | Scan named speakers and select a message for details. | text,rule,item | partyline | Attach transport, timestamps and retention. |
| 6 | Human-agent chat | See prompt edits immediately, with optional ripple feedback. | text,cursor,impulse | starwrite | Implement composition/IME/editor semantics beyond narrow demo input. |
| 7 | Log watch | Inspect events while background motion remains independent. | text,item,rule | logwatch | Wire log source and bounded retention. |
| 8 | Severity filter | Toggle visible classes without stopping render time. | button,item | logwatch | Map buttons to host filtering. |
| 9 | Knowledge navigator | Expand a hierarchy and inspect linked content. | item,rule | knowledge | Wire document identities/search/index. |
| 10 | Drive browser | Show capacity and navigation with disabled operations explicit. | item,progress,donut | knowledge | No filesystem mutation is performed in the example. |
| 11 | Storage health | Compare disk utilization with normalized bars and exact labels. | bars,text | dashboard | Attach health data, units and alerts. |
| 12 | High-density operations dashboard | Keep large headline values and several compact plots readable. | digits,line,bars | dashboard | Supply authoritative values and domain-specific scales. |
| 13 | Build queue | Use a progress rail while counts change between animation samples. | progress,item | controls | Wire build IDs and state. |
| 14 | Deployment topology | Animate traffic along relationships, not random decorative arrows. | edge,box | fleet | Map route IDs and outcome semantics. |
| 15 | Token budget | Separate budget target from decorative bar motion. | progress,text | dashboard | Keep actual accounting in the application. |
| 16 | Inference latency | Inspect a selected point in a braille line. | line | charts | Normalize external units; expose raw values. |
| 17 | Experiment scatter | Click a point to reveal the exact sample identifier. | scatter | charts | Provide matching source records and scales. |
| 18 | Category proportions | Select a pie wedge by geometry or semantic controls. | pie | charts | Attach category names and unrounded weights. |
| 19 | Resource allocation | Use a donut with intentionally empty, nonclickable center. | donut | charts | Place separate center labels without confusing sectors. |
| 20 | Transition rehearsal | Pause, single-step and scrub the same deterministic scene. | all | all | Use fixed fixtures in design review. |
| 21 | Keystroke sonar | Emit feedback at the inserted character, not an arbitrary center. | impulse,text | starwrite | Replay exact insertion events. |
| 22 | Quiet starfield | Use only chosen single-dot glyphs and rare bright events. | star surface | starwrite | Choose art/motion budget per environment. |
| 23 | Nova notification | Represent an occasional noteworthy event with a bounded shockwave. | nova impulse | starwrite | Do not encode critical state solely in fading decoration. |
| 24 | Column focus | Keep the current data column faster than its neighbors. | column material | column-current | Bind focus to table navigation. |
| 25 | Row focus | Create a rapid prompt band with slower surrounding rows. | row material | row-current | Bind focus to text cursor row. |
| 26 | Radial spotlight | Center activity at the cursor with reduced surrounding chroma. | radial material | centricity | Update focus position separately from model selection. |
| 27 | Offscreen light source | Rotate a gradient around a pivot outside the panel. | rotating-linear | pivot-room | Set Q8pivot/rotation period explicitly. |
| 28 | Pendulum background | Ease a bidirectional field without moving text. | rotating-linear | pivot-room | Select swing and rotation mode. |
| 29 | Glass details modal | Open opaque-enough text over a moving lower layer. | box,text,compositor | controls | Trap/restore focus and enforce action permissions. |
| 30 | Section hierarchy | Differentiate information sections with moving line glyph families. | rule | rules | Use motion sparingly when density/attention demand it. |
| 31 | Disabled destructive control | Make an unavailable command visibly disabled and nonactivating. | button | controls | Application still enforces authorization. |
| 32 | Branded TDF title | Render a local TheDraw font once, then recolor its cell art. | externalart,compositor | typography | Requires local fork/font; actual binary untested here. |
| 33 | Animated KPI typography | Zoom original digit geometry and shift its hue. | digits | typography | General word-level zoom is not implemented. |
| 34 | AFD status segment | Supply styled, explicit-time text to an existing scheduler. | status provider | tmux/status.py | AFD API hookup awaits accessible source. |
| 35 | tmux art pane | Run the studio with a matching profile without touching an existing server. | pane app,profile | tmux/preview.py | Requires tmux, not installed locally. |
| 36 | Agent-generated interface | Generate bounded semantic scene JSON and test fixed replay frames. | schema,catalog,all | JSONeditor | Schema validates structure; native renderer validates aggregate limits. |

Acceptance across all stories: stable IDs; disabled actions never activate; pointer/keyboard reach the same semantics; data updates during pause; readable labels without motion; explicit units; terminal ownership stays with one host; fixtures reproduce canonical cells. The supplied browser/POSIX hosts exercise representative interactions, not a blanket end-to-end test of every future application in this table.
