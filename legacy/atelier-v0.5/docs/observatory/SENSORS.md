# Sensors and reactive materials

Capture is opt-in. The base gallery has a labelled synthetic feed. Browser audio, browser motion and localhost sensors require explicit controls. No audio playback, recording, automatic persistence or uploads are implemented. Stop closes tracks/subscriptions; exports can contain supplied metadata, so treat exports as potentially sensitive.

## Browser microphone and shared output

Open the standalone gallery or serve it locally. Expand **Audio & system measurements**, then select **Enable microphone** or **Share output audio**. Permission denial is an error, not silent fallback. The shared-source picker may require selecting a video/tab/window alongside audio, and may provide no audio track on a particular browser/OS/source. The gallery does not capture screenshots from the shared video, but a chosen video track remains part of the explicitly shared stream until Stop. All tracks are stopped together.

An `AnalyserNode` produces a waveform, RMS, peak, and coarse bass/mid/treble levels. These are display/reactivity features, not calibrated audio metering or a musical-analysis API. Time-domain values are normalized full-scale samples. No sound is routed to speakers. Browser `devicemotion` is separately requested where available, and permission/API absence is reported.

The software tests use a synthetic Web Audio oscillator. Physical microphone capture, shared system audio and physical accelerometers were not accessible in the development environment.

## Linux system readings

```sh
python3 scripts/serve_observatory.py --port 8765
# Open http://127.0.0.1:8765, then click Connect localhost sensors.
```

The server binds only loopback, permits expected Host/Origin values, denies cross-site requests and arbitrary paths, serves the exact gallery, and offers at most four SSE readers. It does not expose shell execution, file uploads, a directory listing or CORS. Do not reverse-proxy it onto a public interface.

`sensors/system_sensors.py` reads only accessible sysfs/proc files. It supports hwmon temperatures/power, battery `power_now`, powercap energy differences, network byte-counter deltas and exposed IIO acceleration. Hardware/channel identity is retained rather than claiming every temperature means CPU package temperature. No sudo, sensor writes, driver loading or package-power limits are changed.

Temperature uses degrees Celsius; power uses watts; network rates use megabits/second. Network/power-delta sources need two samples. Reset/wrap handling avoids negative or fabricated rates. RAPL domains are separate measurements: do not add overlapping package/subdomain values into a supposed total. Absent/unreadable channels are omitted. Platform availability is not guaranteed. The raw collector may enumerate more sources than the display model's 128-source budget; select an allowlist for very large machines.

Pipe measurements into the terminal host using Bash:

```sh
node examples/observatory_terminal.mjs --scene sensors --sensor-fd 3 \
  3< <(python3 sensors/system_sensors.py --interval 0.25)
```

The inherited descriptor must be a pipe/socket, not a regular file. Each record is limited to 64 KiB. Input `atMs` is normalized into the host monotonic domain; preserve an original-source timestamp in your adapter when required. The synthetic feed is disabled with an external descriptor.

## Native Linux input/output audio

The optional producer uses a caller-selected Pulse-compatible `parec` source. It does not guess a microphone or silently capture the default output. `parec` is not bundled and was not installed locally.

```sh
pactl list short sources
python3 sensors/audio_sensors.py --kind input --device YOUR_MIC_SOURCE
python3 sensors/audio_sensors.py --kind output --device YOUR_SINK_MONITOR_SOURCE
```

Use the selected producer in the descriptor example above. `--stdin-pcm` alternatively accepts little-endian float32 mono PCM from an explicit pipe, 16 kHz by default. It emits scalar RMS/peak records and bounded waveform blocks, not recordings. Hardware capture was not tested; feature extraction was tested on known numeric signals.

## Data records

```json
{"source":"audio.input.rms","value":0.18,"atMs":1200,"seq":1,"unit":"FS","quality":"measured"}
{"source":"temperature.package","value":57.5,"atMs":1200,"seq":1,"unit":"C","quality":"external"}
{"type":"waveform","source":"audio.input.waveform","samples":[0,0.12,-0.18,0.05],"atMs":1200,"seq":1,"quality":"measured"}
```

Sequences increase per source, in one timestamp domain. Duplicates return false; nonfinite, oversized, backward-time and malformed records reject without consuming the sequence. Unknown capture quality defaults to `external`, not verified measurement. Browser file import currently accepts scalar records; waveform blocks are supported by the model and terminal descriptor. Sources remain labelled synthetic/external/measured according to their adapter, not according to the appearance of the chart.

## Routing

A route maps an input range to an output range, optionally with a nonlinear curve/deadband and attack/release envelopes. The browser provides 32 destinations. One route owns each destination; adding another replaces that destination's route. No automatic mixing order hides behind the UI.

Examples to configure explicitly:

| Source | Input range | Destination | Output range | Attack / release |
|---|---:|---|---:|---:|
| Microphone RMS | 0..0.5 | brightness | .10.. .38 | 60 / 420 ms |
| Audio peak | 0..1 | novaRegularity | 0..12/min | 20 / 1000 ms |
| Temperature | 35..85 C | hueOffset | 0..150 degrees | 500 / 2000 ms |
| Network rate | 0..1000 Mbit/s | starSpeed | 2..25 units/s | 200 / 800 ms |
| Acceleration X | -10..10 m/s² | cameraRoll | -25..25 degrees | 80 / 300 ms |
| Power | 20..300 W | chroma | .04.. .20 | 400 / 1200 ms |

These are artistic mappings, not alarm thresholds or health/safety limits. Keep authoritative severity/status indications separate from these effects. Saturation is expressed as **OKLCh chroma**, not HSV S. Out-of-gamut chroma is reduced for sRGB. Stale sources restore baseline after route TTL, two seconds in the gallery. Last measured text can remain visible until replaced; it must not be interpreted as a fresh sample just because a decorative curve moves.
