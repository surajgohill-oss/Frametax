import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildCountryHoverData, buildSingleJurisdictionUniverse } from "../src/lib/globeData.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

test("a contract record with no program_name still discloses the served program names on the hover", () => {
  const allocated = {
    jurisdiction_accounting: {
      single_jurisdiction_contract: [{
        jurisdiction_code: "CA-ON", jurisdiction_name: "Ontario", category: "LEADING_ALTERNATIVE", program_name: null,
        confirmed_npc_usd: 100, potential_npc_usd: 100, confirmed_incentive_usd: 10, potential_incentive_usd: 10,
      }],
    },
    best_per_jurisdiction: {
      "CA-ON": {
        structure_id: "s1", is_fully_priced: true, participants: ["CA-ON"], primary_jurisdiction: "CA-ON",
        npc_with_adjustments_usd: 100, selected_incentive_usd: 10, program_display_names: ["Federal credit", "Provincial credit"],
        segments: [{ jurisdiction_code: "CA-ON", program_slug: "x", claims_incentive: true }],
      },
    },
  };
  const hover = buildCountryHoverData(buildSingleJurisdictionUniverse(allocated), 1000).get("CA-ON");
  assert.equal(hover.contractRecord.program_name, null);
  assert.deepEqual(hover.programDisplayNames, ["Federal credit", "Provincial credit"]);
  const card = readFileSync(join(SRC, "components/GlobeHoverCard.jsx"), "utf8");
  const body = card.slice(card.indexOf("function SingleJurisdictionContractBody"), card.indexOf("function CoProductionBody"));
  assert.match(body, /hover\.programDisplayNames\?\.length \? hover\.programDisplayNames\.join\(" \+ "\)/, "the contract body must read the served program list");
});
