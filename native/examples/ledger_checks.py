"""Independent resource-balance checks for connected public-command studies."""
def check_ledgers(info,checks):
 def near(a,b):
  if abs(a-b)>1e-5:raise RuntimeError(f'Resource ledger mismatch: {a} versus {b}')
 for check in checks:
  if check['kind']=='water':
   water=next(w for w in info['surfaceWater'] if w['surfaceId']==check['surfaceId'])
   if water['receivedVolume']<=0:raise RuntimeError('Water scene produced no accounted impacts')
   near(water['receivedVolume']+water['importedVolume'],water['retainedVolume']+water['evaporatedVolume']+water['exportedVolume']+water['transferredVolume'])
   spray=info['flowSprays'][0]
   near(spray['receivedVolume'],spray['emittedVolume']+spray['pendingVolume'])
   near(spray['flowReceivedVolume'],water['retainedVolume']+water['evaporatedVolume']+water['exportedVolume']+spray['liveVolume']+spray['expiredVolume']+spray['exportedVolume']+spray['pendingVolume']+spray['legacyUnresolvedVolume'])
  elif check['kind']=='thermal':
   cells=info['surfaceThermal']['cells']
   if not any(c['importedEnergy']>0 for c in cells):raise RuntimeError('Thermal network exchanged no accounted energy')
   for c in cells:near(c['energy'],c['initialEnergy']+c['appliedEnergy']+c['environmentEnergy']+c['importedEnergy']-c['transferredEnergy'])
   near(sum(c['importedEnergy'] for c in cells),sum(c['transferredEnergy'] for c in cells))
  else:raise ValueError('Unknown ledger check')
