import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const commands0:NativeCommand[]=[
  {
    "op": "resize",
    "width": 100,
    "height": 40
  },
  {
    "op": "camera",
    "position": [
      0,
      6,
      30
    ],
    "yaw": 0,
    "pitch": -8,
    "roll": 0,
    "near": 0.1,
    "far": 200,
    "fov": 70,
    "span": 40,
    "orthographic": false
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 180,
    "starFar": 130,
    "style": "solid"
  },
  {
    "op": "floor",
    "height": -6,
    "visible": true,
    "enabled": false,
    "alpha": 0.45
  },
  {
    "op": "mesh",
    "triangles": [
      {
        "a": [
          -8,
          -4,
          0
        ],
        "b": [
          0,
          8,
          0
        ],
        "c": [
          8,
          -4,
          0
        ],
        "color": 4372668,
        "alpha": 0.75
      },
      {
        "a": [
          -14,
          -3,
          -6
        ],
        "b": [
          -10,
          6,
          -6
        ],
        "c": [
          -6,
          -3,
          -6
        ],
        "color": 12945121,
        "alpha": 0.6
      }
    ]
  },
  {
    "op": "material",
    "id": 3,
    "space": "rgb",
    "channels": {
      "r": 0.2,
      "g": 0.4,
      "b": 0.6
    },
    "alpha": 1
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "draft",
    "text": "Resource ownership preserves the operator draft",
    "emitWeather": false
  },
  {
    "op": "define",
    "path": "/ownership/control",
    "type": "number",
    "value": 12345
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "alpha": 0.6
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "alpha"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": null
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 12345
  },
  {
    "op": "material",
    "id": 2,
    "gradient": [
      [
        0.78,
        0.12,
        205
      ],
      [
        0.68,
        0.15,
        320
      ]
    ],
    "index": {
      "initial": 0,
      "rate": 0.25,
      "min": 0,
      "max": 1,
      "boundary": "reverse"
    },
    "alpha": 0.75
  },
  {
    "op": "window",
    "id": 90,
    "title": "Application / mission control",
    "text": "Shared world, camera and local controls\nLayered content remains readable\nPrompt source survives scene motion",
    "position": [
      10,
      4,
      -4
    ],
    "width": 32,
    "height": 15,
    "material": 2,
    "effect": "window-transition/ribbon-genie"
  }
];
const commands1:NativeCommand[]=[
  {
    "op": "text",
    "id": 90,
    "text": "MISSION / OPERATION CONSOLE",
    "x": 4,
    "y": 3,
    "effect": "text/ink-dissolve",
    "durationMs": 800
  },
  {
    "op": "prompt",
    "active": true,
    "alpha": 0.22
  },
  {
    "op": "draft",
    "text": "A retained application draft",
    "emitWeather": false
  },
  {
    "op": "indicator",
    "id": 90,
    "x": 4,
    "y": 32,
    "sequence": "◐◓◑◒",
    "stepMs": 150
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "surfaceAlpha": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "surfaceAlpha"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "veinContrast": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "veinContrast"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "backTint": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "backTint"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "twoSided": true
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "twoSided": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "twoSided"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "heat": 2
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 2
  }
];
const commands2:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "heat"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "drag": 1
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "drag"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "lift": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "lift"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "flutterHz": 3
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "flutterHz"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "flutterAmount": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "flutterAmount"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.8,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "sizeMin"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 2,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "sizeMax"
    }
  }
];
const commands3:NativeCommand[]=[
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "radius": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "radius"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "windScale": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windScale"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "windPeriodSeconds": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windPeriodSeconds"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "curl": 0.3
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "curl"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 2,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "nearDistance"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 100,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "farDistance"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 10,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 10
  }
];
const commands4:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "farFadeDistance"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "material": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "sampling": "cell"
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "sampling": "braille"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "sampling"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "deposit"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": false,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "collision"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "topology": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "topology"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 120,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 120
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "count"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "rate": 3
  }
];
const commands5:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "rate"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "cycles": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "cycles"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "gapMs": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "gapMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 3000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 3000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "runningTimeMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1500,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "lifetimeMinMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 5000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 5000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "lifetimeMaxMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "tailMs": 1000
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1000
  }
];
const commands6:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "tailMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "trailMs": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "trailMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "birthFadeMs": 200
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 200
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "birthFadeMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "deathFadeMs": 300
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 300
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "deathFadeMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false,
    "coreMs": 200
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "coreMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      2,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "position.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      2,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "position.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      2
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  }
];
const commands7:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "position.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      0,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "extent.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      0,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "extent.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      0
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "extent.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      2,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "velocity.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      2,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "velocity.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      2
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "velocity.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      2,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "spread.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      2,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  }
];
const commands8:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "spread.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      2
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "spread.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      -2,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "gravity.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -2,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "gravity.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      -2
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "gravity.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      2,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "wind.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      2,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "wind.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      2
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "wind.z"
    }
  }
];
const commands9:NativeCommand[]=[
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      2,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windVariation.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      2,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windVariation.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      2
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windVariation.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      20,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 20
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "tumble.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      20,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "tumble.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      20
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "tumble.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.75,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.75
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "shapeWeights.x"
    }
  }
];
const commands10:NativeCommand[]=[
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.75,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "shapeWeights.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.75
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "shapeWeights.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      20,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "birthOrientation.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      20,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "birthOrientation.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      20
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "birthOrientation.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      20,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "initialOrientation.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      20,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "initialOrientation.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      20
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "initialOrientation.z"
    }
  }
];
const commands11:NativeCommand[]=[
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      20,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "angularVelocity.x"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      20,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "angularVelocity.y"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      20
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "angularVelocity.z"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      3,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windX"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      3,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windY"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/autumn-drift",
    "count": 100,
    "runningTimeMs": 2000,
    "lifetimeMinMs": 1000,
    "lifetimeMaxMs": 4000,
    "sizeMin": 0.5,
    "sizeMax": 3,
    "nearDistance": 1,
    "farDistance": 200,
    "farFadeDistance": 0,
    "position": [
      0,
      6,
      0
    ],
    "extent": [
      2,
      2,
      2
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      -4,
      0
    ],
    "wind": [
      0,
      0,
      3
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "tumble": [
      0,
      0,
      0
    ],
    "birthOrientation": [
      0,
      0,
      0
    ],
    "initialOrientation": [
      0,
      0,
      0
    ],
    "angularVelocity": [
      0,
      0,
      0
    ],
    "shapeWeights": [
      0.5,
      0.5,
      0.5
    ],
    "collision": true,
    "deposit": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "windZ"
    }
  },
  {
    "op": "text",
    "id": 1,
    "text": "Nocturne\nRetained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 2
  },
  {
    "op": "text",
    "id": 1,
    "text": "Nocturne\nRetained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "text",
    "id": 1,
    "x": 12
  }
];
const commands12:NativeCommand[]=[
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 12
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "text",
    "id": 1,
    "y": 8
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "text",
    "id": 1,
    "width": 18
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 18
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "width"
    }
  },
  {
    "op": "text",
    "id": 1,
    "batchSize": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "batchSize"
    }
  },
  {
    "op": "text",
    "id": 1,
    "durationMs": 2000
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 2000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "durationMs"
    }
  },
  {
    "op": "text",
    "id": 1,
    "staggerMs": 30
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 30
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "staggerMs"
    }
  }
];
const commands13:NativeCommand[]=[
  {
    "op": "text",
    "id": 1,
    "jitterMs": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "jitterMs"
    }
  },
  {
    "op": "text",
    "id": 1,
    "delayMs": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "delayMs"
    }
  },
  {
    "op": "text",
    "id": 1,
    "distance": 5
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "distance"
    }
  },
  {
    "op": "text",
    "id": 1,
    "scatter": 4
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "scatter"
    }
  },
  {
    "op": "text",
    "id": 1,
    "variation": 0.5
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "variation"
    }
  },
  {
    "op": "text",
    "id": 1,
    "wind": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "wind"
    }
  },
  {
    "op": "text",
    "id": 1,
    "overshoot": 0.6
  }
];
const commands14:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "overshoot"
    }
  },
  {
    "op": "text",
    "id": 1,
    "cycles": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "cycles"
    }
  },
  {
    "op": "text",
    "id": 1,
    "scrambleHz": 30
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "scrambleHz"
    }
  },
  {
    "op": "text",
    "id": 1,
    "hueSpread": 90
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 90
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "hueSpread"
    }
  },
  {
    "op": "text",
    "id": 1,
    "text": "Nocturne\nRetained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 2,
    "reverseOrder": false
  },
  {
    "op": "text",
    "id": 1,
    "reverseOrder": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "reverseOrder"
    }
  },
  {
    "op": "text",
    "id": 1,
    "text": "Nocturne\nRetained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 2,
    "randomOrder": false
  },
  {
    "op": "text",
    "id": 1,
    "randomOrder": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "randomOrder"
    }
  },
  {
    "op": "text",
    "id": 1,
    "trailLength": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "trailLength"
    }
  }
];
const commands15:NativeCommand[]=[
  {
    "op": "text",
    "id": 1,
    "text": "Nocturne\nRetained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 2,
    "local": false
  },
  {
    "op": "text",
    "id": 1,
    "local": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "local"
    }
  },
  {
    "op": "text",
    "id": 1,
    "phase": "hide"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "phase"
    }
  },
  {
    "op": "text",
    "id": 1,
    "easing": "smoother"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "easing"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "alpha": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "alpha"
    }
  },
  {
    "op": "floor",
    "enabled": false,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "enabled"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": false,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "visible"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -3,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -3
  }
];
const commands16:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "height"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "restitution": 0.3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "restitution"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "friction": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "friction"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "settleSpeed": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "settleSpeed"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "reentrainWindSpeed": 5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "reentrainWindSpeed"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 100,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "maxIndividual"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 100,
    "retentionMs": 5000,
    "fadeMs": 500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "maxTiles"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "overflow": "merge-to-field"
  },
  {
    "op": "floor",
    "overflow": "reject-new"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "overflow"
    }
  }
];
const commands17:NativeCommand[]=[
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 4000,
    "fadeMs": 500
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 4000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "retentionMs"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 1000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "fadeMs"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "cellSize": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "cellSize"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "evaporation": 0.2
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "evaporation"
    }
  },
  {
    "op": "floor",
    "enabled": true,
    "visible": true,
    "height": -5,
    "maxIndividual": 200,
    "maxTiles": 150,
    "retentionMs": 5000,
    "fadeMs": 500,
    "sampling": "braille"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "floor",
      "id": 0,
      "field": "sampling"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      2,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "position.x"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      8,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  }
];
const commands18:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "position.y"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      3
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "position.z"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "pinned": false
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "pinned": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "pinned"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "color": 11189196
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 11189196
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "color"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 24,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 24
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "minColumns"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 50,
    "padding": 1
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 50
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "maxColumns"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 2
  }
];
const commands19:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "padding"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "shaPrefix": 8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "shaPrefix"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showKind": true
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showKind": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "showKind"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showStatus": true
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showStatus": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "showStatus"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showSha": true
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showSha": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "showSha"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showDetail": true
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1,
    "showDetail": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "showDetail"
    }
  },
  {
    "op": "area",
    "id": 1,
    "x": 8,
    "y": 6,
    "width": 48,
    "height": 12
  }
];
const commands20:NativeCommand[]=[
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 2,
    "cursor": false
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 1,
    "x": 12,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 2,
    "cursor": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "area"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 16,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 2,
    "cursor": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 16
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 8,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 2,
    "cursor": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 200,
    "material": 2,
    "cursor": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "stepMs"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 3,
    "cursor": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 6,
    "sequence": "◐◓◑◒",
    "stepMs": 120,
    "material": 2,
    "cursor": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "cursor"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 6,
    "border": "rounded",
    "padding": 1,
    "active": true
  },
  {
    "op": "prompt",
    "mode": "grow",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 6,
    "border": "rounded",
    "padding": 1,
    "active": true
  }
];
const commands21:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "mode"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.6,
    "minRows": 1,
    "maxRows": 6,
    "border": "rounded",
    "padding": 1,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "alpha"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 2,
    "maxRows": 6,
    "border": "rounded",
    "padding": 1,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "minRows"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 8,
    "border": "rounded",
    "padding": 1,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "maxRows"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 6,
    "border": "double",
    "padding": 1,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "border"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 6,
    "border": "rounded",
    "padding": 2,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "padding"
    }
  },
  {
    "op": "prompt",
    "mode": "marquee",
    "alpha": 0.4,
    "minRows": 1,
    "maxRows": 6,
    "border": "rounded",
    "padding": 1,
    "active": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "prompt",
      "id": 0,
      "field": "active"
    }
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 180,
    "starFar": 130,
    "sampling": "hybrid",
    "style": "solid"
  },
  {
    "op": "environment",
    "background": 1193046,
    "stars": 180,
    "starFar": 130,
    "sampling": "hybrid",
    "style": "solid"
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1193046
  }
];
const commands22:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "environment",
      "id": 0,
      "field": "background"
    }
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 100,
    "starFar": 130,
    "sampling": "hybrid",
    "style": "solid"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "environment",
      "id": 0,
      "field": "stars"
    }
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 180,
    "starFar": 200,
    "sampling": "hybrid",
    "style": "solid"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "environment",
      "id": 0,
      "field": "starFar"
    }
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 180,
    "starFar": 130,
    "sampling": "braille",
    "style": "solid"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "environment",
      "id": 0,
      "field": "sampling"
    }
  },
  {
    "op": "environment",
    "background": 726312,
    "stars": 180,
    "starFar": 130,
    "sampling": "hybrid",
    "style": "plasma"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "environment",
      "id": 0,
      "field": "style"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 60,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 60
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 18,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 3,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  }
];
const commands23:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "width"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 10,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "speed"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.7,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "strength"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 5000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "lifeMs"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 3,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 3,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "rings"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": false,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "continuous"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 3,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "falloff"
    }
  }
];
const commands24:NativeCommand[]=[
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 2,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "frequency"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 45,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 45
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "phase"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.7,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "interference"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      2,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "velocity.x"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      2
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "velocity.y"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 46,
      "y": 12,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 46
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "surface.x"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 13,
      "width": 25,
      "height": 16
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 13
  }
];
const commands25:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "surface.y"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 30,
      "height": 16
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "surface.width"
    }
  },
  {
    "op": "field",
    "effect": "surface-field/silk-tide",
    "x": 50,
    "y": 16,
    "lifeMs": 4000,
    "width": 2,
    "speed": 8,
    "strength": 0.5,
    "material": 2,
    "rings": 1,
    "continuous": true,
    "falloff": 2,
    "frequency": 1,
    "phase": 0,
    "interference": 0.2,
    "velocity": [
      0,
      0
    ],
    "surface": {
      "x": 45,
      "y": 12,
      "width": 25,
      "height": 18
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "field",
      "id": 1,
      "field": "surface.height"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "oklch",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "l": {
        "initial": 0.7,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "c": {
        "initial": 0.1,
        "min": 0,
        "max": 0.5,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "h": {
        "initial": 180,
        "min": 0,
        "max": 360,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "widget",
    "id": 71,
    "kind": "text",
    "x": 8,
    "y": 10,
    "width": 3,
    "height": 1,
    "padding": 0,
    "border": "none",
    "text": "ABC",
    "material": 3,
    "alpha": 0
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": 0.25
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.25
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "min": 0.1
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "max": 0.9
      }
    }
  }
];
const commands26:NativeCommand[]=[
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.9
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "l": {
        "seed": 73
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 73
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.l.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": 0.25
    }
  }
];
const commands27:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "min": 0.05
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.05
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "max": 0.45
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.45
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "boundary": "reverse"
      }
    }
  }
];
const commands28:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.c.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": 120
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "initial": 120
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "min": 36.0
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 36.0
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "max": 324.0
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 324.0
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "rate": 0.2
      }
    }
  }
];
const commands29:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "h": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.h.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "oklab",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "l": {
        "initial": 0.7,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "a": {
        "initial": 0.1,
        "min": -0.5,
        "max": 0.5,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "b": {
        "initial": 0.1,
        "min": -0.5,
        "max": 0.5,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.initial"
    }
  }
];
const commands30:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "min": -0.4
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "max": 0.4
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.easing"
    }
  }
];
const commands31:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "a": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.a.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "min": -0.4
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "max": 0.4
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.periodMs"
    }
  }
];
const commands32:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.b.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "hsl",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "h": {
        "initial": 0,
        "min": 0,
        "max": 360,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "s": {
        "initial": 1,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "l": {
        "initial": 0.5,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "rate": 0.2
      }
    }
  }
];
const commands33:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "s": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.s.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "hsb",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "h": {
        "initial": 0,
        "min": 0,
        "max": 360,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "s": {
        "initial": 1,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "v": {
        "initial": 1,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.initial"
    }
  }
];
const commands34:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.v.seed"
    }
  }
];
const commands35:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "space": "rgb",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "r": {
        "initial": 0.2,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "g": {
        "initial": 0.4,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "b": {
        "initial": 0.6,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "boundary": "reverse"
      }
    }
  }
];
const commands36:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "r": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.r.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "step": 0.2
      }
    }
  }
];
const commands37:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "g": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.g.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "min": 0.1
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "b": {
        "max": 0.9
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "linear-rgb",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "r": {
        "initial": 0.2,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "g": {
        "initial": 0.4,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "b": {
        "initial": 0.6,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "cmyk",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "c": {
        "initial": 0.1,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "m": {
        "initial": 0.2,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "y": {
        "initial": 0.3,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "k": {
        "initial": 0.4,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "min": 0.1
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "c": {
        "max": 0.9
      }
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": 0.25
    }
  }
];
const commands38:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "easing": "smoother"
      }
    }
  }
];
const commands39:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "m": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.m.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "periodMs": 1500
      }
    }
  }
];
const commands40:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "y": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.y.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": 0.25
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "initial": 0.25
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "min": 0.1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "max": 0.9
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "rate": 0.2
      }
    }
  }
];
const commands41:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "k": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.k.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "indexed",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "i": {
        "initial": 0,
        "min": 0,
        "max": 64,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    },
    "colors": [
      16711680,
      65280,
      255
    ]
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": 1
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "initial": 1
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.initial"
    }
  }
];
const commands42:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "min": 6.4
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 6.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "max": 57.6
      }
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 57.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "rate": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "step": 0.2
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "periodMs": 1500
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "boundary": "reverse"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "easing": "smoother"
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.easing"
    }
  }
];
const commands43:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "channels": {
      "i": {
        "seed": 73
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "channels.i.seed"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.initial"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.min"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.max"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.rate"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.step"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.periodMs"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.boundary"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.easing"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hue.seed"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.initial"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.min"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.max"
    }
  }
];
const commands44:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.rate"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.step"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.periodMs"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.boundary"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.easing"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "lightness.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": 0.5
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness"
    }
  },
  {
    "op": "material",
    "id": 3,
    "channels": {
      "v": {
        "initial": 0.5
      }
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.initial"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.min"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.max"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.rate"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.step"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.periodMs"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.boundary"
    }
  }
];
const commands45:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.easing"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "brightness.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "initial": 0.4
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "min": 0.1
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "max": 0.9
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "rate": 0.2
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "step": 0.2
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "periodMs": 1500
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.periodMs"
    }
  }
];
const commands46:NativeCommand[]=[
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "boundary": "reverse"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "easing": "smoother"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "alpha": {
      "seed": 73
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "alpha.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "rgb",
    "alpha": {
      "initial": 1,
      "min": 0,
      "max": 1,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "index": {
      "initial": 0,
      "min": -1,
      "max": 2,
      "rate": 0,
      "step": 0,
      "periodMs": 1000,
      "seed": 42
    },
    "channels": {
      "r": {
        "initial": 0.2,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "g": {
        "initial": 0.4,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      },
      "b": {
        "initial": 0.6,
        "min": 0,
        "max": 1,
        "rate": 0,
        "step": 0,
        "periodMs": 1000,
        "seed": 42
      }
    },
    "gradient": [
      [
        1,
        0,
        0
      ],
      [
        0,
        1,
        0
      ]
    ]
  },
  {
    "op": "material",
    "id": 3,
    "index": 0.5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "initial": 0.5
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.initial"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "min": -0.7
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -0.7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.min"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "max": 1.7
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1.7
  }
];
const commands47:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.max"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "rate": 0.2
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.rate"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "step": 0.2
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.step"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "periodMs": 1500
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.periodMs"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "boundary": "reverse"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.boundary"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "easing": "smoother"
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.easing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "index": {
      "seed": 73
    }
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "index.seed"
    }
  },
  {
    "op": "material",
    "id": 3,
    "space": "hsl",
    "channels": {
      "h": 0,
      "s": 1,
      "l": 0.5
    },
    "hueStep": 0,
    "spacing": 0,
    "scope": "uniform",
    "blend": "normal"
  },
  {
    "op": "widget",
    "id": 71,
    "kind": "text",
    "text": "ABC",
    "x": 8,
    "y": 10,
    "material": 3
  },
  {
    "op": "material",
    "id": 3,
    "hueStep": 30
  }
];
const commands48:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "hueStep"
    }
  },
  {
    "op": "material",
    "id": 3,
    "spacing": 0.5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "spacing"
    }
  },
  {
    "op": "material",
    "id": 3,
    "scope": "characters"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "scope"
    }
  },
  {
    "op": "material",
    "id": 3,
    "blend": "screen"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "material",
      "id": 3,
      "field": "blend"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "fadeMs": 500
  },
  {
    "op": "mesh",
    "triangles": [
      {
        "a": [
          -10,
          0,
          -10
        ],
        "b": [
          10,
          0,
          -10
        ],
        "c": [
          0,
          0,
          10
        ],
        "surfaceId": 1,
        "color": 1193046,
        "alpha": 0.6
      },
      {
        "a": [
          10,
          0,
          -10
        ],
        "b": [
          20,
          0,
          -10
        ],
        "c": [
          10,
          0,
          10
        ],
        "surfaceId": 1,
        "color": 6636321,
        "alpha": 0.3
      }
    ]
  },
  {
    "op": "surface",
    "id": 1,
    "collisionEnabled": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "collisionEnabled"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "renderVisible": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "renderVisible"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "maxIndividual": 100
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "maxIndividual"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "maxTiles": 100
  }
];
const commands49:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "maxTiles"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "fadeMs": 500,
    "overflow": "merge-to-field"
  },
  {
    "op": "surface",
    "overflow": "reject-new",
    "id": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "overflow"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "restitution": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "restitution"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "friction": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "friction"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "settleSpeed": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "settleSpeed"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "reentrainWindSpeed": 5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "reentrainWindSpeed"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "retentionMs": 4000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "retentionMs"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "fadeMs": 1000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "fadeMs"
    }
  }
];
const commands50:NativeCommand[]=[
  {
    "op": "surface",
    "id": 1,
    "wetnessGain": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "wetnessGain"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "evaporation": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "evaporation"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "heatGain": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "heatGain"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "cooling": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "cooling"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "thermalEvaporation": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "thermalEvaporation"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "wetnessDarkening": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "wetnessDarkening"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "heatColor": 11259375
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 11259375
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "heatColor"
    }
  },
  {
    "op": "surface",
    "id": 1,
    "heatTintStrength": 0.2
  }
];
const commands51:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "heatTintStrength"
    }
  },
  {
    "op": "surface",
    "id": 1
  },
  {
    "op": "ribbon",
    "points": [
      [
        0,
        0,
        -2
      ],
      [
        0,
        0,
        0
      ]
    ],
    "width": 2,
    "surfaceId": 1
  },
  {
    "op": "flow",
    "id": 1,
    "flux": 2,
    "stages": [
      {
        "name": "channel"
      }
    ]
  },
  {
    "op": "flow-surface",
    "surfaceId": 1,
    "flowId": 1,
    "stage": "channel",
    "referenceFlux": 2
  },
  {
    "op": "flow-thickness",
    "surfaceId": 1,
    "width": 2,
    "speed": 2,
    "maxDepth": 1,
    "direction": [
      0,
      1,
      0
    ]
  },
  {
    "op": "flow-thickness-settings",
    "surfaceId": 1,
    "width": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "thickness.width"
    }
  },
  {
    "op": "flow-thickness-settings",
    "surfaceId": 1,
    "speed": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "thickness.speed"
    }
  },
  {
    "op": "surface-water",
    "surfaceId": 1,
    "capacity": 1,
    "evaporationUs": 1000000
  },
  {
    "op": "surface-water-settings",
    "surfaceId": 1,
    "capacity": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "water.capacity"
    }
  },
  {
    "op": "surface-water-settings",
    "surfaceId": 1,
    "evaporationUs": 2000000
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 2000000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface",
      "id": 1,
      "field": "water.evaporationUs"
    }
  }
];
const commands52:NativeCommand[]=[
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        0.75,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.0.amplitude"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.75,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.0.kx"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.75,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.0.kz"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        0.75,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.0.omega"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.75
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.0.phase"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.75,
        0.1,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.1.amplitude"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.75,
        0.2,
        1,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.1.kx"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.75,
        1,
        0.3
      ]
    ]
  }
];
const commands53:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.1.kz"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        0.75,
        0.3
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.1.omega"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        0.2,
        0.3,
        2,
        0.4
      ],
      [
        0.5,
        0.1,
        0.2,
        1,
        0.75
      ]
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-wave",
      "id": 1,
      "field": "waves.1.phase"
    }
  },
  {
    "op": "surface-waves",
    "surfaceId": 1,
    "waves": [
      [
        1,
        1,
        0,
        0,
        0
      ]
    ]
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "enabled": true,
    "sourceRate": 2,
    "curvatureThreshold": 0,
    "decay": 0.5,
    "impactGain": 1,
    "color": 16777215
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "enabled": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "enabled"
    }
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "sourceRate": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "sourceRate"
    }
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "curvatureThreshold": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "curvatureThreshold"
    }
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "decay": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "decay"
    }
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "impactGain": 0.2
  }
];
const commands54:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "impactGain"
    }
  },
  {
    "op": "surface-foam",
    "surfaceId": 1,
    "color": 11259375
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "color"
    }
  },
  {
    "op": "surface-foam-transport",
    "surfaceId": 1,
    "velocity": [
      2,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "velocity.x"
    }
  },
  {
    "op": "surface-foam-transport",
    "surfaceId": 1,
    "velocity": [
      0,
      2
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "surface-foam",
      "id": 1,
      "field": "velocity.z"
    }
  },
  {
    "op": "surface",
    "id": 2
  },
  {
    "op": "float-body",
    "id": 1,
    "surfaceId": 1,
    "position": [
      0,
      0,
      0
    ],
    "velocity": [
      0,
      0,
      0
    ]
  },
  {
    "op": "float-body",
    "id": 1,
    "mass": 2000
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "mass"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "radius": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "radius"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "fluidDensity": 800
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 800
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "fluidDensity"
    }
  }
];
const commands55:NativeCommand[]=[
  {
    "op": "float-body",
    "id": 1,
    "gravity": 10
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "gravity"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "drag": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "drag"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "visible": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "visible"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "color": 11259375
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "color"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "surfaceId": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "surfaceId"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "position": [
      2,
      0,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "position.x"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "position": [
      0,
      2,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "position.y"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "position": [
      0,
      0,
      2
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "position.z"
    }
  }
];
const commands56:NativeCommand[]=[
  {
    "op": "float-body",
    "id": 1,
    "velocity": [
      1,
      0,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "velocity.x"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "velocity": [
      0,
      1,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "velocity.y"
    }
  },
  {
    "op": "float-body",
    "id": 1,
    "velocity": [
      0,
      0,
      1
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "velocity.z"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      100,
      100
    ],
    "angularVelocity": [
      0,
      0,
      0
    ]
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      100,
      100
    ],
    "angularVelocity": [
      2,
      0,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.angularVelocity.x"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      100,
      100
    ],
    "angularVelocity": [
      0,
      2,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.angularVelocity.y"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      100,
      100
    ],
    "angularVelocity": [
      0,
      0,
      2
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.angularVelocity.z"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      200,
      100,
      100
    ],
    "angularVelocity": [
      0,
      0,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.inertia.x"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      200,
      100
    ],
    "angularVelocity": [
      0,
      0,
      0
    ]
  }
];
const commands57:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.inertia.y"
    }
  },
  {
    "op": "float-hull",
    "id": 1,
    "vertices": [
      [
        -1,
        -1,
        -1
      ],
      [
        1,
        -1,
        -1
      ],
      [
        1,
        1,
        -1
      ],
      [
        -1,
        1,
        -1
      ],
      [
        -1,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ],
      [
        1,
        1,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    "faces": [
      [
        0,
        2,
        1
      ],
      [
        0,
        3,
        2
      ],
      [
        4,
        5,
        6
      ],
      [
        4,
        6,
        7
      ],
      [
        0,
        1,
        5
      ],
      [
        0,
        5,
        4
      ],
      [
        3,
        7,
        6
      ],
      [
        3,
        6,
        2
      ],
      [
        0,
        4,
        7
      ],
      [
        0,
        7,
        3
      ],
      [
        1,
        2,
        6
      ],
      [
        1,
        6,
        5
      ]
    ],
    "inertia": [
      100,
      100,
      200
    ],
    "angularVelocity": [
      0,
      0,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "float-body",
      "id": 1,
      "field": "hull.inertia.z"
    }
  },
  {
    "op": "mesh-style",
    "alpha": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "mesh",
      "id": 0,
      "field": "alpha"
    }
  },
  {
    "op": "mesh-style",
    "color": 11259375
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "mesh",
      "id": 0,
      "field": "color"
    }
  },
  {
    "op": "mesh-style",
    "sampling": "braille"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "mesh",
      "id": 0,
      "field": "sampling"
    }
  },
  {
    "op": "mesh-style",
    "triangleIndex": 1,
    "alpha": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "triangle",
      "id": 1,
      "field": "alpha"
    }
  },
  {
    "op": "mesh-style",
    "triangleIndex": 1,
    "color": 11259375
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "triangle",
      "id": 1,
      "field": "color"
    }
  },
  {
    "op": "surface-thermal",
    "triangleIndex": 0,
    "temperature": 400,
    "capacity": 2,
    "ambientTemperature": 300,
    "conductance": 2,
    "power": 4
  },
  {
    "op": "surface-thermal-settings",
    "triangleIndex": 0,
    "power": 8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "triangle",
      "id": 0,
      "field": "thermal.power"
    }
  }
];
const commands58:NativeCommand[]=[
  {
    "op": "surface-thermal-settings",
    "triangleIndex": 0,
    "ambientTemperature": 250
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 250
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "triangle",
      "id": 0,
      "field": "thermal.ambientTemperature"
    }
  },
  {
    "op": "surface-thermal-settings",
    "triangleIndex": 0,
    "conductance": 4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "triangle",
      "id": 0,
      "field": "thermal.conductance"
    }
  },
  {
    "op": "cell-art",
    "id": 1,
    "width": 3,
    "height": 1,
    "x": 8,
    "y": 12,
    "alpha": 0.8,
    "layer": "overlay",
    "cells": [
      [
        65,
        11259375,
        1193046
      ],
      [
        82,
        4372668,
        1056816
      ],
      [
        70,
        12945121,
        1056816
      ]
    ]
  },
  {
    "op": "cell-art",
    "id": 1,
    "x": 18
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "cell-art",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "cell-art",
    "id": 1,
    "y": 20
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "cell-art",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "cell-art",
    "id": 1,
    "alpha": 0.3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "cell-art",
      "id": 1,
      "field": "alpha"
    }
  },
  {
    "op": "cell-art",
    "id": 1,
    "layer": "background"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "cell-art",
      "id": 1,
      "field": "layer"
    }
  },
  {
    "op": "flow",
    "id": 1,
    "flux": 2,
    "stages": [
      {
        "name": "fall",
        "delayUs": 100000,
        "tailUs": 500000
      }
    ]
  },
  {
    "op": "flow-rate",
    "id": 1,
    "flux": 5
  }
];
const commands59:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "flow",
      "id": 1,
      "field": "flux"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 20,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "speed"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0.5,
    "flicker": 0,
    "alpha": 0.8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "jitter"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "alpha"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0.2,
    "alpha": 0.8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "flicker"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8,
    "delayMs": 50.125
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 50.125
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "delayMs"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 150.125,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 150.125
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "holdMs"
    }
  }
];
const commands60:NativeCommand[]=[
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 250.125,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 250.125
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "fadeMs"
    }
  },
  {
    "op": "electrical-arc",
    "id": 7,
    "points": [
      {
        "position": [
          0,
          0,
          0
        ],
        "parent": -1
      },
      {
        "position": [
          3,
          0,
          0
        ],
        "parent": 0
      },
      {
        "position": [
          3,
          4,
          0
        ],
        "parent": 1
      },
      {
        "position": [
          3,
          0,
          12
        ],
        "parent": 1
      }
    ],
    "speed": 10,
    "holdMs": 200,
    "fadeMs": 300,
    "jitter": 0,
    "flicker": 0,
    "alpha": 0.8,
    "repeatMs": 3000.125
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 3000.125
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "electrical-arc",
      "id": 7,
      "field": "repeatMs"
    }
  },
  {
    "op": "emitter",
    "id": 1,
    "effect": "weather/chrysanthemum",
    "seed": 73,
    "count": 1,
    "runningTimeMs": 0,
    "shape": "point",
    "position": [
      0,
      0,
      0
    ],
    "velocity": [
      0,
      0,
      0
    ],
    "extent": [
      0,
      0,
      0
    ],
    "spread": [
      0,
      0,
      0
    ],
    "gravity": [
      0,
      0,
      0
    ],
    "wind": [
      0,
      0,
      0
    ],
    "windVariation": [
      0,
      0,
      0
    ],
    "drag": 0,
    "lift": 0,
    "flutterAmount": 0,
    "tumble": [
      0,
      0,
      0
    ],
    "deposit": false,
    "collision": false,
    "radius": 4,
    "topology": 0,
    "coreMs": 200,
    "trailMs": 90,
    "lifetimeMinMs": 2000,
    "lifetimeMaxMs": 2000
  },
  {
    "op": "burst-style",
    "id": 1,
    "glitterHz": 30
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "glitterHz"
    }
  },
  {
    "op": "burst-style",
    "id": 1,
    "glitterDepth": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "glitterDepth"
    }
  },
  {
    "op": "burst-style",
    "id": 1,
    "coreAlpha": 0.3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "coreAlpha"
    }
  },
  {
    "op": "burst-style",
    "id": 1,
    "residualMs": 350.125
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 350.125
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "residualMs"
    }
  }
];
const commands61:NativeCommand[]=[
  {
    "op": "burst-style",
    "id": 1,
    "residualAlpha": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "emitter",
      "id": 1,
      "field": "residualAlpha"
    }
  },
  {
    "op": "define",
    "path": "/ownership/control",
    "type": "boolean",
    "value": false
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": true
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": false
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": false
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "enabled"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": true,
    "selected": false
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": true,
    "selected": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "selected"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": true,
    "active": false
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Inspect",
    "enabled": true,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "active"
    }
  },
  {
    "op": "camera",
    "orthographic": false
  },
  {
    "op": "camera",
    "orthographic": true
  }
];
const commands62:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "orthographic"
    }
  },
  {
    "op": "area",
    "id": 1,
    "x": 8,
    "y": 8,
    "width": 40,
    "height": 10,
    "hideEmpty": false
  },
  {
    "op": "status",
    "id": 1,
    "area": 1,
    "text": "Native typed controls",
    "durationMs": 0
  },
  {
    "op": "area",
    "id": 1,
    "x": 8,
    "y": 8,
    "width": 40,
    "height": 10,
    "hideEmpty": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "hideEmpty"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Registered action"
  },
  {
    "op": "state-register",
    "id": 1,
    "path": "/app/inspect",
    "role": "control",
    "target": {
      "family": "widget",
      "id": 1
    },
    "active": false
  },
  {
    "op": "style-rule",
    "id": 1,
    "selector": {
      "family": "widget",
      "path": "/app/inspect",
      "states": {
        "active": true
      }
    },
    "style": {
      "alpha": 0.8
    }
  },
  {
    "op": "state-update",
    "id": 1,
    "active": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "state",
      "id": 1,
      "field": "active"
    }
  },
  {
    "op": "accessibility",
    "reducedMotion": false,
    "screenReader": false
  },
  {
    "op": "accessibility",
    "reducedMotion": true,
    "screenReader": false
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "accessibility",
      "id": 0,
      "field": "reducedMotion"
    }
  },
  {
    "op": "accessibility",
    "reducedMotion": false,
    "screenReader": true
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "accessibility",
      "id": 0,
      "field": "screenReader"
    }
  },
  {
    "op": "indicator",
    "id": 1,
    "area": 0,
    "x": 12,
    "y": 6,
    "sequence": "Retained source",
    "stepMs": 120,
    "material": 2,
    "cursor": false
  }
];
const commands63:NativeCommand[]=[
  {
    "op": "define",
    "path": "/ownership/control",
    "type": "string",
    "value": "Detached source remains owned"
  },
  {
    "op": "indicator",
    "id": 1,
    "sequence": "NOC 日本 / source é"
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "indicator",
      "id": 1,
      "field": "sequence"
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": "Detached source remains owned"
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "button",
    "x": 8,
    "y": 12,
    "width": 32,
    "height": 4,
    "text": "Retained source",
    "enabled": true
  },
  {
    "op": "widget",
    "id": 1,
    "text": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "text"
    }
  },
  {
    "op": "window",
    "id": 1,
    "title": "Retained source",
    "text": "Retained document",
    "position": [
      0,
      8,
      0
    ],
    "width": 40,
    "height": 20
  },
  {
    "op": "window",
    "id": 1,
    "title": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "title"
    }
  },
  {
    "op": "window",
    "id": 1,
    "title": "SDK window",
    "text": "Retained source",
    "position": [
      0,
      8,
      0
    ],
    "width": 40,
    "height": 20
  },
  {
    "op": "window",
    "id": 1,
    "text": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "text"
    }
  },
  {
    "op": "text",
    "id": 1,
    "text": "Retained source",
    "x": 8,
    "y": 10,
    "width": 32,
    "effect": "text/ink-dissolve",
    "durationMs": 1500,
    "material": 2
  },
  {
    "op": "text",
    "id": 1,
    "text": "NOC 日本 / source é"
  }
];
const commands64:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "text",
      "id": 1,
      "field": "text"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "Retained source",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "label": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "label"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained source",
    "kind": "task",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "detail": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "detail"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "Retained source",
    "status": "ready",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "kind": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "kind"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "Retained source",
    "sha": "abcdef012345",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "status": "NOC 日本 / source é"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "status"
    }
  },
  {
    "op": "node",
    "id": 1,
    "label": "SDK resource controls",
    "detail": "Retained graph card",
    "kind": "task",
    "status": "ready",
    "sha": "Retained source",
    "position": [
      0,
      6,
      0
    ],
    "minColumns": 22,
    "maxColumns": 44,
    "padding": 1
  },
  {
    "op": "node",
    "id": 1,
    "sha": "fedcba9876543210"
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": "fedcba9876543210"
  }
];
const commands65:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "node",
      "id": 1,
      "field": "sha"
    }
  },
  {
    "op": "camera",
    "position": [
      0,
      6,
      30
    ]
  },
  {
    "op": "camera",
    "position": [
      8,
      6,
      30
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "position.x"
    }
  },
  {
    "op": "camera",
    "position": [
      0,
      9,
      30
    ]
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 9
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "position.y"
    }
  },
  {
    "op": "camera",
    "position": [
      0,
      6,
      24
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "position.z"
    }
  },
  {
    "op": "camera",
    "yaw": 0
  },
  {
    "op": "camera",
    "yaw": 25
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 25
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "yaw"
    }
  },
  {
    "op": "camera",
    "pitch": -8
  },
  {
    "op": "camera",
    "pitch": -15
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -15
  }
];
const commands66:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "pitch"
    }
  },
  {
    "op": "camera",
    "roll": 0
  },
  {
    "op": "camera",
    "roll": 20
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "roll"
    }
  },
  {
    "op": "camera",
    "near": 0.1
  },
  {
    "op": "camera",
    "near": 0.5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "near"
    }
  },
  {
    "op": "camera",
    "far": 200
  },
  {
    "op": "camera",
    "far": 150
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 150
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "far"
    }
  },
  {
    "op": "camera",
    "fov": 70
  },
  {
    "op": "camera",
    "fov": 50
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "fov"
    }
  },
  {
    "op": "camera",
    "span": 40
  },
  {
    "op": "camera",
    "span": 30
  }
];
const commands67:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "camera",
      "id": 0,
      "field": "span"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "donut",
    "x": 8,
    "y": 10,
    "width": 32,
    "height": 12,
    "value": 0.5,
    "data": [
      2,
      3,
      5
    ],
    "alpha": 0.8
  },
  {
    "op": "widget",
    "id": 1,
    "x": 8
  },
  {
    "op": "widget",
    "id": 1,
    "x": 12
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "y": 10
  },
  {
    "op": "widget",
    "id": 1,
    "y": 14
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 14
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "width": 32
  },
  {
    "op": "widget",
    "id": 1,
    "width": 28
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 28
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "width"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "height": 12
  },
  {
    "op": "widget",
    "id": 1,
    "height": 8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "height"
    }
  }
];
const commands68:NativeCommand[]=[
  {
    "op": "widget",
    "id": 1,
    "padding": 0
  },
  {
    "op": "widget",
    "id": 1,
    "padding": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "padding"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "min": 0
  },
  {
    "op": "widget",
    "id": 1,
    "min": -0.5
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": -0.5
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "min"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "max": 1
  },
  {
    "op": "widget",
    "id": 1,
    "max": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "max"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "mode": 0
  },
  {
    "op": "widget",
    "id": 1,
    "mode": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "mode"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "pulseMs": 1000
  },
  {
    "op": "widget",
    "id": 1,
    "pulseMs": 400
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 400
  }
];
const commands69:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "pulseMs"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "cellAspect": 2
  },
  {
    "op": "widget",
    "id": 1,
    "cellAspect": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "cellAspect"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "innerRadius": 0.55
  },
  {
    "op": "widget",
    "id": 1,
    "innerRadius": 0.7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "innerRadius"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "startAngle": 0
  },
  {
    "op": "widget",
    "id": 1,
    "startAngle": 45
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "startAngle"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "sweepAngle": 360
  },
  {
    "op": "widget",
    "id": 1,
    "sweepAngle": 200
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "sweepAngle"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "alpha": 0.4
  },
  {
    "op": "widget",
    "id": 1,
    "alpha": 0.7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "alpha"
    }
  }
];
const commands70:NativeCommand[]=[
  {
    "op": "widget",
    "id": 1,
    "value": 0.2
  },
  {
    "op": "widget",
    "id": 1,
    "value": 0.7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "value"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "material": 2
  },
  {
    "op": "widget",
    "id": 1,
    "material": 0
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "backgroundMaterial": -1
  },
  {
    "op": "widget",
    "id": 1,
    "backgroundMaterial": 0
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "backgroundMaterial"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "border": "none"
  },
  {
    "op": "widget",
    "id": 1,
    "border": "square"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "border"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "sampling": "cell"
  },
  {
    "op": "widget",
    "id": 1,
    "sampling": "braille"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "sampling"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "revealMs": 1000
  }
];
const commands71:NativeCommand[]=[
  {
    "op": "widget",
    "id": 1,
    "revealMs": 1500
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "revealMs"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "enabled": false
  },
  {
    "op": "widget",
    "id": 1,
    "enabled": true
  },
  {
    "op": "widget",
    "id": 1,
    "selected": false
  },
  {
    "op": "widget",
    "id": 1,
    "selected": true
  },
  {
    "op": "widget",
    "id": 1,
    "active": false
  },
  {
    "op": "widget",
    "id": 1,
    "active": true
  },
  {
    "op": "window",
    "id": 1,
    "title": "Retained panel",
    "text": "Native numeric controls\nGeometry, chrome and transition\nRetained document source",
    "position": [
      0,
      4,
      0
    ],
    "width": 30,
    "height": 14,
    "effect": "window-transition/ribbon-genie"
  },
  {
    "op": "window",
    "id": 1,
    "position": [
      0,
      4,
      0
    ]
  },
  {
    "op": "window",
    "id": 1,
    "position": [
      8,
      4,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "position.x"
    }
  },
  {
    "op": "window",
    "id": 1,
    "position": [
      0,
      8,
      0
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "position.y"
    }
  },
  {
    "op": "window",
    "id": 1,
    "position": [
      0,
      4,
      3
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "position.z"
    }
  }
];
const commands72:NativeCommand[]=[
  {
    "op": "window",
    "id": 1,
    "yaw": 0
  },
  {
    "op": "window",
    "id": 1,
    "yaw": 25
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "yaw"
    }
  },
  {
    "op": "window",
    "id": 1,
    "pitch": 0
  },
  {
    "op": "window",
    "id": 1,
    "pitch": 15
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 15
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "pitch"
    }
  },
  {
    "op": "window",
    "id": 1,
    "roll": 0
  },
  {
    "op": "window",
    "id": 1,
    "roll": 10
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "roll"
    }
  },
  {
    "op": "window",
    "id": 1,
    "width": 30
  },
  {
    "op": "window",
    "id": 1,
    "width": 38
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 38
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "width"
    }
  },
  {
    "op": "window",
    "id": 1,
    "height": 14
  },
  {
    "op": "window",
    "id": 1,
    "height": 18
  }
];
const commands73:NativeCommand[]=[
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "height"
    }
  },
  {
    "op": "window",
    "id": 1,
    "minColumns": 30
  },
  {
    "op": "window",
    "id": 1,
    "minColumns": 36
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 36
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "minColumns"
    }
  },
  {
    "op": "window",
    "id": 1,
    "maxColumns": 78
  },
  {
    "op": "window",
    "id": 1,
    "maxColumns": 68
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 68
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "maxColumns"
    }
  },
  {
    "op": "window",
    "id": 1,
    "padding": 1
  },
  {
    "op": "window",
    "id": 1,
    "padding": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "padding"
    }
  },
  {
    "op": "window",
    "id": 1,
    "chromeSize": 3
  },
  {
    "op": "window",
    "id": 1,
    "chromeSize": 4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "chromeSize"
    }
  },
  {
    "op": "window",
    "id": 1,
    "fadeStartRatio": 1
  }
];
const commands74:NativeCommand[]=[
  {
    "op": "window",
    "id": 1,
    "fadeStartRatio": 1.2
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "fadeStartRatio"
    }
  },
  {
    "op": "window",
    "id": 1,
    "fadeEndRatio": 0.22
  },
  {
    "op": "window",
    "id": 1,
    "fadeEndRatio": 0.1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "fadeEndRatio"
    }
  },
  {
    "op": "window",
    "id": 1,
    "anchorX": 0.5
  },
  {
    "op": "window",
    "id": 1,
    "anchorX": 0.2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "anchorX"
    }
  },
  {
    "op": "window",
    "id": 1,
    "anchorY": 1.15
  },
  {
    "op": "window",
    "id": 1,
    "anchorY": 0.8
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "anchorY"
    }
  },
  {
    "op": "window",
    "id": 1,
    "overshoot": 0.18
  },
  {
    "op": "window",
    "id": 1,
    "overshoot": 0.4
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "overshoot"
    }
  },
  {
    "op": "window",
    "id": 1,
    "scatter": 32
  }
];
const commands75:NativeCommand[]=[
  {
    "op": "window",
    "id": 1,
    "scatter": 16
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "scatter"
    }
  },
  {
    "op": "window",
    "id": 1,
    "bend": 9
  },
  {
    "op": "window",
    "id": 1,
    "bend": 14
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "bend"
    }
  },
  {
    "op": "window",
    "id": 1,
    "folds": 6
  },
  {
    "op": "window",
    "id": 1,
    "folds": 10
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "folds"
    }
  },
  {
    "op": "window",
    "id": 1,
    "meshColumns": 12
  },
  {
    "op": "window",
    "id": 1,
    "meshColumns": 16
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "meshColumns"
    }
  },
  {
    "op": "window",
    "id": 1,
    "meshRows": 8
  },
  {
    "op": "window",
    "id": 1,
    "meshRows": 12
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "meshRows"
    }
  },
  {
    "op": "window",
    "id": 1,
    "durationMs": 600
  },
  {
    "op": "window",
    "id": 1,
    "durationMs": 1200
  }
];
const commands76:NativeCommand[]=[
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 1200
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "durationMs"
    }
  },
  {
    "op": "area",
    "id": 1,
    "x": 8,
    "y": 26,
    "width": 60,
    "height": 7
  },
  {
    "op": "status",
    "id": 1,
    "area": 1,
    "text": "Build started",
    "durationMs": 0
  },
  {
    "op": "status",
    "id": 2,
    "area": 1,
    "text": "Reusable native notification layout",
    "durationMs": 0
  },
  {
    "op": "area",
    "id": 1,
    "x": 8
  },
  {
    "op": "area",
    "id": 1,
    "x": 12
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "x"
    }
  },
  {
    "op": "area",
    "id": 1,
    "y": 26
  },
  {
    "op": "area",
    "id": 1,
    "y": 24
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "y"
    }
  },
  {
    "op": "area",
    "id": 1,
    "width": 60
  },
  {
    "op": "area",
    "id": 1,
    "width": 72
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 72
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "width"
    }
  },
  {
    "op": "area",
    "id": 1,
    "height": 7
  }
];
const commands77:NativeCommand[]=[
  {
    "op": "area",
    "id": 1,
    "height": 9
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "height"
    }
  },
  {
    "op": "area",
    "id": 1,
    "padding": 1
  },
  {
    "op": "area",
    "id": 1,
    "padding": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "padding"
    }
  },
  {
    "op": "area",
    "id": 1,
    "margin": 0
  },
  {
    "op": "area",
    "id": 1,
    "margin": 1
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "margin"
    }
  },
  {
    "op": "area",
    "id": 1,
    "speedX": 8
  },
  {
    "op": "area",
    "id": 1,
    "speedX": 16
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "speedX"
    }
  },
  {
    "op": "area",
    "id": 1,
    "speedY": 1
  },
  {
    "op": "area",
    "id": 1,
    "speedY": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "speedY"
    }
  },
  {
    "op": "area",
    "id": 1,
    "hideEmpty": false
  },
  {
    "op": "area",
    "id": 1,
    "hideEmpty": true
  }
];
const commands78:NativeCommand[]=[
  {
    "op": "area",
    "id": 1,
    "fadeMs": 500
  },
  {
    "op": "area",
    "id": 1,
    "fadeMs": 800
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "fadeMs"
    }
  },
  {
    "op": "area",
    "id": 1,
    "gapMs": 300
  },
  {
    "op": "area",
    "id": 1,
    "gapMs": 600
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 600
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "gapMs"
    }
  },
  {
    "op": "window",
    "id": 1,
    "alpha": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "alpha"
    }
  },
  {
    "op": "window",
    "id": 1,
    "material": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "window",
    "id": 1,
    "border": "heavy"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "border"
    }
  },
  {
    "op": "window",
    "id": 1,
    "shape": "ellipse"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "shape"
    }
  },
  {
    "op": "window",
    "id": 1,
    "group": 7
  }
];
const commands79:NativeCommand[]=[
  {
    "op": "set",
    "path": "/ownership/control",
    "value": 7
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "window",
      "id": 1,
      "field": "group"
    }
  },
  {
    "op": "area",
    "id": 1,
    "alpha": 0.6
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "alpha"
    }
  },
  {
    "op": "area",
    "id": 1,
    "material": 3
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "material"
    }
  },
  {
    "op": "area",
    "id": 1,
    "border": "heavy"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "border"
    }
  },
  {
    "op": "area",
    "id": 1,
    "layout": "direct"
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "layout"
    }
  },
  {
    "op": "area",
    "id": 2,
    "x": 0,
    "y": 0,
    "width": 100,
    "height": 40
  },
  {
    "op": "area",
    "id": 1,
    "parent": 2
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "area",
      "id": 1,
      "field": "parent"
    }
  },
  {
    "op": "widget",
    "id": 1,
    "kind": "donut",
    "data": [
      1,
      2,
      3
    ],
    "x": 8,
    "y": 10,
    "width": 32,
    "height": 12
  },
  {
    "op": "define",
    "path": "/ownership/control",
    "type": "json",
    "value": [
      7,
      8
    ]
  },
  {
    "op": "widget",
    "id": 1,
    "data": [
      2,
      3,
      5
    ]
  }
];
const commands80:NativeCommand[]=[
  {
    "op": "set",
    "path": "/ownership/control",
    "value": [
      2,
      3,
      5
    ]
  },
  {
    "op": "bind",
    "path": "/ownership/control",
    "binding": {
      "family": "widget",
      "id": 1,
      "field": "data"
    }
  },
  {
    "op": "set",
    "path": "/ownership/control",
    "value": [
      7,
      8
    ]
  }
];
// @ts-expect-error unsupported replacement field must reject
const rejected0:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "emitter", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected1:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "text", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected2:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "floor", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected3:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "node", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected4:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "indicator", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected5:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "prompt", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected6:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "environment", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected7:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "field", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected8:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "material", "id": 3, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected9:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "surface", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected10:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "surface-wave", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected11:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "surface-foam", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected12:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "float-body", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected13:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "mesh", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected14:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "triangle", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected15:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "triangle", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected16:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "cell-art", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected17:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "flow", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected18:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "electrical-arc", "id": 7, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected19:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "widget", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected20:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "camera", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected21:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "area", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected22:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "state", "id": 1, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected23:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "accessibility", "id": 0, "field": "unsupported"}};
// @ts-expect-error unsupported replacement field must reject
const rejected24:NativeCommand={"op": "bind", "path": "/ownership/control", "binding": {"family": "window", "id": 1, "field": "unsupported"}};
