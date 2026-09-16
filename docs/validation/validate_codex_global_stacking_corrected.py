#!/usr/bin/env python3
"""Semantic acceptance gate for the corrected global stacking audit.

This validator intentionally rejects the methodology errors in the superseded
oracle.  It reads artifacts only; it does not import or mutate production data.
"""
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

def rows(name):
    with open(HERE / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def require(ok, message):
    if not ok:
        raise AssertionError(message)

nodes = rows('CODEX_GLOBAL_PROGRAM_SCOPE_NODES.csv')
pairs = rows('CODEX_GLOBAL_ALL_PAIRS_CLASSIFIED.csv')
legal = rows('CODEX_LEGAL_COMPATIBILITY_ORACLE.csv')
arch = rows('CODEX_STRUCTURAL_COMPONENT_ARCHETYPES.csv')
treaties = rows('CODEX_TREATY_STACKING_ORACLE.csv')
higher = rows('CODEX_HIGHER_ORDER_STACKING_ORACLE.csv')
evidence = rows('CODEX_STACKING_AUTHORITY_EVIDENCE_CORRECTED.csv')
registry = rows('CODEX_STACKING_REGISTRY_RECONCILIATION.csv')
gaps = rows('CODEX_STACKING_RUNTIME_GAPS_CORRECTED.csv')
calcs = rows('CODEX_STACKING_CALCULATION_CONTROLS_CORRECTED.csv')
manual = rows('CODEX_GLOBAL_STACKING_MANUAL_CHECKS.csv')

node = {r['program_id']: r for r in nodes}
require(len(nodes) == len(node) == 126, 'exact 126-node census required')
require(len(pairs) == 7875 and len({r['pair_id'] for r in pairs}) == 7875, 'exact unordered Cartesian index required')
allowed_classes = {
 'LEGAL_COMPATIBILITY_REVIEW_REQUIRED','STRUCTURAL_COMPONENT_COMBINATION_POSSIBLE',
 'TREATY_RELATIONSHIP_REQUIRED','NO_DIRECT_STACKING_RELATIONSHIP',
 'SAME_ECONOMIC_IDENTITY_OR_ROUTE','SCOPE_INCOMPATIBLE','INSUFFICIENT_SCOPE_DATA'}
require({r['classification'] for r in pairs} <= allowed_classes, 'invalid all-pair classification')
require(all(r['positive_legal_conclusion']=='NO' for r in pairs), 'Cartesian index may not assert legal stacking')

# Positive scope cannot be inferred from UNCLASSIFIED.
for r in nodes:
    if r['positive_structural_use_permitted'] == 'YES':
        require(r['component_scope'] != 'UNCLASSIFIED' and r['source_status'] != 'SCOPE_UNCLASSIFIED_NOT_POSITIVE', f'unsupported positive scope: {r["program_id"]}')
    if r['source_status'] == 'SCOPE_UNCLASSIFIED_NOT_POSITIVE':
        require(r['positive_structural_use_permitted'] == 'NO', f'unclassified node promoted: {r["program_id"]}')

# Every resolved legal disposition needs exact interaction evidence; route
# identity is also evidenced rather than merely asserted.
ev = {r['evidence_id']: r for r in evidence}
require(len(ev) == len(evidence), 'duplicate evidence IDs')
positive = [r for r in legal if r['disposition'] != 'UNRESOLVED']
for r in positive:
    require(r['evidence_id'] in ev, f'resolved legal row lacks evidence: {r["interaction_id"]}')
    e = ev[r['evidence_id']]
    require(e['interaction_id'] == r['interaction_id'], 'evidence attached to unrelated interaction')
    require(e['program_a'] == r['program_a'] and e['program_b'] == r['program_b'], 'evidence/program mismatch')
    require(e['source_url'].startswith('https://'), 'legal evidence requires exact URL')
    require(e['document_title'] and e['exact_locator'] and e['supporting_excerpt'] and e['supported_fact'] and e['interpretation'], 'incomplete authority evidence')
require(any(r['disposition']=='UNRESOLVED' for r in legal), 'zero unresolved is not credible without complete evidence')

# Reject copied generic evidence across unrelated pairs.
generic = Counter(r['supporting_excerpt'].strip().lower() for r in evidence)
require(max(generic.values(), default=0) <= 3, 'identical generic evidence repeated across unrelated pairs')

# Structural rows must use real nodes and confirmed scope examples.
for r in arch:
    require(r['acceptance_status']=='ACCEPTED_ARCHETYPE' and r['scope_validation']=='PASS', f'unaccepted archetype: {r["archetype_id"]}')
    progs=[x.strip() for x in r['canonical_example_programs'].split(' | ')]
    require(all(x in node for x in progs), f'invented program in archetype: {r["archetype_id"]}')
    require(r['allocation_rule'].startswith('Each source budget line is allocated once'), 'missing one-line/one-program allocation rule')
require(len(arch)==12, 'all twelve required archetypes required')

# Treaty oracle must correspond exactly to registered frameworks and must not
# turn arbitrary foreign pairs into treaty relationships.
require(len(treaties)==29 and len({r['treaty_id'] for r in treaties})==29, 'registered 26 bilateral + 3 multilateral frameworks required')
require(all(r['acceptance_status']=='REGISTERED_FRAMEWORK_CONDITIONAL' for r in treaties), 'treaty framework incorrectly made unconditional')

# Explicit allocation and real program identities are mandatory.  Size claims
# must match rows and the four-program claim must have an actual size-four row.
for r in higher:
    ps=r['programs'].split(' | '); alloc=r['exact_component_allocation'].split(' | ')
    require(int(r['combination_size']) == len(ps) == len(alloc), f'size/allocation mismatch: {r["combination_id"]}')
    require(all(x in node for x in ps), f'invented higher-order program: {r["combination_id"]}')
    require(len({x.split(':',1)[0] for x in alloc})==len(alloc), f'route double count: {r["combination_id"]}')
    require(r['minimum_spend_feasible']=='YES', f'infeasible threshold: {r["combination_id"]}')
    require(all(float(x.rsplit(':',1)[1])>0 for x in alloc), f'nonpositive allocation: {r["combination_id"]}')
require(any(r['combination_size']=='4' for r in higher), 'claimed size-four universe has no size-four row')
require(not any(r['combination_size']=='5' for r in higher), 'unsupported size-five claim')

# Real-project omissions require the full trigger record. Isolated controls are
# not silently converted into four-project findings.
for r in gaps:
    if r['classification']=='PROVEN_RUNTIME_OMISSION':
        require(r['trigger_type']=='REAL_PROJECT' and r['project_or_control']=='Lips Like Sugar', 'invalid real-project trigger')
        require(r['scope_match']=='PASS' and r['minimum_spend_test'].startswith('PASS') and r['runtime_result']=='SILENTLY_OMITTED', 'unproven runtime omission')
    if r['trigger_type']=='ISOLATED_CANONICAL_CONTROL':
        require(r['classification']=='ISOLATED_CONTROL_REQUIRED', 'isolated control mislabeled as runtime omission')
require(sum(r['classification']=='REGISTERED_CONTROL_NOT_CONSUMED' for r in gaps)==5, 'five missing executable registered controls not preserved')
require(sum(r['classification']=='REGISTERED_CONTROL_GENERATED' for r in gaps)==1, 'generated executable registered control not preserved')

# No generic/hypothetical program or rate controls; arithmetic must recompute.
for r in calcs:
    require(r['program_a'] in node and r['program_b'] in node, f'noncanonical calculation identity: {r["control_id"]}')
    require('generic' not in (r['program_a']+r['program_b']).lower() and 'hypothetical' not in (r['program_a']+r['program_b']).lower(), 'generic/hypothetical calculation')
    qa,qb,ra,rb=[float(r[x]) for x in ('qpe_a_usd','qpe_b_usd','rate_a','rate_b')]
    rates_a={float(x.strip()) for x in node[r['program_a']]['canonical_rate_set'].split(' | ') if x.strip()}
    rates_b={float(x.strip()) for x in node[r['program_b']]['canonical_rate_set'].split(' | ') if x.strip()}
    require(ra in rates_a and rb in rates_b, f'invented/noncanonical rate: {r["control_id"]}')
    red,cond=float(r['reductions_usd']),float(r['conditional_upside_usd'])
    expected=qa*ra+qb*rb-red-cond
    require(abs(expected-float(r['expected_guaranteed_incentive_usd'])) < .01, f'calculation mismatch: {r["control_id"]}')
    require(abs((float(r['project_budget_usd'])-expected)-float(r['expected_npc_usd'])) < .01, f'NPC mismatch: {r["control_id"]}')
    require(r['program_identity_check']=='REAL_CANONICAL_PROGRAMS' and r['result']=='PASS', 'calculation not accepted')

# Every existing rule exactly once; all six executable controls preserved.
require(len(registry)==229 and len({r['registry_row_id'] for r in registry})==229, 'all 229 rules must be reconciled once')
controls={
 'ca_bc_pstc::ca_federal_cptc','ca_federal_cptc::on_ofttc','ca_federal_cptc::on_opstc',
 'ie_section_481::uk_avec','ny_state_film::us_ny_post_production_credit','on_ofttc::on_opstc'}
require(controls <= {r['canonical_pair_id'] for r in registry if r['both_126_nodes']=='YES'}, 'executable registered control omitted')
ny=next(r for r in registry if r['canonical_pair_id']=='ny_state_film::us_ny_post_production_credit')
require(ny['corrected_disposition']=='SAME_COST_PROHIBITED_DISTINCT_COSTS_ALLOWED', 'New York disposition not corrected')

# Alias/election routes cannot be summed in accepted higher-order controls.
for r in higher:
    groups=[node[x]['election_route_group'] for x in r['programs'].split(' | ') if node[x]['election_route_group']]
    require(len(groups)==len(set(groups)), f'election route double-counted: {r["combination_id"]}')

# Manual acceptance coverage.
mc=Counter(r['category'] for r in manual if r['result']=='PASS')
require(mc['SAME_JURISDICTION']>=10 and mc['NATIONAL_SUBNATIONAL']>=10 and mc['CROSS_JURISDICTION_OR_ARCHETYPE']>=10, 'manual interaction samples incomplete')
require(mc['EXECUTABLE_REGISTERED_PAIR']==6 and mc['TREATY_PLUS_COMPONENT']>=1 and mc['HIGHER_ORDER']>=10, 'manual oracle coverage incomplete')
require(mc['CALCULATION_CONTROL']==len(calcs), 'not every calculation manually checked')

summary={
 'status':'PASS','nodes':len(nodes),'all_pairs':len(pairs),'legal_interactions':len(legal),
 'authority_supported':len(positive),'authority_unresolved':sum(r['disposition']=='UNRESOLVED' for r in legal),
 'structural_archetypes':len(arch),'treaty_frameworks':len(treaties),
 'higher_by_size':dict(Counter(r['combination_size'] for r in higher)),
 'real_project_runtime_omissions':sum(r['classification']=='PROVEN_RUNTIME_OMISSION' for r in gaps),
 'isolated_controls':sum(r['classification']=='ISOLATED_CONTROL_REQUIRED' for r in gaps),
 'calculation_controls':len(calcs),'manual_checks':len(manual),'registered_rules':len(registry)}
print(json.dumps(summary, indent=2, sort_keys=True))
