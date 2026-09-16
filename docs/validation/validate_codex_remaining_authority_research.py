#!/usr/bin/env python3
"""Acceptance validator for the exhaustive gross-up authority closeout."""
from __future__ import annotations
import csv, hashlib, io, json, subprocess, sys
from pathlib import Path
import psycopg

P=Path(__file__).resolve().parent;ROOT=P.parents[1];ERR=[]
def bad(x):ERR.append(x)
def rows(name):
    path=P/name
    if not path.exists() or not path.stat().st_size:bad('missing/empty '+name);return []
    with path.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f);out=list(r)
        if not r.fieldnames or any(None in x for x in out):bad('CSV width/header '+name)
        return out
def ids(s):return {x for x in (s or '').split(';') if x}

def main():
    census=rows('CODEX_REINVESTMENT_GROSS_UP_INTERNAL_CENSUS.csv')
    cross=rows('CODEX_REINVESTMENT_GROSS_UP_RESEARCH_QUESTION_CROSSWALK.csv')
    questions=rows('CODEX_REMAINING_AUTHORITY_QUESTIONS.csv')
    auth=rows('CODEX_REINVESTMENT_GROSS_UP_AUTHORITY_RESEARCH.csv')
    disp=rows('CODEX_REINVESTMENT_GROSS_UP_ECONOMIC_DISPOSITIONS.csv')
    stack=rows('CODEX_31_STACKING_AUTHORITY_RESOLUTION.csv')
    nodes=rows('CODEX_90_NODE_STRUCTURAL_SCOPE_RESOLUTION.csv')
    checks=rows('CODEX_AUTHORITY_RESEARCH_MANUAL_CHECKS.csv')
    examples=rows('CODEX_REINVESTMENT_GROSS_UP_WORKED_EXAMPLES.csv')
    conflicts=rows('CODEX_REINVESTMENT_GROSS_UP_CONFLICTS.csv')
    slog=[]
    for i,line in enumerate((P/'CODEX_REINVESTMENT_GROSS_UP_SOURCE_LOG.jsonl').read_text().splitlines(),1):
        try:slog.append(json.loads(line))
        except Exception as e:bad(f'source JSON line {i}: {e}')
    smap={s['retrieval_id']:s for s in slog}
    if len(smap)!=len(slog):bad('duplicate retrieval IDs')
    for s in slog:
        excerpt=s.get('short_verified_excerpt') or s.get('short_excerpt_present_in_content','')
        if not excerpt or not s.get('exact_locator'):bad('source lacks verified excerpt/locator '+s.get('retrieval_id',''))
        expected=s.get('content_sha256') or s.get('extracted_content_sha256')
        if expected!=hashlib.sha256(excerpt.encode()).hexdigest():bad('source hash mismatch '+s['retrieval_id'])
        if int(s.get('content_length',-1))!=len(excerpt):bad('source length mismatch '+s['retrieval_id'])
        if 'search_query' in s.get('final_url','') or 'google.com/search' in s.get('final_url',''):bad('search result used as source '+s['retrieval_id'])

    cids={x['record_id'] for x in census};qids={x['question_id'] for x in questions}
    if len(census)!=1250 or len(cids)!=1250:bad('locked physical census is not 1,250 unique rows')
    if len(cross)!=1250 or {x['physical_record_id'] for x in cross}!=cids:bad('physical crosswalk incomplete')
    if len({x['physical_record_id'] for x in cross})!=len(cross):bad('physical record maps more than once')
    if not qids or any(x['unique_research_question_id'] not in qids for x in cross):bad('crosswalk references missing question')
    if {x['unique_research_question_id'] for x in cross}!=qids:bad('question ledger contains omitted/unmapped question')
    cmap={x['record_id']:x for x in census}
    for x in cross:
        c=cmap[x['physical_record_id']]
        if c.get('unique_research_question_id')!=x['unique_research_question_id'] or c.get('final_authority_disposition')!=x['final_disposition']:bad('census/crosswalk inheritance mismatch '+x['physical_record_id'])
    allowed={'QPE_GROSS_UP_AUTHORIZED','QPE_FMV_AUTHORIZED_WITH_CONDITIONS','QPE_CASH_PAID_ONLY','COST_ONLY_GROSS_UP','FINANCING_SOURCE_ONLY','NON_QPE_SUPPORT','NPC_REDUCTION_ONLY','CONDITIONAL_NPC_REDUCTION','QPE_REDUCTION','SPEND_REDUCTION','AGGREGATE_AID_LIMIT','SAME_COST_PROHIBITED_DISTINCT_COST_ALLOWED','MUTUALLY_EXCLUSIVE','SELECTIVE_CONDITIONAL_UPSIDE','EXCLUDED','INACTIVE_OR_SUPERSEDED','DUPLICATE_OR_ALIAS','AUTHORITY_SILENT_AGENCY_RULING_REQUIRED'}
    primary={s['retrieval_id'] for s in slog if s.get('source_classification') in {'PRIMARY_OFFICIAL','PRIMARY_OFFICIAL_RECOVERED'}}
    for q in questions:
        if q['final_disposition'] not in allowed:bad('invalid question disposition '+q['question_id'])
        r=ids(q['supporting_retrieval_ids'])
        if not r or r-smap.keys():bad('question missing/unknown retrieval '+q['question_id'])
        if q['final_disposition']=='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED':
            if len(q['agency_ruling_language'])<40 or not q['safe_implementation_behavior']:bad('imprecise agency ruling '+q['question_id'])
        if q['final_disposition'] in {'QPE_GROSS_UP_AUTHORIZED','QPE_FMV_AUTHORIZED_WITH_CONDITIONS','QPE_CASH_PAID_ONLY','EXCLUDED'} and not (r&primary):bad('resolved QPE/exclusion lacks opened official source '+q['question_id'])
        if q['final_disposition']=='SELECTIVE_CONDITIONAL_UPSIDE' and 'guaranteed' in q['safe_implementation_behavior'].lower():bad('selective fund guaranteed '+q['question_id'])
        if q['question_type']=='TRAVEL' and (not q['ordinary_cash_paid_treatment'] or not q['contributed_in_kind_treatment']):bad('cash/contributed travel conflated '+q['question_id'])

    for name,data in [('authority',auth),('disposition',disp)]:
        if len(data)!=1250 or {x['record_id'] for x in data}!=cids:bad(name+' row parity')
    dmap={x['record_id']:x for x in disp}
    for x in cross:
        if dmap[x['physical_record_id']]['economic_disposition']!=x['final_disposition']:bad('inherited disposition mismatch '+x['physical_record_id'])
    positive={'QPE_GROSS_UP_AUTHORIZED','QPE_FMV_AUTHORIZED_WITH_CONDITIONS','COST_ONLY_GROSS_UP'}
    for d in disp:
        if d['economic_disposition'] in positive:
            if not (ids(d['source_retrieval_ids'])&primary):bad('gross-up inferred without official authority '+d['record_id'])
            if not d['valuation_source'] or 'once' not in d['double_count_prevention_rule'].lower():bad('gross-up valuation/offset missing '+d['record_id'])

    raw=subprocess.check_output(['git','show','e7c8c28da5f8977f97e4a571241a9f5e382f5127:docs/validation/CODEX_31_STACKING_AUTHORITY_RESOLUTION.csv'],cwd=ROOT,text=True)
    expected={r['interaction_id'] for r in csv.DictReader(io.StringIO(raw)) if r['disposition'].startswith('UNRESOLVED')}
    if len(stack)!=31:bad('31 interaction row count')
    original_gaps=[s for s in stack if s['interaction_id'] in expected]
    if len(original_gaps)!=11:bad('original 11 pair-gap coverage')
    for s in original_gaps:
        if s['disposition'].startswith('UNRESOLVED'):bad('generic unresolved stacking remains '+s['interaction_id'])
        if s['disposition']=='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED' and len(s['unresolved_facts'])<80:bad('stack agency question imprecise '+s['interaction_id'])
        if s['disposition']!='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED' and (not ids(s['authority']) or ids(s['authority'])-smap.keys()):bad('resolved stack lacks source-log authority '+s['interaction_id'])
    if len(nodes)!=90 or len({n['node_id'] for n in nodes})!=90:bad('90 node coverage')
    prior_nodes=subprocess.check_output(['git','show','e7c8c28da5f8977f97e4a571241a9f5e382f5127:docs/validation/CODEX_90_NODE_STRUCTURAL_SCOPE_RESOLUTION.csv'],cwd=ROOT,text=True)
    prior_required={n['node_id'] for n in csv.DictReader(io.StringIO(prior_nodes)) if n['classification']=='AUTHORITY_RESEARCH_REQUIRED'}
    current_required=[n for n in nodes if n['node_id'] in prior_required]
    if len(prior_required)!=69 or len(current_required)!=69 or any(not n.get('final_authority_disposition') for n in current_required):bad('69 structural-node closeout accounting')
    former=[n for n in current_required if n.get('final_authority_disposition')=='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED']
    for n in former:
        if len(n.get('exact_agency_ruling_question',''))<100 or not n.get('safe_implementation_behavior'):bad('node agency question imprecise '+n['node_id'])
    for n in current_required:
        if n.get('final_authority_disposition')=='POSITIVE_STRUCTURAL_SCOPE_CONFIRMED' and not (ids(n.get('supporting_retrieval_ids',''))&primary):
            bad('positive structural conclusion lacks opened official source '+n['node_id'])

    checked={x['record_id'] for x in checks}
    if not cids.issubset(checked):bad('manual physical checks incomplete')
    if not {'STACK:'+x['interaction_id'] for x in stack}.issubset(checked):bad('manual stack checks incomplete')
    if not {'NODE:'+x['node_id'] for x in nodes}.issubset(checked):bad('manual node checks incomplete')
    corpus='\n'.join((P/f).read_text(errors='replace') for f in ['CODEX_REINVESTMENT_GROSS_UP_AUTHORITY_RESEARCH.csv','CODEX_REINVESTMENT_GROSS_UP_ECONOMIC_DISPOSITIONS.csv','CODEX_REMAINING_AUTHORITY_QUESTIONS.csv','CODEX_AUTHORITY_IMPLEMENTATION_HANDOFF.md'])
    legacy='AUTHORITY'+'_'+'BLOCKED'
    if legacy in corpus:bad('legacy generic blocker label remains')
    if not conflicts or len(examples)!=8:bad('conflict/example artifacts incomplete')
    hand=(P/'CODEX_AUTHORITY_IMPLEMENTATION_HANDOFF.md').read_text()
    if 'GROSS_UP_AUTHORITY_RESEARCH_EXHAUSTIVELY_CLOSED_READY_FOR_IMPLEMENTATION' not in hand:bad('handoff status missing')

    with psycopg.connect('postgresql://frametax:frametax@localhost:5432/frametax2') as cn,cn.cursor() as cur:
        cur.execute("select count(*) from qualifying_spend_categories where spend_category in ('deferment','in_kind','reinvestment','equity_participation','travel','lodging','btl_transportation','btl_equipment_rental','btl_stage_facility','btl_location_fees','vessel_marine')");a=cur.fetchone()[0]
        cur.execute("select count(*) from program_spend_treatments where labor_type in ('travel','accommodation_lodging','per_diem','customs_imports','marine_vessel')");b=cur.fetchone()[0]
        cur.execute('select count(*) from fund_economics');c=cur.fetchone()[0]
        cur.execute('select count(*) from production_contributions');d=cur.fetchone()[0]
    if a+b+c+11!=1250 or d!=0:bad('database census drift')

    if ERR:
        print('VALIDATION: FAIL');print('\n'.join('- '+e for e in ERR));return 1
    agency=sum(q['final_disposition']=='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED' for q in questions)+sum(s['disposition']=='AUTHORITY_SILENT_AGENCY_RULING_REQUIRED' for s in original_gaps)+len(former)
    print('VALIDATION: PASS')
    print(f'physical={len(census)} questions={len(questions)} sources={len(slog)} primary={len(primary)} stacking={len(stack)} structural_nodes={len(nodes)} agency_questions={agency} manual_checks={len(checks)}')
    return 0
if __name__=='__main__':sys.exit(main())
