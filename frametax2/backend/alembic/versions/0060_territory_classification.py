"""0060 — Territory classification table + six new programs.

Creates:
  - territory_classifications table (all ~249 territories with status)

Adds programs for 6 new jurisdictions:
  FO — Faroese Film Fund (Filmstødín)
  GL — Greenland Film Institute (GFI)
  IM — Isle of Man Film Co-Production Fund
  PK — Pakistan Film Commission Cash Rebate (20%)
  PY — CONACINE Paraguay Fondo de Fomento
  XK — Kosovo Film Center QKK Production Fund

Adds for each new program:
  - program_admin_details (DISCOVERY tier)
  - program_spend_treatments (21 labour types, DISCOVERY tier)
  - fund_economics (for grant programmes: FO, GL, PY, XK)

Revision ID: 0060
Revises: 0059
Create Date: 2026-06-24
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0060"
down_revision: Union[str, None] = "0059"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0060-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# ---------------------------------------------------------------------------
# New programs
# slug is derived as lowercase(jurisdiction_code) + "_" + key_name_fragment
# ---------------------------------------------------------------------------
_NEW_PROGRAMS = [
    # (jcode, jname, pname, slug, ptype, brate, mrate, refund, transfer,
    #  mspend, acap, cult, local_ent, conf, source_title, source_url)
    (
        "FO", "Faroe Islands",
        "Faroese Film Fund (Filmstødín)",
        "fo_filmstoddin",
        "direct_grant", None, None, False, False, None, 500_000, False, True,
        "DISCOVERY",
        "Filmstødín — Faroese Film Fund",
        "https://filmstodín.fo/",
    ),
    (
        "GL", "Greenland",
        "Greenland Film Institute (GFI) Production Support",
        "gl_gfi",
        "direct_grant", None, None, False, False, None, 300_000, False, True,
        "DISCOVERY",
        "Greenland Film Institute",
        "https://www.gfi.gl/",
    ),
    (
        "IM", "Isle of Man",
        "Isle of Man Film Co-Production Fund",
        "im_iom_film",
        "co_production_fund", None, None, False, True, 100_000, 1_000_000, False, True,
        "DISCOVERY",
        "Isle of Man Film",
        "https://www.isleofmanfilm.com/",
    ),
    (
        "PK", "Pakistan",
        "Pakistan Film Commission Cash Rebate",
        "pk_pfc_rebate",
        "cash_rebate", 20.0, 20.0, True, False, 500_000, None, False, True,
        "DISCOVERY",
        "Pakistan Film Commission",
        "https://www.filmcommission.pk/",
    ),
    (
        "PY", "Paraguay",
        "CONACINE Paraguay Fondo de Fomento Cinematográfico",
        "py_conacine",
        "direct_grant", None, None, False, False, None, 200_000, False, True,
        "DISCOVERY",
        "CONACINE Paraguay",
        "http://www.conacine.gov.py/",
    ),
    (
        "XK", "Kosovo",
        "Kosovo Film Center QKK Production Fund",
        "xk_qkk",
        "direct_grant", None, None, False, False, None, 500_000, False, True,
        "DISCOVERY",
        "Kosovo Film Center (QKK)",
        "https://qkk-ks.net/",
    ),
]

_PROGRAM_SLUGS = [row[3] for row in _NEW_PROGRAMS]

# Grant programmes that need fund_economics
_GRANT_FUND_ECON = [
    # (slug, classification, is_repayable, is_recoupable, has_equity,
    #  is_soft_money, is_govt_assistance, typical_max_usd, notes)
    (
        "fo_filmstoddin", "grant", False, False, False, True, True, 500_000,
        "Filmstødín direct grant. Small fund; competitive allocation. "
        "Source: filmstodín.fo. Govt assistance.",
    ),
    (
        "gl_gfi", "grant", False, False, False, True, True, 300_000,
        "Greenland Film Institute direct grant. Competitive. "
        "Source: gfi.gl. Govt assistance.",
    ),
    (
        "py_conacine", "grant", False, False, False, True, True, 200_000,
        "CONACINE Paraguay Fondo de Fomento. Direct grant. "
        "Source: conacine.gov.py. Govt assistance.",
    ),
    (
        "xk_qkk", "grant", False, False, False, True, True, 500_000,
        "Kosovo Film Center QKK production fund. Direct grant. "
        "Source: qkk-ks.net. Govt assistance.",
    ),
]

_DISC_ASSIGN_NOTES = (
    "DISCOVERY tier — assignability to lenders not confirmed from primary source."
)
_DISC_FIN_NOTES = (
    "DISCOVERY tier — processing timeline and financing terms not confirmed."
)
_DISC_WINDOW = (
    "Application typically required before commencement of qualifying production. "
    "Verify with local film office before pre-production."
)

_LABOR_TYPES: list[str] = [
    "atl_writer", "atl_director", "atl_producer",
    "atl_cast_principal", "atl_cast_supporting",
    "btl_crew_resident", "btl_crew_non_resident", "btl_crew_foreign",
    "travel", "accommodation_lodging", "per_diem",
    "insurance", "completion_bond", "contingency",
    "marine_vessel", "vfx", "post_production", "animation",
    "music", "legal_accounting", "customs_imports",
]

_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)
_UNKNOWN_NOTE = (
    "DISCOVERY tier — spend treatment not confirmed from primary source. "
    "Verify eligibility with local film office before budget finalisation."
)

# ---------------------------------------------------------------------------
# Territory classifications — all ~249 entries
# ---------------------------------------------------------------------------
_TERRITORY_ROWS = [
    # code, name, status, notes
    ("AD", "Andorra", "NO_KNOWN_PROGRAM_FOUND",
     "No known national film incentive. No public program registry found."),
    ("AE", "United Arab Emirates", "PROGRAMS_FOUND",
     "Dubai DPI rebate and ADFC rebate programs. In FrameTax DB: AE."),
    ("AF", "Afghanistan", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict since 2021 Taliban takeover. No accessible public film body."),
    ("AG", "Antigua and Barbuda", "NO_KNOWN_PROGRAM_FOUND",
     "Antigua Film Office provides facilitation services only."),
    ("AI", "Anguilla", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film production incentive."),
    ("AL", "Albania", "PROGRAMS_FOUND",
     "Albanian National Centre of Cinematography (AKSH) grant. In FrameTax DB: AL."),
    ("AM", "Armenia", "PROGRAMS_FOUND",
     "National Cinema Centre of Armenia grant. In FrameTax DB: AM."),
    ("AO", "Angola", "PROGRAMS_FOUND",
     "INCA film support program. In FrameTax DB: AO."),
    ("AQ", "Antarctica", "NO_KNOWN_PROGRAM_FOUND",
     "No permanent population; no film incentive."),
    ("AR", "Argentina", "PROGRAMS_FOUND",
     "INCAA grants and rebates. In FrameTax DB: AR."),
    ("AS", "American Samoa", "NO_KNOWN_PROGRAM_FOUND",
     "US territory. No known separate film incentive."),
    ("AT", "Austria", "PROGRAMS_FOUND",
     "FISA+ cash rebate. In FrameTax DB: AT."),
    ("AU", "Australia", "PROGRAMS_FOUND",
     "Location Offset, PDV Offset, Screen Australia. In FrameTax DB: AU."),
    ("AW", "Aruba", "NO_KNOWN_PROGRAM_FOUND",
     "Dutch constituent country. No known film incentive program."),
    ("AZ", "Azerbaijan", "NO_KNOWN_PROGRAM_FOUND",
     "Azerbaijanfilm studio. No accessible incentive program found."),
    ("BA", "Bosnia and Herzegovina", "PROGRAMS_FOUND",
     "BH Film Fund (BHFF) grants; Eurimages member. In FrameTax DB: BA."),
    ("BB", "Barbados", "PROGRAMS_FOUND",
     "Barbados Film Commission facilitation. In FrameTax DB: BB."),
    ("BD", "Bangladesh", "PROGRAMS_FOUND",
     "BFDC (Bangladesh Film Development Corporation). In FrameTax DB: BD."),
    ("BE", "Belgium", "PROGRAMS_FOUND",
     "Belgian Tax Shelter, VAF Flanders, Wallimage, Screen.Brussels. In FrameTax DB: BE."),
    ("BF", "Burkina Faso", "NO_KNOWN_PROGRAM_FOUND",
     "FESPACO host country; no accessible production incentive program found."),
    ("BG", "Bulgaria", "PROGRAMS_FOUND",
     "Bulgarian Film Commission cash rebate. In FrameTax DB: BG."),
    ("BH", "Bahrain", "PROGRAMS_FOUND",
     "Bahrain film support bureau. In FrameTax DB: BH."),
    ("BI", "Burundi", "NO_KNOWN_PROGRAM_FOUND",
     "No known film incentive or public film body."),
    ("BJ", "Benin", "NO_KNOWN_PROGRAM_FOUND",
     "No known film incentive program."),
    ("BL", "Saint Barthélemy", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas collectivity. No separate film program."),
    ("BM", "Bermuda", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film production incentive."),
    ("BN", "Brunei", "NO_KNOWN_PROGRAM_FOUND",
     "No known public film production incentive program."),
    ("BO", "Bolivia", "NO_KNOWN_PROGRAM_FOUND",
     "CONACINE Bolivia. No accessible production incentive found."),
    ("BQ", "Bonaire, Sint Eustatius and Saba", "NO_KNOWN_PROGRAM_FOUND",
     "Dutch special municipalities. No known separate film incentive."),
    ("BR", "Brazil", "PROGRAMS_FOUND",
     "ANCINE rebate and Fundo Setorial do Audiovisual. In FrameTax DB: BR."),
    ("BS", "Bahamas", "PROGRAMS_FOUND",
     "Bahamas Film Commission facilitation. In FrameTax DB: BS."),
    ("BT", "Bhutan", "PROGRAMS_FOUND",
     "Bhutan Tourism Council film facilitation. In FrameTax DB: BT."),
    ("BV", "Bouvet Island", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited Norwegian territory. No film program."),
    ("BW", "Botswana", "PROGRAMS_FOUND",
     "Botswana film commission. In FrameTax DB: BW."),
    ("BY", "Belarus", "PROGRAMS_FOUND",
     "Belarusfilm national studio facilitation. In FrameTax DB: BY."),
    ("BZ", "Belize", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("CA", "Canada", "PROGRAMS_FOUND",
     "Telefilm Canada, CMF, provincial tax credits (BC, ON, QC, AB, NS, MB, etc.). In FrameTax DB: CA."),
    ("CC", "Cocos (Keeling) Islands", "NO_KNOWN_PROGRAM_FOUND",
     "Australian external territory. No known separate film program."),
    ("CD", "Democratic Republic of the Congo", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("CF", "Central African Republic", "NO_KNOWN_PROGRAM_FOUND",
     "No known film incentive program."),
    ("CG", "Republic of the Congo", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("CH", "Switzerland", "PROGRAMS_FOUND",
     "Swiss Federal Film Support (FOC/BAK). In FrameTax DB: CH."),
    ("CI", "Côte d'Ivoire", "NO_KNOWN_PROGRAM_FOUND",
     "No accessible film production incentive program found."),
    ("CK", "Cook Islands", "NO_KNOWN_PROGRAM_FOUND",
     "New Zealand associated state. No known separate film incentive."),
    ("CL", "Chile", "PROGRAMS_FOUND",
     "CORFO 30% rebate and CNTV. In FrameTax DB: CL."),
    ("CM", "Cameroon", "NO_KNOWN_PROGRAM_FOUND",
     "No known accessible film production incentive program."),
    ("CN", "China", "PROGRAMS_FOUND",
     "NRTA co-production track; co-production treaties. In FrameTax DB: CN."),
    ("CO", "Colombia", "PROGRAMS_FOUND",
     "FDC Colombia ~20% rebate and Film Commission. In FrameTax DB: CO."),
    ("CR", "Costa Rica", "PROGRAMS_FOUND",
     "Costa Rica Film Commission facilitation. In FrameTax DB: CR."),
    ("CU", "Cuba", "PROGRAMS_FOUND",
     "ICAIC Cuba film production support. In FrameTax DB: CU."),
    ("CV", "Cabo Verde", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("CW", "Curaçao", "NO_KNOWN_PROGRAM_FOUND",
     "Dutch constituent country. No known separate film incentive."),
    ("CX", "Christmas Island", "NO_KNOWN_PROGRAM_FOUND",
     "Australian territory. No known separate film program."),
    ("CY", "Cyprus", "PROGRAMS_FOUND",
     "Cyprus Film Advisory Board 35% rebate. In FrameTax DB: CY."),
    ("CZ", "Czechia", "PROGRAMS_FOUND",
     "Czech Film Commission 20% incentive. In FrameTax DB: CZ."),
    ("DE", "Germany", "PROGRAMS_FOUND",
     "DFFF, FFA, regional funds (Bayern, NRW, etc.), ARD/ZDF. In FrameTax DB: DE."),
    ("DJ", "Djibouti", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("DK", "Denmark", "PROGRAMS_FOUND",
     "Danish Film Institute and Copenhagen Film Fund. In FrameTax DB: DK."),
    ("DM", "Dominica", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("DO", "Dominican Republic", "PROGRAMS_FOUND",
     "25% cash rebate on local spend. In FrameTax DB: DO."),
    ("DZ", "Algeria", "PROGRAMS_FOUND",
     "CADC (Centre Algérien pour le Développement du Cinéma). In FrameTax DB: DZ."),
    ("EC", "Ecuador", "PROGRAMS_FOUND",
     "Ecuador Film Commission facilitation. In FrameTax DB: EC."),
    ("EE", "Estonia", "PROGRAMS_FOUND",
     "Estonian Film Commission 30% rebate. In FrameTax DB: EE."),
    ("EG", "Egypt", "PROGRAMS_FOUND",
     "Egypt Film Commission facilitation. In FrameTax DB: EG."),
    ("EH", "Western Sahara", "NO_KNOWN_PROGRAM_FOUND",
     "Contested territory with no known film program."),
    ("ER", "Eritrea", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Closed state with no accessible public government information."),
    ("ES", "Spain", "PROGRAMS_FOUND",
     "ICAA tax credit (Spain Audiovisual Hub), regional incentives (Canary Islands, etc.). In FrameTax DB: ES."),
    ("ET", "Ethiopia", "PROGRAMS_FOUND",
     "Ethiopia Film Commission. In FrameTax DB: ET."),
    ("FI", "Finland", "PROGRAMS_FOUND",
     "Finnish Film Foundation (SES) grants. In FrameTax DB: FI."),
    ("FJ", "Fiji", "PROGRAMS_FOUND",
     "Fiji Audio Visual Commission facilitation and tourism film support. In FrameTax DB: FJ."),
    ("FK", "Falkland Islands", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("FM", "Micronesia", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("FO", "Faroe Islands", "PROGRAMS_FOUND",
     "Filmstødín Faroese Film Fund. Added in migration 0060."),
    ("FR", "France", "PROGRAMS_FOUND",
     "CNC, TRIP, UniFrance, regional funds, CNC animation. In FrameTax DB: FR."),
    ("GA", "Gabon", "PROGRAMS_FOUND",
     "Gabon Ministry of Culture film commission. In FrameTax DB: GA."),
    ("GB", "United Kingdom", "PROGRAMS_FOUND",
     "UK AVEC, Screen Scotland, Wales Film Fund, BFI, regional funds. In FrameTax DB: GB."),
    ("GD", "Grenada", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("GE", "Georgia", "PROGRAMS_FOUND",
     "Georgian National Film Center (GNFC) rebate. In FrameTax DB: GE."),
    ("GF", "French Guiana", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas region. No separate film incentive."),
    ("GG", "Guernsey", "NO_KNOWN_PROGRAM_FOUND",
     "Crown dependency. No known film incentive program."),
    ("GH", "Ghana", "PROGRAMS_FOUND",
     "Ghana Film Authority facilitation. In FrameTax DB: GH."),
    ("GI", "Gibraltar", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("GL", "Greenland", "PROGRAMS_FOUND",
     "Greenland Film Institute (GFI). Added in migration 0060."),
    ("GM", "Gambia", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("GN", "Guinea", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("GP", "Guadeloupe", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas region. No separate film program."),
    ("GQ", "Equatorial Guinea", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("GR", "Greece", "PROGRAMS_FOUND",
     "Greek Film Centre cash rebate and grants, EKOME. In FrameTax DB: GR."),
    ("GS", "South Georgia and South Sandwich Islands", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited British territory. No film program."),
    ("GT", "Guatemala", "PROGRAMS_FOUND",
     "Guatemala film commission. In FrameTax DB: GT."),
    ("GU", "Guam", "NO_KNOWN_PROGRAM_FOUND",
     "US territory. No known separate film incentive."),
    ("GW", "Guinea-Bissau", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("GY", "Guyana", "PROGRAMS_FOUND",
     "Guyana film commission. In FrameTax DB: GY."),
    ("HK", "Hong Kong", "PROGRAMS_FOUND",
     "CreateHK film support. In FrameTax DB: HK."),
    ("HM", "Heard Island and McDonald Islands", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited Australian territory. No film program."),
    ("HN", "Honduras", "NO_KNOWN_PROGRAM_FOUND",
     "No known accessible film production incentive program."),
    ("HR", "Croatia", "PROGRAMS_FOUND",
     "Croatian Audiovisual Centre (HAVC) cash rebate. In FrameTax DB: HR."),
    ("HT", "Haiti", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("HU", "Hungary", "PROGRAMS_FOUND",
     "HIPA 30% cash rebate. In FrameTax DB: HU."),
    ("ID", "Indonesia", "PROGRAMS_FOUND",
     "Indonesian Film Production Board (BPIFB) facilitation. In FrameTax DB: ID."),
    ("IE", "Ireland", "PROGRAMS_FOUND",
     "Section 481 tax credit, Screen Ireland. In FrameTax DB: IE."),
    ("IL", "Israel", "PROGRAMS_FOUND",
     "Maslool 30% rebate, Israeli Film Council. In FrameTax DB: IL."),
    ("IM", "Isle of Man", "PROGRAMS_FOUND",
     "Isle of Man Film Co-Production Fund. Added in migration 0060."),
    ("IN", "India", "PROGRAMS_FOUND",
     "India NFDC co-production fund and state film commissions. In FrameTax DB: IN."),
    ("IO", "British Indian Ocean Territory", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited British territory. No film program."),
    ("IQ", "Iraq", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict zones; no accessible public film incentive information."),
    ("IR", "Iran", "PROGRAMS_FOUND",
     "Farabi Cinema Foundation film support. In FrameTax DB: IR."),
    ("IS", "Iceland", "PROGRAMS_FOUND",
     "Iceland 25% rebate and post/VFX incentive. In FrameTax DB: IS."),
    ("IT", "Italy", "PROGRAMS_FOUND",
     "MiC Tax Credit, regional funds (Lazio, Sicilia, etc.), RAI Cinema. In FrameTax DB: IT."),
    ("JE", "Jersey", "NO_KNOWN_PROGRAM_FOUND",
     "Crown dependency. No known film incentive program."),
    ("JM", "Jamaica", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("JO", "Jordan", "PROGRAMS_FOUND",
     "Royal Film Commission (RFC) 15% rebate. In FrameTax DB: JO."),
    ("JP", "Japan", "PROGRAMS_FOUND",
     "JLOC location incentive up to 25%, VIPO animation. In FrameTax DB: JP."),
    ("KE", "Kenya", "PROGRAMS_FOUND",
     "Kenya Film Commission (KFC) rebate. In FrameTax DB: KE."),
    ("KG", "Kyrgyzstan", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("KH", "Cambodia", "PROGRAMS_FOUND",
     "Cambodia Department of Cinema facilitation. In FrameTax DB: KH."),
    ("KI", "Kiribati", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("KM", "Comoros", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("KN", "Saint Kitts and Nevis", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("KP", "North Korea", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Closed state. No publicly accessible government information."),
    ("KR", "South Korea", "PROGRAMS_FOUND",
     "KOFIC location incentive, KOCCA animation, export programs. In FrameTax DB: KR."),
    ("KW", "Kuwait", "PROGRAMS_FOUND",
     "Kuwait film bureau facilitation. In FrameTax DB: KW."),
    ("KY", "Cayman Islands", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("KZ", "Kazakhstan", "PROGRAMS_FOUND",
     "Kazakhfilm studio facilitation. In FrameTax DB: KZ."),
    ("LA", "Laos", "PROGRAM_STATUS_UNCLEAR",
     "Lao Filming Bureau exists; no accessible production incentive confirmed."),
    ("LB", "Lebanon", "NO_KNOWN_PROGRAM_FOUND",
     "No known accessible film production incentive program."),
    ("LC", "Saint Lucia", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("LI", "Liechtenstein", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("LK", "Sri Lanka", "PROGRAMS_FOUND",
     "Sri Lanka film rebate. In FrameTax DB: LK."),
    ("LR", "Liberia", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("LS", "Lesotho", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("LT", "Lithuania", "PROGRAMS_FOUND",
     "LCC Lithuania 30% rebate. In FrameTax DB: LT."),
    ("LU", "Luxembourg", "PROGRAMS_FOUND",
     "Film Fund Luxembourg and Tax Shelter. In FrameTax DB: LU."),
    ("LV", "Latvia", "PROGRAMS_FOUND",
     "NKMP Latvia 30% rebate. In FrameTax DB: LV."),
    ("LY", "Libya", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict; no accessible public film body or incentive information."),
    ("MA", "Morocco", "PROGRAMS_FOUND",
     "CCM Morocco rebate and facilitation. In FrameTax DB: MA."),
    ("MC", "Monaco", "NO_KNOWN_PROGRAM_FOUND",
     "No known separate film production incentive program."),
    ("MD", "Moldova", "PROGRAMS_FOUND",
     "National Centre for Cinematography Moldova (NCFM). In FrameTax DB: MD."),
    ("ME", "Montenegro", "PROGRAMS_FOUND",
     "Montenegro Film Commission rebate. In FrameTax DB: ME."),
    ("MF", "Saint Martin (French)", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas collectivity. No separate film incentive."),
    ("MG", "Madagascar", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MH", "Marshall Islands", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MK", "North Macedonia", "PROGRAMS_FOUND",
     "Macedonian Film Agency (MFA) rebate. In FrameTax DB: MK."),
    ("ML", "Mali", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MM", "Myanmar", "PROGRAM_STATUS_UNCLEAR",
     "Myanmar Motion Picture Enterprise exists; production incentive status unclear post-coup."),
    ("MN", "Mongolia", "PROGRAMS_FOUND",
     "Mongolia film commission facilitation. In FrameTax DB: MN."),
    ("MO", "Macao", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MP", "Northern Mariana Islands", "NO_KNOWN_PROGRAM_FOUND",
     "US Commonwealth. No known separate film incentive."),
    ("MQ", "Martinique", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas region. No separate film incentive."),
    ("MR", "Mauritania", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MS", "Montserrat", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("MT", "Malta", "PROGRAMS_FOUND",
     "MFC Malta 40% cash rebate. In FrameTax DB: MT."),
    ("MU", "Mauritius", "PROGRAMS_FOUND",
     "EDB Mauritius film incentive. In FrameTax DB: MU."),
    ("MV", "Maldives", "PROGRAMS_FOUND",
     "MMPRC film facilitation and tourism film support. In FrameTax DB: MV."),
    ("MW", "Malawi", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("MX", "Mexico", "PROGRAMS_FOUND",
     "IMCINE, EFICINE tax benefit, state facilitation. In FrameTax DB: MX."),
    ("MY", "Malaysia", "PROGRAMS_FOUND",
     "FINAS Malaysia rebate. In FrameTax DB: MY."),
    ("MZ", "Mozambique", "PROGRAMS_FOUND",
     "Mozambique film commission. In FrameTax DB: MZ."),
    ("NA", "Namibia", "PROGRAMS_FOUND",
     "Namibia Film Commission (NFC) incentive. In FrameTax DB: NA."),
    ("NC", "New Caledonia", "NO_KNOWN_PROGRAM_FOUND",
     "French special collectivity. No separate film incentive."),
    ("NE", "Niger", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("NF", "Norfolk Island", "NO_KNOWN_PROGRAM_FOUND",
     "Australian territory. No known separate film program."),
    ("NG", "Nigeria", "NO_KNOWN_PROGRAM_FOUND",
     "NFVCB regulatory body; no accessible production incentive confirmed."),
    ("NI", "Nicaragua", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("NL", "Netherlands", "PROGRAMS_FOUND",
     "NFPI 30% rebate and Netherlands Film Fund. In FrameTax DB: NL."),
    ("NO", "Norway", "PROGRAMS_FOUND",
     "NFI Norway 25% rebate, regional funds. In FrameTax DB: NO."),
    ("NP", "Nepal", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("NR", "Nauru", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("NU", "Niue", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("NZ", "New Zealand", "PROGRAMS_FOUND",
     "NZSPG, PDV rebate, Tourism NZ, Air NZ. In FrameTax DB: NZ."),
    ("OM", "Oman", "PROGRAMS_FOUND",
     "Oman Film Centre facilitation. In FrameTax DB: OM."),
    ("PA", "Panama", "PROGRAMS_FOUND",
     "Panama Film Commission facilitation. In FrameTax DB: PA."),
    ("PE", "Peru", "NO_KNOWN_PROGRAM_FOUND",
     "No known accessible film production incentive program."),
    ("PF", "French Polynesia", "NO_KNOWN_PROGRAM_FOUND",
     "French collectivity. No separate film incentive."),
    ("PG", "Papua New Guinea", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("PH", "Philippines", "PROGRAMS_FOUND",
     "FDCP Philippines incentive. In FrameTax DB: PH."),
    ("PK", "Pakistan", "PROGRAMS_FOUND",
     "Pakistan Film Commission 20% cash rebate. Added in migration 0060."),
    ("PL", "Poland", "PROGRAMS_FOUND",
     "PISF Poland film incentive. In FrameTax DB: PL."),
    ("PM", "Saint Pierre and Miquelon", "NO_KNOWN_PROGRAM_FOUND",
     "French collectivity. No separate film incentive."),
    ("PN", "Pitcairn Islands", "NO_KNOWN_PROGRAM_FOUND",
     "Tiny British territory. No film program."),
    ("PR", "Puerto Rico", "PROGRAMS_FOUND",
     "Puerto Rico Film Commission tax credit. In FrameTax DB: PR."),
    ("PS", "Palestine", "PROGRAM_STATUS_UNCLEAR",
     "Palestinian Film Institute exists; production incentive program status unclear."),
    ("PT", "Portugal", "PROGRAMS_FOUND",
     "Portugal 25% cash rebate. In FrameTax DB: PT."),
    ("PW", "Palau", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("PY", "Paraguay", "PROGRAMS_FOUND",
     "CONACINE Paraguay Fondo de Fomento. Added in migration 0060."),
    ("QA", "Qatar", "PROGRAMS_FOUND",
     "Qatar film support. In FrameTax DB: QA."),
    ("RE", "Réunion", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas region. No separate film incentive."),
    ("RO", "Romania", "PROGRAMS_FOUND",
     "Romania 35% cash rebate. In FrameTax DB: RO."),
    ("RS", "Serbia", "PROGRAMS_FOUND",
     "Serbia 25% cash rebate. In FrameTax DB: RS."),
    ("RU", "Russia", "PROGRAMS_FOUND",
     "Russian Cinema Fund (Fond Kino). In FrameTax DB: RU."),
    ("RW", "Rwanda", "PROGRAMS_FOUND",
     "Rwanda Film Commission facilitation. In FrameTax DB: RW."),
    ("SA", "Saudi Arabia", "PROGRAMS_FOUND",
     "Saudi Film Commission rebate and grants. In FrameTax DB: SA."),
    ("SB", "Solomon Islands", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SC", "Seychelles", "PROGRAMS_FOUND",
     "Seychelles Tourism Board film support. In FrameTax DB: SC."),
    ("SD", "Sudan", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict since 2023. No accessible public film body or incentive."),
    ("SE", "Sweden", "PROGRAMS_FOUND",
     "Swedish Film Institute (SFI) 25% rebate and regional funds. In FrameTax DB: SE."),
    ("SG", "Singapore", "PROGRAMS_FOUND",
     "IMDA Singapore digital media fund. In FrameTax DB: SG."),
    ("SH", "Saint Helena, Ascension and Tristan da Cunha", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("SI", "Slovenia", "PROGRAMS_FOUND",
     "Slovenian Film Centre (SFC) 25% rebate. In FrameTax DB: SI."),
    ("SJ", "Svalbard and Jan Mayen", "NO_KNOWN_PROGRAM_FOUND",
     "Norwegian territory. No known separate film program."),
    ("SK", "Slovakia", "PROGRAMS_FOUND",
     "AVF Slovakia 33% rebate. In FrameTax DB: SK."),
    ("SL", "Sierra Leone", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SM", "San Marino", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SN", "Senegal", "PROGRAMS_FOUND",
     "Senegal FOPICA film fund. In FrameTax DB: SN."),
    ("SO", "Somalia", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict; no accessible public film body or incentive information."),
    ("SR", "Suriname", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SS", "South Sudan", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict; no accessible public film body or incentive information."),
    ("ST", "São Tomé and Príncipe", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SV", "El Salvador", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("SX", "Sint Maarten (Dutch)", "NO_KNOWN_PROGRAM_FOUND",
     "Dutch constituent country. No known separate film incentive."),
    ("SY", "Syria", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict. No accessible public film body or incentive information."),
    ("SZ", "Eswatini", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TC", "Turks and Caicos Islands", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("TD", "Chad", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TF", "French Southern Territories", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited French territory. No film program."),
    ("TG", "Togo", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TH", "Thailand", "PROGRAMS_FOUND",
     "BOI Thailand 20% rebate. In FrameTax DB: TH."),
    ("TJ", "Tajikistan", "NO_KNOWN_PROGRAM_FOUND",
     "No known accessible film production incentive program."),
    ("TK", "Tokelau", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TL", "Timor-Leste", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TM", "Turkmenistan", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Highly closed state. No accessible public government film information."),
    ("TN", "Tunisia", "PROGRAMS_FOUND",
     "CNCI Tunisia rebate. In FrameTax DB: TN."),
    ("TO", "Tonga", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TR", "Turkey", "PROGRAMS_FOUND",
     "Turkey Ministry of Culture cinema support fund. In FrameTax DB: TR."),
    ("TT", "Trinidad and Tobago", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TV", "Tuvalu", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("TW", "Taiwan", "PROGRAMS_FOUND",
     "TFAI Taiwan rebate. In FrameTax DB: TW."),
    ("TZ", "Tanzania", "PROGRAMS_FOUND",
     "Tanzania Film Board. In FrameTax DB: TZ."),
    ("UA", "Ukraine", "PROGRAMS_FOUND",
     "Ukrainian State Film Agency production support. In FrameTax DB: UA."),
    ("UG", "Uganda", "PROGRAMS_FOUND",
     "Uganda Film Commission. In FrameTax DB: UG."),
    ("UM", "United States Minor Outlying Islands", "NO_KNOWN_PROGRAM_FOUND",
     "Uninhabited US territories. No film program."),
    ("US", "United States", "PROGRAMS_FOUND",
     "Federal historic tax credit; state programs (GA, LA, NM, NY, MA, CA, OR, WA, NC, TX, etc.). In FrameTax DB: US."),
    ("UY", "Uruguay", "PROGRAMS_FOUND",
     "ICAU Uruguay rebate. In FrameTax DB: UY."),
    ("UZ", "Uzbekistan", "PROGRAMS_FOUND",
     "Uzbekkino national studio facilitation. In FrameTax DB: UZ."),
    ("VA", "Vatican City", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("VC", "Saint Vincent and the Grenadines", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("VE", "Venezuela", "NO_KNOWN_PROGRAM_FOUND",
     "CNAC Venezuela. Economic instability; no accessible incentive program."),
    ("VG", "British Virgin Islands", "NO_KNOWN_PROGRAM_FOUND",
     "British Overseas Territory. No known film incentive."),
    ("VI", "US Virgin Islands", "PROGRAMS_FOUND",
     "USVI film program. In FrameTax DB: VI."),
    ("VN", "Vietnam", "PROGRAMS_FOUND",
     "Vietnam Film Department facilitation. In FrameTax DB: VN."),
    ("VU", "Vanuatu", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("WF", "Wallis and Futuna", "NO_KNOWN_PROGRAM_FOUND",
     "French collectivity. No separate film incentive."),
    ("WS", "Samoa", "NO_KNOWN_PROGRAM_FOUND",
     "No known film production incentive program."),
    ("XK", "Kosovo", "PROGRAMS_FOUND",
     "Kosovo Film Center QKK production fund. Added in migration 0060."),
    ("YE", "Yemen", "PUBLIC_INFORMATION_UNAVAILABLE",
     "Active conflict. No accessible public film body or incentive information."),
    ("YT", "Mayotte", "NO_KNOWN_PROGRAM_FOUND",
     "French overseas department. No separate film incentive."),
    ("ZA", "South Africa", "PROGRAMS_FOUND",
     "NFVF, DTI/DTIC cash rebate. In FrameTax DB: ZA."),
    ("ZM", "Zambia", "PROGRAMS_FOUND",
     "National Arts Council of Zambia film support. In FrameTax DB: ZM."),
    ("ZW", "Zimbabwe", "PROGRAMS_FOUND",
     "Zimbabwe Film Council (ZFC) production support. In FrameTax DB: ZW."),
    # Supranational / regional groupings
    ("EU", "European Union", "PROGRAMS_FOUND",
     "Eurimages, MEDIA Fund (Creative Europe). In FrameTax DB: EU."),
    ("ACP", "African, Caribbean and Pacific Group", "PROGRAMS_FOUND",
     "ACP–EU co-production fund. In FrameTax DB: ACP."),
    ("IBERO", "Ibero-American Region", "PROGRAMS_FOUND",
     "Ibermedia Programme. In FrameTax DB: IBERO."),
    ("NORDIC", "Nordic Region", "PROGRAMS_FOUND",
     "Nordic Film & TV Fund (NFTF). In FrameTax DB: NORDIC."),
]


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Create territory_classifications table
    # ------------------------------------------------------------------
    op.create_table(
        "territory_classifications",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, index=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ------------------------------------------------------------------
    # 2. Seed territory_classifications rows
    # ------------------------------------------------------------------
    for code, name, status, notes in _TERRITORY_ROWS:
        conn.execute(
            sa.text("""
                INSERT INTO territory_classifications (code, name, status, notes)
                VALUES (:code, :name, :status, :notes)
                ON CONFLICT (code) DO UPDATE SET
                    name   = EXCLUDED.name,
                    status = EXCLUDED.status,
                    notes  = EXCLUDED.notes
            """),
            {"code": code, "name": name, "status": status, "notes": notes},
        )

    # ------------------------------------------------------------------
    # 3. Ensure jurisdiction rows for the 6 new codes
    # ------------------------------------------------------------------
    _JURS = [
        ("FO", "Faroe Islands", "Europe", "DK"),
        ("GL", "Greenland", "Americas", "DK"),
        ("IM", "Isle of Man", "Europe", "GB"),
        ("PK", "Pakistan", "Asia", "PK"),
        ("PY", "Paraguay", "Americas", "PY"),
        ("XK", "Kosovo", "Europe", "XK"),
    ]
    for code, name, region, country_code in _JURS:
        conn.execute(
            sa.text("""
                INSERT INTO jurisdictions (id, code, name, level, currency_code, country_code,
                    is_active, created_at, updated_at)
                SELECT gen_random_uuid(), :code, :name, 'country', 'USD', :country_code,
                    true, now(), now()
                WHERE NOT EXISTS (
                    SELECT 1 FROM jurisdictions WHERE code = :code ::varchar
                )
            """),
            {"code": code, "name": name, "country_code": country_code},
        )

    # ------------------------------------------------------------------
    # 4. Insert new incentive programs
    # ------------------------------------------------------------------
    for row in _NEW_PROGRAMS:
        (jcode, jname, pname, slug, ptype, brate, mrate, refund, transfer,
         mspend, acap, cult, local_ent, conf, src_title, src_url) = row
        brate = brate / 100.0 if brate is not None else None
        mrate = mrate / 100.0 if mrate is not None else None
        conn.execute(
            sa.text("""
                INSERT INTO incentive_programs
                    (id, jurisdiction_id, name, slug, program_type, credit_basis,
                     base_rate, max_rate, is_refundable, is_transferable,
                     annual_cap_local, requires_cultural_test,
                     requires_local_entity, confidence_tier, created_at, updated_at)
                SELECT gen_random_uuid(),
                    (SELECT id FROM jurisdictions WHERE code = :jcode ::varchar LIMIT 1),
                    :pname, :slug, :ptype, 'qualifying_spend',
                    :brate, :mrate, :refund, :transfer,
                    :acap, :cult, :local_ent, :conf, now(), now()
                WHERE (SELECT id FROM jurisdictions WHERE code = :jcode ::varchar LIMIT 1) IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM incentive_programs WHERE slug = :slug ::varchar
                )
            """),
            {
                "jcode": jcode, "pname": pname, "slug": slug, "ptype": ptype,
                "brate": brate, "mrate": mrate, "refund": refund, "transfer": transfer,
                "acap": acap, "cult": cult,
                "local_ent": local_ent, "conf": conf,
            },
        )

    # ------------------------------------------------------------------
    # 5. Program admin details (one per new slug)
    # ------------------------------------------------------------------
    for row in _NEW_PROGRAMS:
        _, _, _, slug, _, _, _, _, _, _, _, _, _, conf, src_title, src_url = row
        label = f"{src_title} ({slug})"
        pay_notes = f"{label} — payment timing not confirmed. DISCOVERY tier."
        notes = (
            f"{label}: DISCOVERY tier. "
            f"Source: {src_url}. "
            "Verify with local film office before budget finalisation."
        )
        conn.execute(
            sa.text("""
                INSERT INTO program_admin_details (
                    id, program_id,
                    payment_timing_weeks, payment_timing_notes,
                    audit_required, audit_authority, audit_cost_estimate_usd,
                    is_assignable, assignability_notes,
                    processing_timeline_weeks, financing_friction_notes,
                    first_window_open_relative, final_claim_deadline,
                    confidence_tier, notes, created_at, updated_at
                )
                SELECT
                    :id, p.id,
                    NULL, :pay_notes,
                    NULL, NULL, NULL,
                    NULL, :assign_notes,
                    NULL, :fin_notes,
                    :window_open, NULL,
                    'DISCOVERY', :notes, :now, :now
                FROM incentive_programs p
                WHERE p.slug = :slug
                  AND NOT EXISTS (
                      SELECT 1 FROM program_admin_details d WHERE d.program_id = p.id
                  )
                LIMIT 1
            """),
            {
                "id": _uid(f"admin:{slug}"),
                "slug": slug,
                "pay_notes": pay_notes,
                "assign_notes": _DISC_ASSIGN_NOTES,
                "fin_notes": _DISC_FIN_NOTES,
                "window_open": _DISC_WINDOW,
                "notes": notes,
                "now": NOW,
            },
        )

    # ------------------------------------------------------------------
    # 6. Spend treatment rows — 21 labour types per new program
    # ------------------------------------------------------------------
    for row in _NEW_PROGRAMS:
        _, _, _, slug, _, _, _, _, _, _, _, _, _, _, _, _ = row
        for labor_type in _LABOR_TYPES:
            qualifies = False if labor_type == "contingency" else None
            notes = _CONTINGENCY_NOTE if labor_type == "contingency" else _UNKNOWN_NOTE
            conn.execute(
                sa.text("""
                    INSERT INTO program_spend_treatments (
                        id, program_id, labor_type,
                        qualifies, treatment_notes, confidence_tier,
                        created_at, updated_at
                    )
                    SELECT
                        :id, p.id, :labor_type,
                        :qualifies, :notes, 'DISCOVERY',
                        :now, :now
                    FROM incentive_programs p
                    WHERE p.slug = :slug
                      AND NOT EXISTS (
                          SELECT 1 FROM program_spend_treatments t
                          WHERE t.program_id = p.id AND t.labor_type = :labor_type ::varchar
                      )
                    LIMIT 1
                """),
                {
                    "id": _uid(f"treatment:{slug}:{labor_type}"),
                    "slug": slug,
                    "labor_type": labor_type,
                    "qualifies": qualifies,
                    "notes": notes,
                    "now": NOW,
                },
            )

    # ------------------------------------------------------------------
    # 7. Fund economics for grant programmes
    # ------------------------------------------------------------------
    for slug, classif, repayable, recoup, equity, soft, govt, max_usd, notes_txt in _GRANT_FUND_ECON:
        conn.execute(
            sa.text("""
                INSERT INTO fund_economics
                    (program_id, is_repayable, is_recoupable,
                     has_equity_participation, stackable_with_incentives,
                     typical_max_award_usd, notes)
                SELECT ip.id, :repay, :recoup, :equity, :govt, :maxusd, :notes
                FROM incentive_programs ip
                WHERE ip.slug = :slug ::varchar
                  AND NOT EXISTS (
                      SELECT 1 FROM fund_economics fe WHERE fe.program_id = ip.id
                  )
            """),
            {
                "slug": slug, "repay": repayable, "recoup": recoup,
                "equity": equity, "govt": not govt,
                "maxusd": max_usd, "notes": notes_txt,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove fund_economics for new grants
    for row in _GRANT_FUND_ECON:
        conn.execute(
            sa.text("DELETE FROM fund_economics WHERE program_slug = :slug"),
            {"slug": row[0]},
        )

    # Remove spend treatments
    for row in _NEW_PROGRAMS:
        slug = row[3]
        for labor_type in _LABOR_TYPES:
            conn.execute(
                sa.text("DELETE FROM program_spend_treatments WHERE id = :id"),
                {"id": _uid(f"treatment:{slug}:{labor_type}")},
            )

    # Remove admin details
    for row in _NEW_PROGRAMS:
        conn.execute(
            sa.text("DELETE FROM program_admin_details WHERE id = :id"),
            {"id": _uid(f"admin:{row[3]}")},
        )

    # Remove programs
    for row in _NEW_PROGRAMS:
        jcode, _, pname, _, _, _, _, _, _, _, _, _, _, _, _, _ = row
        conn.execute(
            sa.text(
                "DELETE FROM incentive_programs "
                "WHERE jurisdiction_code = :jcode AND program_name = :pname"
            ),
            {"jcode": jcode, "pname": pname},
        )

    # Drop territory_classifications table
    op.drop_table("territory_classifications")
