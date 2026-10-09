// Company Globe stage colour: the canonical production-stage mapping (lib/productionStageVisual.js) applied to a project's
// stage key (the same libraryStageKey the Library uses). Same hex in both app themes: it paints the dark globe stage.
import { libraryStageKey } from "./libraryStatus";
import { stageVisual, activeStageVisuals } from "./productionStageVisual";

export const activeStages = () => activeStageVisuals();
export const stageOf = (project) => stageVisual(libraryStageKey(project));
