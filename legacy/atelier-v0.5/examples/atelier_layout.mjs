#!/usr/bin/env node
/** Read graph JSON from a named file (or use the shared example); write layout.
 * node examples/atelier_layout.mjs graph.json 3 force > arranged.json */
import fs from 'node:fs';
import {layoutGraph} from '../dist/typescript/spatial.js';
import {DEFAULT_GRAPH} from '../dist/typescript/atelier.js';
const [file,dimensions='3',algorithm='layered']=process.argv.slice(2);
if(file==='--help'){console.log('node examples/atelier_layout.mjs [graph.json] [2|3] [layered|force|radial]');process.exit(0);}
if(file&&fs.statSync(file).size>1048576)throw new RangeError('Graph JSON limit: 1 MiB');
const graph=file?JSON.parse(fs.readFileSync(file,'utf8')):DEFAULT_GRAPH;
console.log(JSON.stringify(layoutGraph(graph,{dimensions:Number(dimensions),algorithm}),null,2));
