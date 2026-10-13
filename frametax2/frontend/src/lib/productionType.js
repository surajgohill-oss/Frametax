// The production type label for display, derived ONLY from the served view (`production.production_type`): the stated option's own label, or an honest "not stated". The identity header
// used to print a hard-coded "Feature Film" for every production regardless of what the producer stated; nothing is defaulted here.
export function productionTypeLabel(productionType) {
  if (!productionType) return null;
  if (productionType.state !== "STATED") return "Production type not stated";
  const option = (productionType.options || []).find((o) => o.format === productionType.format);
  return option ? option.label : productionType.format;
}
