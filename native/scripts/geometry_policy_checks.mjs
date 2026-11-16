export function checkGeometryPolicy(scene,recipe){
 const info=scene.infoComplete(),rows=scene.surfaceTriangles(1);
 if(info.geometry.triangles!==recipe.expectedTriangleCount)throw Error('Replace/append triangle count');
 if(JSON.stringify(rows.map(row=>row.slice(1,10)))!==JSON.stringify(recipe.expectedVertices))throw Error('Independent geometry vertices');
 const state=info.registeredStates.find(r=>r.id===21);
 if(state.authored.sampling!==['cell','half','braille','hybrid'].indexOf(recipe.sampling))throw Error('Authored sampling');
 if(info.prompt.text!==recipe.expectedPrompt)throw Error('Draft ownership');
}
