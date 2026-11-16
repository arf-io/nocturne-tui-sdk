/** Gallery attract policy: which recipes rotate, their order and their provenance caption.
 * Import-free and pure. Randomness is injected; no DOM, clock or scene state is read. */

/** Isolated compositions of these features rotate and are grouped as 3D scenes. */
export const GALLERY_SCENIC_FEATURES = Object.freeze(['shared-ocean', 'waterfall-composition', 'road-composition', 'garden-composition']);
const scenicFeatureSet = new Set(GALLERY_SCENIC_FEATURES);

/** Attract shows classic, original and scenic demos rather than thousands of parameter probes. */
export function isAttractRecipe(recipe) {
  return recipe.demo === true || !recipe.demonstrates || (recipe.mode === 'isolated' && scenicFeatureSet.has(recipe.demonstrates.feature));
}

/** Shuffle-bag rotation over every recipe. Each bag is a permutation of the whole list drawn
 * with random(), which must return numbers in [0, 1). next(currentId) never returns the
 * recipe on screen: a fresh bag never starts with it, and a recipe already on screen while
 * still pending (manual exploration, then resume) counts as shown for that bag. */
export function createAttractRotation(recipes, random) {
  if (!Array.isArray(recipes)) throw new TypeError('Attract rotation requires an array of recipes');
  if (typeof random !== 'function') throw new TypeError('Attract rotation requires an injected random source');
  const pool = recipes.slice(), identities = new Set();
  for (const recipe of pool) {
    const id = recipe?.id;
    if (typeof id !== 'string' || !id || identities.has(id)) throw new Error('Attract rotation requires unique nonempty recipe identities');
    identities.add(id);
  }
  let bag = [];
  const draw = bound => {
    const value = random();
    if (typeof value !== 'number' || !(value >= 0 && value < 1)) throw new RangeError('Attract random source must return a number in [0, 1)');
    return Math.floor(value * bound);
  };
  const refill = currentId => {
    bag = pool.slice();
    for (let i = bag.length - 1; i > 0; i--) {
      const j = draw(i + 1);
      [bag[i], bag[j]] = [bag[j], bag[i]];
    }
    if (bag.length > 1 && bag[0].id === currentId) {
      const j = 1 + draw(bag.length - 1);
      [bag[0], bag[j]] = [bag[j], bag[0]];
    }
  };
  return {
    next(currentId) {
      if (!pool.some(recipe => recipe.id !== currentId)) return null;
      bag = bag.filter(recipe => recipe.id !== currentId);
      if (!bag.length) refill(currentId);
      return bag.shift();
    },
  };
}

const nonempty = value => typeof value === 'string' && value.trim() !== '';

/** Caption naming a recipe's edition and component (or source commit), its source identity
 * and its stable recipe identity. Attribution text is shown as recorded, never shortened.
 * A catalogue identity is historical naming, not an accepted port, and is labelled so. */
export function recipeProvenance(recipe) {
  if (!recipe || !nonempty(recipe.id)) throw new TypeError('Gallery provenance requires a recipe identity');
  const source = recipe.provenance, parts = [];
  if (source && typeof source === 'object') {
    parts.push(source.release);
    if (nonempty(source.component)) parts.push(source.component);
    else if (nonempty(source.sourceCommit)) parts.push('commit ' + source.sourceCommit.slice(0, 12));
    parts.push(source.sourceIdentity);
  } else if (recipe.demonstrates) {
    const study = recipe.demonstrates;
    parts.push('API study', recipe.catalogueEffect ?? study.feature ?? study.effect ?? study.contract);
    if (nonempty(recipe.sourceIdentity)) parts.push('catalogue identity ' + recipe.sourceIdentity);
  } else {
    parts.push('SDK recipe');
  }
  const label = parts.filter(nonempty).join(' / ');
  return (label || 'Recipe') + ' · ' + recipe.id;
}
