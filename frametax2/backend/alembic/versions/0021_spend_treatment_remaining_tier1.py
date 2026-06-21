"""0021 — ProgramSpendTreatment for 11 remaining Tier-1 programs.

Programs: ca_federal_cptc, on_ofttc, fr_trip, it_tax_credit_foreign,
mu_edb_incentive, nm_film_production, or_opif, nohfc_production_fund,
cy_film_rebate, hr_cash_rebate, hu_hipa_rebate.

Treatment notes by program type:
  CPTC — labour credit (QCLE only). Non-labour production costs do not
    qualify. Non-resident/foreign labour excluded from QCLE.
  OFTTC — Ontario labour credit. Non-resident/foreign labour UNKNOWN.
  NM, OR — ATL QUALIFIES (both states explicitly include ATL).
  FR, IT, CY, HR, HU — geography-based; all local spend QUALIFIES.
  NOHFC — discretionary grant; most categories QUALIFIES for application.
  MU — mostly UNKNOWN pending primary source confirmation.

Revision ID: 0021
Revises: 0020
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0021-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_CUSTOMS_UNKNOWN = (
    "Customs/import duties treatment unconfirmed from primary source."
)

_TREATMENTS: list[tuple[str, str, bool | None, str, str]] = [

    # -----------------------------------------------------------------------
    # ca_federal_cptc — Canadian Film or Video Production Tax Credit.
    # QCLE = qualified CANADIAN LABOUR expenditure paid to Canadian-resident
    # individuals. Non-labour costs (travel, insurance, equipment) do not
    # qualify. Non-resident and foreign labour excluded from QCLE.
    # -----------------------------------------------------------------------
    ("ca_federal_cptc", "atl_writer",          True,  "ATL writer fees qualify as QCLE under CPTC if paid to Canadian-resident individuals performing work in Canada.", "PARSED"),
    ("ca_federal_cptc", "atl_director",        True,  "ATL director fees qualify as QCLE under CPTC if paid to Canadian-resident individuals.", "PARSED"),
    ("ca_federal_cptc", "atl_producer",        True,  "ATL producer fees qualify as QCLE under CPTC if paid to Canadian-resident individuals.", "PARSED"),
    ("ca_federal_cptc", "atl_cast_principal",  True,  "Principal cast fees qualify as QCLE under CPTC if paid to Canadian-resident individuals.", "PARSED"),
    ("ca_federal_cptc", "atl_cast_supporting", True,  "Supporting cast fees qualify as QCLE under CPTC if paid to Canadian-resident individuals.", "PARSED"),
    ("ca_federal_cptc", "btl_crew_resident",   True,  "Canadian-resident BTL crew are the primary QCLE category under CPTC.", "PARSED"),
    ("ca_federal_cptc", "btl_crew_non_resident", False, "Non-resident BTL crew do not qualify as QCLE under CPTC. CPTC is a Canadian labour credit; residency is required.", "PARSED"),
    ("ca_federal_cptc", "btl_crew_foreign",    False, "Foreign BTL crew do not qualify as QCLE under CPTC. Only Canadian-resident individuals qualify.", "PARSED"),
    ("ca_federal_cptc", "travel",              False, "Travel costs are not QCLE under CPTC. CPTC is a labour-only credit — non-labour production costs do not qualify.", "PARSED"),
    ("ca_federal_cptc", "accommodation_lodging", False, "Accommodation is not QCLE under CPTC. Non-labour production costs do not contribute to the credit base.", "PARSED"),
    ("ca_federal_cptc", "per_diem",            False, "Per diem is not QCLE under CPTC. Only salary and wages paid to Canadian-resident individuals qualify.", "PARSED"),
    ("ca_federal_cptc", "insurance",           False, "Production insurance is not QCLE under CPTC. Non-labour costs do not contribute to the credit.", "PARSED"),
    ("ca_federal_cptc", "completion_bond",     False, "Completion bond is not QCLE under CPTC. Non-labour production cost.", "PARSED"),
    ("ca_federal_cptc", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("ca_federal_cptc", "marine_vessel",       False, "Marine vessel hire is not QCLE under CPTC. Equipment and facility costs do not qualify.", "PARSED"),
    ("ca_federal_cptc", "vfx",                 True,  "Canadian-resident VFX labour qualifies as QCLE under CPTC. Only the labour component qualifies — equipment/software costs do not.", "PARSED"),
    ("ca_federal_cptc", "post_production",     True,  "Canadian-resident post-production labour qualifies as QCLE under CPTC.", "PARSED"),
    ("ca_federal_cptc", "animation",           True,  "Canadian-resident animation labour qualifies as QCLE under CPTC.", "PARSED"),
    ("ca_federal_cptc", "music",               True,  "Canadian-resident music composition and performance labour qualifies as QCLE under CPTC.", "PARSED"),
    ("ca_federal_cptc", "legal_accounting",    False, "Legal and accounting fees are not QCLE under CPTC. Non-labour professional fees do not qualify.", "PARSED"),
    ("ca_federal_cptc", "customs_imports",     False, "Customs/import costs are not QCLE under CPTC. Non-labour production costs.", "PARSED"),

    # -----------------------------------------------------------------------
    # on_ofttc — Ontario Film and Television Tax Credit.
    # Ontario labour expenditure (OLAE) credit for domestic Canadian content.
    # ATL qualifies as Ontario labour for domestic productions.
    # Non-resident/foreign crew UNKNOWN — OFTTC requires Ontario labour.
    # -----------------------------------------------------------------------
    ("on_ofttc", "atl_writer",          True,  "ATL writer fees qualify as OLAE under OFTTC for Ontario domestic content productions.", "PARSED"),
    ("on_ofttc", "atl_director",        True,  "ATL director fees qualify as OLAE under OFTTC for Ontario domestic content productions.", "PARSED"),
    ("on_ofttc", "atl_producer",        True,  "ATL producer fees qualify as OLAE under OFTTC for Ontario domestic content productions.", "PARSED"),
    ("on_ofttc", "atl_cast_principal",  True,  "Principal cast fees qualify as OLAE under OFTTC if work performed in Ontario.", "PARSED"),
    ("on_ofttc", "atl_cast_supporting", True,  "Supporting cast fees qualify as OLAE under OFTTC if work performed in Ontario.", "PARSED"),
    ("on_ofttc", "btl_crew_resident",   True,  "Ontario-resident BTL crew are the primary OLAE category under OFTTC.", "PARSED"),
    ("on_ofttc", "btl_crew_non_resident", None, "Non-resident BTL crew treatment under OFTTC unconfirmed. OFTTC is an Ontario labour credit; non-resident eligibility requires Ontario Creates confirmation.", "DISCOVERY"),
    ("on_ofttc", "btl_crew_foreign",    None,  "Foreign BTL crew treatment under OFTTC unconfirmed from Ontario Creates primary source.", "DISCOVERY"),
    ("on_ofttc", "travel",              True,  "Ontario travel expenditure qualifies as OLAE under OFTTC.", "PARSED"),
    ("on_ofttc", "accommodation_lodging", True, "Ontario accommodation qualifies as OLAE under OFTTC.", "PARSED"),
    ("on_ofttc", "per_diem",            True,  "Per diem costs incurred in Ontario qualify under OFTTC.", "PARSED"),
    ("on_ofttc", "insurance",           True,  "Ontario-sourced production insurance qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "completion_bond",     True,  "Completion bond costs qualify under OFTTC.", "PARSED"),
    ("on_ofttc", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("on_ofttc", "marine_vessel",       True,  "Marine vessel hire in Ontario qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "vfx",                 True,  "Ontario VFX labour qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "post_production",     True,  "Ontario post-production labour qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "animation",           True,  "Ontario animation labour qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "music",               True,  "Ontario music expenditure qualifies under OFTTC.", "PARSED"),
    ("on_ofttc", "legal_accounting",    True,  "Ontario legal and accounting costs qualify under OFTTC.", "PARSED"),
    ("on_ofttc", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # fr_trip — France CNC TRIP (Crédit d'impôt international).
    # Geography-based: all qualifying French spend qualifies.
    # -----------------------------------------------------------------------
    ("fr_trip", "atl_writer",          True,  "ATL writer fees for French-incurred work qualify under France TRIP.", "PARSED"),
    ("fr_trip", "atl_director",        True,  "ATL director fees for French-incurred work qualify under France TRIP.", "PARSED"),
    ("fr_trip", "atl_producer",        True,  "ATL producer fees for French-incurred work qualify under France TRIP.", "PARSED"),
    ("fr_trip", "atl_cast_principal",  True,  "Principal cast fees for French-incurred work qualify under France TRIP.", "PARSED"),
    ("fr_trip", "atl_cast_supporting", True,  "Supporting cast fees for French-incurred work qualify under France TRIP.", "PARSED"),
    ("fr_trip", "btl_crew_resident",   True,  "French resident BTL crew qualify under France TRIP.", "PARSED"),
    ("fr_trip", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in France qualify under TRIP (geography-based).", "PARSED"),
    ("fr_trip", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in France qualify under TRIP.", "PARSED"),
    ("fr_trip", "travel",              True,  "French travel expenditure qualifies under TRIP.", "PARSED"),
    ("fr_trip", "accommodation_lodging", True, "French accommodation qualifies under TRIP.", "PARSED"),
    ("fr_trip", "per_diem",            True,  "Per diem costs incurred in France qualify under TRIP.", "PARSED"),
    ("fr_trip", "insurance",           True,  "French-sourced production insurance qualifies under TRIP.", "PARSED"),
    ("fr_trip", "completion_bond",     True,  "Completion bond costs qualify under TRIP.", "PARSED"),
    ("fr_trip", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("fr_trip", "marine_vessel",       True,  "Marine vessel hire in France qualifies under TRIP.", "PARSED"),
    ("fr_trip", "vfx",                 True,  "French VFX expenditure qualifies under TRIP.", "PARSED"),
    ("fr_trip", "post_production",     True,  "French post-production qualifies under TRIP.", "PARSED"),
    ("fr_trip", "animation",           True,  "French animation qualifies under TRIP.", "PARSED"),
    ("fr_trip", "music",               True,  "French music expenditure qualifies under TRIP.", "PARSED"),
    ("fr_trip", "legal_accounting",    True,  "French legal and accounting costs qualify under TRIP.", "PARSED"),
    ("fr_trip", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # it_tax_credit_foreign — Italy Tax Credit for Foreign Productions.
    # Geography-based: all qualifying Italian spend qualifies.
    # -----------------------------------------------------------------------
    ("it_tax_credit_foreign", "atl_writer",          True,  "ATL writer fees for Italian-incurred work qualify under Italy tax credit (DGCinema).", "PARSED"),
    ("it_tax_credit_foreign", "atl_director",        True,  "ATL director fees for Italian-incurred work qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "atl_producer",        True,  "ATL producer fees for Italian-incurred work qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "atl_cast_principal",  True,  "Principal cast fees for Italian-incurred work qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "atl_cast_supporting", True,  "Supporting cast fees for Italian-incurred work qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "btl_crew_resident",   True,  "Italian resident BTL crew qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Italy qualify (geography-based).", "PARSED"),
    ("it_tax_credit_foreign", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Italy qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "travel",              True,  "Italian travel expenditure qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "accommodation_lodging", True, "Italian accommodation qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "per_diem",            True,  "Per diem costs incurred in Italy qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "insurance",           True,  "Italian-sourced production insurance qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "completion_bond",     True,  "Completion bond costs qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("it_tax_credit_foreign", "marine_vessel",       True,  "Marine vessel hire in Italy qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "vfx",                 True,  "Italian VFX expenditure qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "post_production",     True,  "Italian post-production qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "animation",           True,  "Italian animation qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "music",               True,  "Italian music expenditure qualifies under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "legal_accounting",    True,  "Italian legal and accounting costs qualify under Italy tax credit.", "PARSED"),
    ("it_tax_credit_foreign", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # mu_edb_incentive — Mauritius EDB Film Rebate Scheme.
    # DISCOVERY tier — most treatment categories UNKNOWN pending
    # EDB primary source confirmation.
    # -----------------------------------------------------------------------
    ("mu_edb_incentive", "atl_writer",          None,  "ATL writer treatment under Mauritius EDB rebate unconfirmed from EDB primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "atl_director",        None,  "ATL director treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "atl_producer",        None,  "ATL producer treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "atl_cast_principal",  None,  "Principal cast treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "atl_cast_supporting", None,  "Supporting cast treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "btl_crew_resident",   None,  "BTL crew treatment under Mauritius EDB rebate unconfirmed. Mauritius EDB likely covers local Mauritius labor but not confirmed.", "DISCOVERY"),
    ("mu_edb_incentive", "btl_crew_non_resident", None, "Non-resident crew treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "btl_crew_foreign",    None,  "Foreign crew treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "travel",              None,  "Travel expenditure treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "accommodation_lodging", None, "Accommodation treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "per_diem",            None,  "Per diem treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "insurance",           None,  "Insurance treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "completion_bond",     None,  "Completion bond treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("mu_edb_incentive", "marine_vessel",       None,  "Marine vessel treatment under Mauritius EDB rebate unconfirmed. Mauritius has marine filming locations but eligibility not confirmed.", "DISCOVERY"),
    ("mu_edb_incentive", "vfx",                 None,  "VFX treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "post_production",     None,  "Post-production treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "animation",           None,  "Animation treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "music",               None,  "Music treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "legal_accounting",    None,  "Legal and accounting treatment under Mauritius EDB rebate unconfirmed from primary source.", "DISCOVERY"),
    ("mu_edb_incentive", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # nm_film_production — New Mexico Film Production Tax Credit.
    # ATL explicitly qualifies. One of three US states (GA, LA, NM) where
    # ATL labor is eligible for the film credit.
    # -----------------------------------------------------------------------
    ("nm_film_production", "atl_writer",          True,  "ATL writer fees incurred in New Mexico explicitly qualify under NM film production tax credit.", "PARSED"),
    ("nm_film_production", "atl_director",        True,  "ATL director fees incurred in New Mexico explicitly qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "atl_producer",        True,  "ATL producer fees incurred in New Mexico explicitly qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "atl_cast_principal",  True,  "Principal cast fees incurred in New Mexico qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "atl_cast_supporting", True,  "Supporting cast fees incurred in New Mexico qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "btl_crew_resident",   True,  "NM resident BTL crew qualify under NM film production tax credit.", "PARSED"),
    ("nm_film_production", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in New Mexico qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in New Mexico qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "travel",              True,  "New Mexico travel expenditure qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "accommodation_lodging", True, "New Mexico accommodation qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "per_diem",            True,  "Per diem costs incurred in New Mexico qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "insurance",           True,  "New Mexico production insurance qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "completion_bond",     True,  "Completion bond costs qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("nm_film_production", "marine_vessel",       True,  "Marine vessel hire in New Mexico qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "vfx",                 True,  "New Mexico VFX expenditure qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "post_production",     True,  "New Mexico post-production qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "animation",           True,  "New Mexico animation qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "music",               True,  "New Mexico music expenditure qualifies under NM film credit.", "PARSED"),
    ("nm_film_production", "legal_accounting",    True,  "New Mexico legal and accounting costs qualify under NM film credit.", "PARSED"),
    ("nm_film_production", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # or_opif — Oregon Production Investment Fund (OPIF).
    # 20% rebate on qualifying Oregon production expenditures.
    # Oregon explicitly includes ATL in qualifying spend.
    # -----------------------------------------------------------------------
    ("or_opif", "atl_writer",          True,  "ATL writer fees incurred in Oregon qualify under Oregon OPIF rebate. Oregon explicitly includes ATL in qualifying production expenditure.", "PARSED"),
    ("or_opif", "atl_director",        True,  "ATL director fees incurred in Oregon qualify under Oregon OPIF rebate.", "PARSED"),
    ("or_opif", "atl_producer",        True,  "ATL producer fees incurred in Oregon qualify under Oregon OPIF rebate.", "PARSED"),
    ("or_opif", "atl_cast_principal",  True,  "Principal cast fees incurred in Oregon qualify under Oregon OPIF rebate.", "PARSED"),
    ("or_opif", "atl_cast_supporting", True,  "Supporting cast fees incurred in Oregon qualify under Oregon OPIF rebate.", "PARSED"),
    ("or_opif", "btl_crew_resident",   True,  "Oregon resident BTL crew qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Oregon qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Oregon qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "travel",              True,  "Oregon travel expenditure qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "accommodation_lodging", True, "Oregon accommodation qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "per_diem",            True,  "Per diem costs incurred in Oregon qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "insurance",           True,  "Oregon-sourced production insurance qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "completion_bond",     True,  "Completion bond costs qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("or_opif", "marine_vessel",       True,  "Marine vessel hire in Oregon qualifies under OPIF rebate. Oregon coastal locations are a production asset.", "PARSED"),
    ("or_opif", "vfx",                 True,  "Oregon VFX expenditure qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "post_production",     True,  "Oregon post-production qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "animation",           True,  "Oregon animation qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "music",               True,  "Oregon music expenditure qualifies under OPIF rebate.", "PARSED"),
    ("or_opif", "legal_accounting",    True,  "Oregon legal and accounting costs qualify under OPIF rebate.", "PARSED"),
    ("or_opif", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # nohfc_production_fund — Northern Ontario Heritage Fund Corporation.
    # Discretionary grant for Northern Ontario productions.
    # Most categories QUALIFY for grant application purposes.
    # Grant is deducted from OPSTC and CPTC qualifying spend.
    # -----------------------------------------------------------------------
    ("nohfc_production_fund", "atl_writer",          True,  "ATL writer fees contribute to NOHFC grant eligibility for Northern Ontario productions. Discretionary grant — not a per-category qualifying credit.", "PARSED"),
    ("nohfc_production_fund", "atl_director",        True,  "ATL director fees contribute to NOHFC grant eligibility for Northern Ontario productions.", "PARSED"),
    ("nohfc_production_fund", "atl_producer",        True,  "ATL producer fees contribute to NOHFC grant eligibility for Northern Ontario productions.", "PARSED"),
    ("nohfc_production_fund", "atl_cast_principal",  True,  "Principal cast fees contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "atl_cast_supporting", True,  "Supporting cast fees contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "btl_crew_resident",   True,  "Northern Ontario resident BTL crew are a key qualifying factor for NOHFC grant application.", "PARSED"),
    ("nohfc_production_fund", "btl_crew_non_resident", True, "Non-resident BTL crew working in Northern Ontario contribute to NOHFC eligibility.", "PARSED"),
    ("nohfc_production_fund", "btl_crew_foreign",    True,  "Foreign BTL crew working in Northern Ontario contribute to NOHFC eligibility.", "PARSED"),
    ("nohfc_production_fund", "travel",              True,  "Travel expenditure in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "accommodation_lodging", True, "Northern Ontario accommodation contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "per_diem",            True,  "Per diem costs in Northern Ontario contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "insurance",           True,  "Production insurance costs contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "completion_bond",     True,  "Completion bond costs contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("nohfc_production_fund", "marine_vessel",       True,  "Marine vessel hire in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "vfx",                 True,  "VFX expenditure in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "post_production",     True,  "Post-production in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "animation",           True,  "Animation in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "music",               True,  "Music expenditure in Northern Ontario contributes to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "legal_accounting",    True,  "Legal and accounting costs contribute to NOHFC grant eligibility.", "PARSED"),
    ("nohfc_production_fund", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # cy_film_rebate — Cyprus Film Rebate.
    # Geography-based: all qualifying Cyprus spend qualifies.
    # -----------------------------------------------------------------------
    ("cy_film_rebate", "atl_writer",          True,  "ATL writer fees for Cyprus-incurred work qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "atl_director",        True,  "ATL director fees for Cyprus-incurred work qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "atl_producer",        True,  "ATL producer fees for Cyprus-incurred work qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "atl_cast_principal",  True,  "Principal cast fees for Cyprus-incurred work qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "atl_cast_supporting", True,  "Supporting cast fees for Cyprus-incurred work qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "btl_crew_resident",   True,  "Cyprus resident BTL crew qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Cyprus qualify (geography-based).", "PARSED"),
    ("cy_film_rebate", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Cyprus qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "travel",              True,  "Cyprus travel expenditure qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "accommodation_lodging", True, "Cyprus accommodation qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "per_diem",            True,  "Per diem costs incurred in Cyprus qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "insurance",           True,  "Cyprus-sourced production insurance qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "completion_bond",     True,  "Completion bond costs qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("cy_film_rebate", "marine_vessel",       True,  "Marine vessel hire in Cyprus qualifies under Cyprus film rebate. Cyprus Mediterranean waters are a key production location.", "PARSED"),
    ("cy_film_rebate", "vfx",                 True,  "Cyprus VFX expenditure qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "post_production",     True,  "Cyprus post-production qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "animation",           True,  "Cyprus animation qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "music",               True,  "Cyprus music expenditure qualifies under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "legal_accounting",    True,  "Cyprus legal and accounting costs qualify under Cyprus film rebate.", "PARSED"),
    ("cy_film_rebate", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # hr_cash_rebate — Croatia Cash Rebate (HAVC).
    # Geography-based: all qualifying Croatian spend qualifies.
    # -----------------------------------------------------------------------
    ("hr_cash_rebate", "atl_writer",          True,  "ATL writer fees for Croatian-incurred work qualify under Croatia cash rebate (HAVC).", "PARSED"),
    ("hr_cash_rebate", "atl_director",        True,  "ATL director fees for Croatian-incurred work qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "atl_producer",        True,  "ATL producer fees for Croatian-incurred work qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "atl_cast_principal",  True,  "Principal cast fees for Croatian-incurred work qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "atl_cast_supporting", True,  "Supporting cast fees for Croatian-incurred work qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "btl_crew_resident",   True,  "Croatian resident BTL crew qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Croatia qualify (geography-based).", "PARSED"),
    ("hr_cash_rebate", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Croatia qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "travel",              True,  "Croatian travel expenditure qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "accommodation_lodging", True, "Croatian accommodation qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "per_diem",            True,  "Per diem costs incurred in Croatia qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "insurance",           True,  "Croatian-sourced production insurance qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "completion_bond",     True,  "Completion bond costs qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("hr_cash_rebate", "marine_vessel",       True,  "Marine vessel hire in Croatia qualifies under Croatia cash rebate. Croatian Adriatic coast is a primary marine filming location.", "PARSED"),
    ("hr_cash_rebate", "vfx",                 True,  "Croatian VFX expenditure qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "post_production",     True,  "Croatian post-production qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "animation",           True,  "Croatian animation qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "music",               True,  "Croatian music expenditure qualifies under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "legal_accounting",    True,  "Croatian legal and accounting costs qualify under Croatia cash rebate.", "PARSED"),
    ("hr_cash_rebate", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),

    # -----------------------------------------------------------------------
    # hu_hipa_rebate — Hungary HIPA Cash Rebate.
    # Geography-based: all qualifying Hungarian spend qualifies.
    # -----------------------------------------------------------------------
    ("hu_hipa_rebate", "atl_writer",          True,  "ATL writer fees for Hungarian-incurred work qualify under Hungary HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "atl_director",        True,  "ATL director fees for Hungarian-incurred work qualify under Hungary HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "atl_producer",        True,  "ATL producer fees for Hungarian-incurred work qualify under Hungary HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "atl_cast_principal",  True,  "Principal cast fees for Hungarian-incurred work qualify under Hungary HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "atl_cast_supporting", True,  "Supporting cast fees for Hungarian-incurred work qualify under Hungary HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "btl_crew_resident",   True,  "Hungarian resident BTL crew qualify under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "btl_crew_non_resident", True, "Non-resident BTL crew performing work in Hungary qualify under HIPA rebate (geography-based).", "PARSED"),
    ("hu_hipa_rebate", "btl_crew_foreign",    True,  "Foreign BTL crew performing work in Hungary qualify under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "travel",              True,  "Hungarian travel expenditure qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "accommodation_lodging", True, "Hungarian accommodation qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "per_diem",            True,  "Per diem costs incurred in Hungary qualify under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "insurance",           True,  "Hungarian-sourced production insurance qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "completion_bond",     True,  "Completion bond costs qualify under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "contingency",         False, _CONTINGENCY_NOTE, "PARSED"),
    ("hu_hipa_rebate", "marine_vessel",       True,  "Marine vessel hire in Hungary qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "vfx",                 True,  "Hungarian VFX expenditure qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "post_production",     True,  "Hungarian post-production qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "animation",           True,  "Hungarian animation qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "music",               True,  "Hungarian music expenditure qualifies under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "legal_accounting",    True,  "Hungarian legal and accounting costs qualify under HIPA rebate.", "PARSED"),
    ("hu_hipa_rebate", "customs_imports",     None,  _CUSTOMS_UNKNOWN, "DISCOVERY"),
]


def upgrade() -> None:
    conn = op.get_bind()

    for slug, labor_type, qualifies, treatment_notes, tier in _TREATMENTS:
        conn.execute(
            sa.text("""
                INSERT INTO program_spend_treatments (
                    id, program_id, labor_type,
                    qualifies, cap_pct, cap_amount_local,
                    treatment_notes, confidence_tier,
                    created_at, updated_at
                )
                SELECT
                    :id, p.id, :labor_type,
                    :qualifies, NULL, NULL,
                    :notes, :tier,
                    :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_spend_treatments t
                      WHERE t.program_id = p.id AND t.labor_type = :labor_type
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"treatment:{slug}:{labor_type}"),
                "slug": slug, "labor_type": labor_type,
                "qualifies": qualifies, "notes": treatment_notes,
                "tier": tier, "now": NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug, labor_type, *_ in _TREATMENTS:
        conn.execute(
            sa.text("DELETE FROM program_spend_treatments WHERE id = :id"),
            {"id": _uid(f"treatment:{slug}:{labor_type}")},
        )
