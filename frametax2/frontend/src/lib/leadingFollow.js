// A re-evaluation creates a new generation, and every structure in it has a NEW id. The server re-points the producer's selection to the same economic identity under that new id
// (Project.leading_structure_id changes), so a refetch serves a different persisted id than the one the UI last applied. The UI follows that re-pointing -- but only while the producer
// has NOT moved the selection since the previous served value was applied (current still equals it): a selection the producer made, cleared or changed in this visit always wins.
// Returns the id to apply, or null for "leave the selection alone".
export function followServedLeading({ prevServed, current, served }) {
  if (!served || !prevServed || served === prevServed) return null;
  return current === prevServed ? served : null;
}
