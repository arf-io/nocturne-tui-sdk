/** Resolve initial gallery links without replacing recipe or clock ownership. */
export function resolveGalleryLocation(hash, recipes) {
  const parameters = new URLSearchParams(hash.replace(/^#/, ''));
  if (!parameters.has('scene') && !parameters.has('timeUs')) return null;
  for (const key of parameters.keys()) {
    if (!['scene', 'timeUs'].includes(key) || parameters.getAll(key).length !== 1) {
      throw new Error('Gallery link has unknown or duplicate parameters. Use scene and timeUs.');
    }
  }
  const identity = parameters.get('scene');
  if (!identity) throw new Error('Gallery link requires a scene identity.');
  const matches = recipes.filter(recipe => recipe.id === identity);
  if (matches.length !== 1) throw new Error('Gallery link scene was not found: ' + identity);
  const encodedTime = parameters.get('timeUs') ?? '0';
  if (!/^\d+$/.test(encodedTime)) {
    throw new Error('Gallery link timeUs must be nonnegative integer microseconds.');
  }
  const timeUs = Number(encodedTime);
  if (!Number.isSafeInteger(timeUs) || timeUs > 86400000000) {
    throw new Error('Gallery link timeUs exceeds the 24-hour scene range.');
  }
  return {recipe: matches[0], timeUs};
}
