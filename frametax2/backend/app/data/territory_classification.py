"""
territory_classification.py — Comprehensive global territory classification.

Every ISO 3166-1 territory (plus select dependencies and special regions)
is classified into exactly one of four statuses:

  PROGRAMS_FOUND              — ≥1 incentive/support program exists and is in
                                the FrameTax database.
  NO_KNOWN_PROGRAM_FOUND      — Publicly searched; no accessible film incentive
                                or production support program identified.
  PUBLIC_INFORMATION_UNAVAILABLE — Active conflict zone, closed/inaccessible
                                state, or no publicly accessible government
                                information reachable at search time.
  PROGRAM_STATUS_UNCLEAR      — Government cinema body or partial program
                                information found; insufficient detail to add
                                a complete program record.

Each entry carries:
  code        — ISO 3166-1 alpha-2 (or regional grouping code)
  name        — English name
  status      — one of the four values above
  notes       — search evidence, source fragment, or rationale
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TerritoryStatus = Literal[
    "PROGRAMS_FOUND",
    "NO_KNOWN_PROGRAM_FOUND",
    "PUBLIC_INFORMATION_UNAVAILABLE",
    "PROGRAM_STATUS_UNCLEAR",
]


@dataclass(frozen=True)
class TerritoryClassification:
    code: str
    name: str
    status: TerritoryStatus
    notes: str


# ---------------------------------------------------------------------------
# Master list — every entry is mandatory; no territory may be absent.
# ---------------------------------------------------------------------------

ALL_TERRITORIES: list[TerritoryClassification] = [
    # ------------------------------------------------------------------
    # A
    # ------------------------------------------------------------------
    TerritoryClassification("AD", "Andorra", "NO_KNOWN_PROGRAM_FOUND",
        "Andorra has no known national film incentive program. "
        "Cultural output is minimal; no public program registry found. "
        "Source searched: Ministry of Culture of Andorra."),
    TerritoryClassification("AE", "United Arab Emirates", "PROGRAMS_FOUND",
        "Dubai Film & TV Commission rebate (DPI) and ADFC (Abu Dhabi) rebate programs exist. "
        "Seeded in FrameTax DB: AE jurisdiction."),
    TerritoryClassification("AF", "Afghanistan", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict since 2021 Taliban takeover. No accessible public film body or incentive program. "
        "Afghan Film Organisation (Khaad Film) functionally suspended."),
    TerritoryClassification("AG", "Antigua and Barbuda", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive cash program. Antigua Film Office provides "
        "facilitation services only. Source: Antigua Film Office search 2025."),
    TerritoryClassification("AI", "Anguilla", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. No known film production incentive program."),
    TerritoryClassification("AL", "Albania", "PROGRAMS_FOUND",
        "Albanian National Centre of Cinematography (AKSH) grant program. In FrameTax DB: AL."),
    TerritoryClassification("AM", "Armenia", "PROGRAMS_FOUND",
        "National Cinema Centre of Armenia grant program. In FrameTax DB: AM."),
    TerritoryClassification("AO", "Angola", "PROGRAMS_FOUND",
        "Instituto Nacional do Cinema e Audiovisual (INCA) support program. In FrameTax DB: AO."),
    TerritoryClassification("AQ", "Antarctica", "NO_KNOWN_PROGRAM_FOUND",
        "No permanent population; no film incentive program exists or is applicable."),
    TerritoryClassification("AR", "Argentina", "PROGRAMS_FOUND",
        "INCAA (Instituto Nacional de Cine y Artes Audiovisuales) grants and rebates. "
        "In FrameTax DB: AR."),
    TerritoryClassification("AS", "American Samoa", "NO_KNOWN_PROGRAM_FOUND",
        "US unincorporated territory. No known separate film incentive program; "
        "US federal programs may apply."),
    TerritoryClassification("AT", "Austria", "PROGRAMS_FOUND",
        "Austrian Film Institute (ÖFI) grants and ORF Film/Fernsehabkommen. In FrameTax DB: AT."),
    TerritoryClassification("AU", "Australia", "PROGRAMS_FOUND",
        "Producer Offset, Location Offset, PDV Offset, and state funds. In FrameTax DB: AU and sub-nationals."),
    TerritoryClassification("AW", "Aruba", "NO_KNOWN_PROGRAM_FOUND",
        "Dutch constituent country. Aruba Tourism Authority offers facilitation; "
        "no known cash incentive program. Source: Aruba Film Commission search 2025."),
    TerritoryClassification("AX", "Åland Islands", "NO_KNOWN_PROGRAM_FOUND",
        "Finnish autonomous territory. Covered under Finnish programs; no separate Åland incentive."),
    TerritoryClassification("AZ", "Azerbaijan", "PROGRAMS_FOUND",
        "Azerbaijan National Cinema Fund support program. In FrameTax DB: AZ."),
    # ------------------------------------------------------------------
    # B
    # ------------------------------------------------------------------
    TerritoryClassification("BA", "Bosnia and Herzegovina", "PROGRAMS_FOUND",
        "Center for Film of BiH (Centar za Film) grant program. In FrameTax DB: BA."),
    TerritoryClassification("BB", "Barbados", "PROGRAMS_FOUND",
        "Barbados Film Commission support program. In FrameTax DB: BB."),
    TerritoryClassification("BD", "Bangladesh", "PROGRAMS_FOUND",
        "Bangladesh Film Development Corporation (BFDC) support. In FrameTax DB: BD."),
    TerritoryClassification("BE", "Belgium", "PROGRAMS_FOUND",
        "Belgian Tax Shelter and regional funds (Screen Brussels, VAF, Wallimage). "
        "In FrameTax DB: BE and sub-nationals."),
    TerritoryClassification("BF", "Burkina Faso", "PROGRAMS_FOUND",
        "Centre National du Cinéma du Burkina (CNCB) support. "
        "Host of FESPACO. In FrameTax DB: BF."),
    TerritoryClassification("BG", "Bulgaria", "PROGRAMS_FOUND",
        "Bulgarian National Film Centre (NFT) grant program. In FrameTax DB: BG."),
    TerritoryClassification("BH", "Bahrain", "PROGRAMS_FOUND",
        "Bahrain Authority for Culture and Antiquities (BACA) film support. In FrameTax DB: BH."),
    TerritoryClassification("BI", "Burundi", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive or government production support program. "
        "Cinema infrastructure is minimal. Source: ONACOM search."),
    TerritoryClassification("BJ", "Benin", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program. "
        "Film activity exists but no formal production support mechanism identified."),
    TerritoryClassification("BL", "Saint Barthélemy", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas collectivity. No separate film incentive; French national programs may apply."),
    TerritoryClassification("BM", "Bermuda", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. Bermuda Film Office provides facilitation; "
        "no known production rebate program."),
    TerritoryClassification("BN", "Brunei Darussalam", "NO_KNOWN_PROGRAM_FOUND",
        "Brunei Film Commission provides location facilitation. "
        "No known accessible cash rebate or grant program for international productions. "
        "Source: Brunei Film Commission website search 2025."),
    TerritoryClassification("BO", "Bolivia", "NO_KNOWN_PROGRAM_FOUND",
        "CONACINE Bolivia (Consejo Nacional de Cinematografía) has existed but "
        "no publicly accessible active rebate or grant program was found for international use. "
        "Domestic support mechanisms reported but not verifiable online. "
        "Source: CONACINE Bolivia government search 2025."),
    TerritoryClassification("BQ", "Bonaire, Sint Eustatius and Saba", "NO_KNOWN_PROGRAM_FOUND",
        "Dutch special municipalities in the Caribbean. No known separate film incentive."),
    TerritoryClassification("BR", "Brazil", "PROGRAMS_FOUND",
        "ANCINE FSAC (Fundo Setorial do Audiovisual) and Rouanet Law. In FrameTax DB: BR."),
    TerritoryClassification("BS", "Bahamas", "PROGRAMS_FOUND",
        "Bahamas Film Commission production support. In FrameTax DB: BS."),
    TerritoryClassification("BT", "Bhutan", "PROGRAMS_FOUND",
        "Bhutan has a film clearance and production facilitation program. In FrameTax DB: BT."),
    TerritoryClassification("BV", "Bouvet Island", "NO_KNOWN_PROGRAM_FOUND",
        "Uninhabited Norwegian dependency. No film program applicable."),
    TerritoryClassification("BW", "Botswana", "PROGRAMS_FOUND",
        "Botswana Film Commission support program. In FrameTax DB: BW."),
    TerritoryClassification("BY", "Belarus", "PROGRAMS_FOUND",
        "Belarusfilm state studio support program. In FrameTax DB: BY."),
    TerritoryClassification("BZ", "Belize", "NO_KNOWN_PROGRAM_FOUND",
        "Belize Tourism Board supports filming facilitation. "
        "No known cash rebate or direct grant program for film productions. "
        "Source: BTB Film Commission search 2025."),
    # ------------------------------------------------------------------
    # C
    # ------------------------------------------------------------------
    TerritoryClassification("CA", "Canada", "PROGRAMS_FOUND",
        "CPTC, CMF, provincial tax credits (BC, ON, QC, AB, MB, NS, NB, SK, NL, PE). "
        "In FrameTax DB: CA and all sub-nationals."),
    TerritoryClassification("CC", "Cocos (Keeling) Islands", "NO_KNOWN_PROGRAM_FOUND",
        "Australian external territory (40 residents). No film program applicable."),
    TerritoryClassification("CD", "Congo, Democratic Republic of the", "NO_KNOWN_PROGRAM_FOUND",
        "No known accessible film incentive program. "
        "Centre National du Cinéma (CNC-DRC) has limited public information on production support."),
    TerritoryClassification("CF", "Central African Republic", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Ongoing instability limits film infrastructure."),
    TerritoryClassification("CG", "Congo, Republic of the", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program identified. No public film fund website found."),
    TerritoryClassification("CH", "Switzerland", "PROGRAMS_FOUND",
        "Swiss Federal Office of Culture (BAK) film fund, SRG/SSR broadcaster support, "
        "Succès cinéma. In FrameTax DB: CH."),
    TerritoryClassification("CI", "Côte d'Ivoire", "PROGRAMS_FOUND",
        "CAACI / OISC film support program. In FrameTax DB: CI."),
    TerritoryClassification("CK", "Cook Islands", "NO_KNOWN_PROGRAM_FOUND",
        "New Zealand self-governing territory. No separate Cook Islands film incentive identified."),
    TerritoryClassification("CL", "Chile", "PROGRAMS_FOUND",
        "CORFO audiovisual fund and CNTV support. In FrameTax DB: CL."),
    TerritoryClassification("CM", "Cameroon", "PROGRAMS_FOUND",
        "Ministry of Arts and Culture / DFC Cameroon film support. In FrameTax DB: CM."),
    TerritoryClassification("CN", "China", "PROGRAMS_FOUND",
        "China Film Bureau co-production fund and SARFT support. In FrameTax DB: CN."),
    TerritoryClassification("CO", "Colombia", "PROGRAMS_FOUND",
        "Proimágenes Colombia FDC and Colombia Film Commission. In FrameTax DB: CO."),
    TerritoryClassification("CR", "Costa Rica", "PROGRAMS_FOUND",
        "Centro Costarricense de Producción Cinematográfica (CCPC) support. In FrameTax DB: CR."),
    TerritoryClassification("CU", "Cuba", "PROGRAMS_FOUND",
        "ICAIC (Instituto Cubano del Arte e Industria Cinematográficos) support. In FrameTax DB: CU."),
    TerritoryClassification("CV", "Cabo Verde", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive or production grant program. "
        "Festival activity exists but no production support mechanism identified."),
    TerritoryClassification("CW", "Curaçao", "NO_KNOWN_PROGRAM_FOUND",
        "Curaçao Film Commission provides location facilitation, no known cash incentive program."),
    TerritoryClassification("CX", "Christmas Island", "NO_KNOWN_PROGRAM_FOUND",
        "Australian external territory (~1,800 residents). No separate film program."),
    TerritoryClassification("CY", "Cyprus", "PROGRAMS_FOUND",
        "Cinema Advisory Committee (KOE) grant program. In FrameTax DB: CY."),
    TerritoryClassification("CZ", "Czech Republic", "PROGRAMS_FOUND",
        "Czech Film Fund (SFDI) cash rebate and grants. In FrameTax DB: CZ."),
    # ------------------------------------------------------------------
    # D
    # ------------------------------------------------------------------
    TerritoryClassification("DE", "Germany", "PROGRAMS_FOUND",
        "DFFF, MFG, FFF Bayern, Film- und Medienstiftung NRW, MBB, nordmedia, HDF, etc. "
        "In FrameTax DB: DE and sub-nationals."),
    TerritoryClassification("DJ", "Djibouti", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. No government film body website identified."),
    TerritoryClassification("DK", "Denmark", "PROGRAMS_FOUND",
        "Danish Film Institute (DFI) grants. In FrameTax DB: DK and sub-nationals."),
    TerritoryClassification("DM", "Dominica", "NO_KNOWN_PROGRAM_FOUND",
        "Discover Dominica Authority provides facilitation; no cash rebate program found."),
    TerritoryClassification("DO", "Dominican Republic", "PROGRAMS_FOUND",
        "Dominican Film Commission support and Law 108-10. In FrameTax DB: DO."),
    TerritoryClassification("DZ", "Algeria", "PROGRAMS_FOUND",
        "Centre Algérien pour l'Art et l'Industrie Cinématographiques (CAAIC). In FrameTax DB: DZ."),
    # ------------------------------------------------------------------
    # E
    # ------------------------------------------------------------------
    TerritoryClassification("EC", "Ecuador", "PROGRAMS_FOUND",
        "Casa de la Cultura Ecuatoriana / CNCINE support program. In FrameTax DB: EC."),
    TerritoryClassification("EE", "Estonia", "PROGRAMS_FOUND",
        "Estonian Film Institute (EFI) grant program. In FrameTax DB: EE."),
    TerritoryClassification("EG", "Egypt", "PROGRAMS_FOUND",
        "Egyptian Film Support Center (ASBU) and Cairo Film Fund. In FrameTax DB: EG."),
    TerritoryClassification("EH", "Western Sahara", "NO_KNOWN_PROGRAM_FOUND",
        "Disputed territory with no internationally recognised government with a film incentive program."),
    TerritoryClassification("ER", "Eritrea", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Closed state; minimal publicly accessible government information. "
        "No known film incentive or production support program accessible from outside Eritrea."),
    TerritoryClassification("ES", "Spain", "PROGRAMS_FOUND",
        "Spain IFE, Canary Islands ZTLC, regional funds (Catalunya, Andalucía, Euskadi, Galicia, Valencia). "
        "In FrameTax DB: ES and sub-nationals."),
    TerritoryClassification("ET", "Ethiopia", "PROGRAMS_FOUND",
        "Ethiopian Film and Televsion Institute (EFTI) support. In FrameTax DB: ET."),
    # ------------------------------------------------------------------
    # F
    # ------------------------------------------------------------------
    TerritoryClassification("FI", "Finland", "PROGRAMS_FOUND",
        "Finnish Film Foundation (SES) grants and YLE broadcaster fund. In FrameTax DB: FI."),
    TerritoryClassification("FJ", "Fiji", "PROGRAMS_FOUND",
        "Fiji Audio-Visual Commission cash rebate. In FrameTax DB: FJ."),
    TerritoryClassification("FK", "Falkland Islands", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory (~3,000 residents). No film incentive program."),
    TerritoryClassification("FM", "Micronesia, Federated States of", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Small island nation with limited film infrastructure."),
    TerritoryClassification("FO", "Faroe Islands", "PROGRAMS_FOUND",
        "Faroese Film Fund (Filmstøðin) production support. Added to FrameTax DB in migration 0060."),
    TerritoryClassification("FR", "France", "PROGRAMS_FOUND",
        "CNC (TRIP, SOFICA, Advance on Receipts, CNC Animation), PROCIREP, UniFrance. "
        "In FrameTax DB: FR and sub-nationals."),
    # ------------------------------------------------------------------
    # G
    # ------------------------------------------------------------------
    TerritoryClassification("GA", "Gabon", "PROGRAMS_FOUND",
        "CNC Gabon / CENACI production support. In FrameTax DB: GA."),
    TerritoryClassification("GB", "United Kingdom", "PROGRAMS_FOUND",
        "AVEC, HVC, Animation Tax Relief, Children's, High-End TV, and regional funds "
        "(BFI, Screen Scotland, Film Cymru Wales, Northern Ireland Screen). "
        "In FrameTax DB: GB and sub-nationals."),
    TerritoryClassification("GD", "Grenada", "NO_KNOWN_PROGRAM_FOUND",
        "Grenada Tourism Authority provides facilitation. No known cash incentive program."),
    TerritoryClassification("GE", "Georgia", "PROGRAMS_FOUND",
        "Georgian Film Centre grant program and Cash Rebate. In FrameTax DB: GE."),
    TerritoryClassification("GF", "French Guiana", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas region. French national programs (CNC) may apply; "
        "no separate territory-specific incentive identified."),
    TerritoryClassification("GG", "Guernsey", "NO_KNOWN_PROGRAM_FOUND",
        "Crown dependency. No known film incentive program beyond general investment facilitation."),
    TerritoryClassification("GH", "Ghana", "PROGRAMS_FOUND",
        "National Film Authority (NFA) Ghana support program. In FrameTax DB: GH."),
    TerritoryClassification("GI", "Gibraltar", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. No known film production incentive program."),
    TerritoryClassification("GL", "Greenland", "PROGRAMS_FOUND",
        "Greenland Film Institute (GFI) production support grant. "
        "Added to FrameTax DB in migration 0060."),
    TerritoryClassification("GM", "Gambia", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program identified."),
    TerritoryClassification("GN", "Guinea", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program. "
        "BCRG / Ministry of Culture search returned no accessible production fund."),
    TerritoryClassification("GP", "Guadeloupe", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas region. French CNC programs may apply; "
        "no Guadeloupe-specific cash incentive found."),
    TerritoryClassification("GQ", "Equatorial Guinea", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program identified."),
    TerritoryClassification("GR", "Greece", "PROGRAMS_FOUND",
        "EKOME cash rebate and Greek Film Centre (GFC) grants. In FrameTax DB: GR."),
    TerritoryClassification("GS", "South Georgia and the South Sandwich Islands", "NO_KNOWN_PROGRAM_FOUND",
        "Uninhabited British Overseas Territory. No film program applicable."),
    TerritoryClassification("GT", "Guatemala", "PROGRAMS_FOUND",
        "Guatemalan Film Commission / DICINE support. In FrameTax DB: GT."),
    TerritoryClassification("GU", "Guam", "NO_KNOWN_PROGRAM_FOUND",
        "US unincorporated territory. No known separate film incentive; "
        "Guam Film Office provides facilitation only."),
    TerritoryClassification("GW", "Guinea-Bissau", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("GY", "Guyana", "PROGRAMS_FOUND",
        "Guyana Film Commission production support. In FrameTax DB: GY."),
    # ------------------------------------------------------------------
    # H
    # ------------------------------------------------------------------
    TerritoryClassification("HK", "Hong Kong", "PROGRAMS_FOUND",
        "CreateSmart Film Development Fund and HKIFF programme. In FrameTax DB: HK."),
    TerritoryClassification("HM", "Heard Island and McDonald Islands", "NO_KNOWN_PROGRAM_FOUND",
        "Uninhabited Australian external territory. No film program applicable."),
    TerritoryClassification("HN", "Honduras", "NO_KNOWN_PROGRAM_FOUND",
        "Honduran Institute of Anthropology and History (IHAH) and Honducine have been referenced, "
        "but no accessible cash rebate or grant program for international productions found. "
        "Source: Honduras Film Commission search 2025."),
    TerritoryClassification("HR", "Croatia", "PROGRAMS_FOUND",
        "HAVC (Croatian Audiovisual Centre) cash rebate and grants. In FrameTax DB: HR."),
    TerritoryClassification("HT", "Haiti", "NO_KNOWN_PROGRAM_FOUND",
        "No known accessible film incentive program. "
        "Political and humanitarian crisis limits film infrastructure."),
    TerritoryClassification("HU", "Hungary", "PROGRAMS_FOUND",
        "Hungary NFI (National Film Institute) cash rebate and grants. In FrameTax DB: HU."),
    # ------------------------------------------------------------------
    # I
    # ------------------------------------------------------------------
    TerritoryClassification("ID", "Indonesia", "PROGRAMS_FOUND",
        "Badan Perfilman Indonesia (BPI) and BEKRAF / BPFN support. In FrameTax DB: ID."),
    TerritoryClassification("IE", "Ireland", "PROGRAMS_FOUND",
        "Section 481 tax credit, Screen Ireland development/talent funds, RTÉ broadcaster fund. "
        "In FrameTax DB: IE."),
    TerritoryClassification("IL", "Israel", "PROGRAMS_FOUND",
        "Israel Film Fund (IFF) and Makor Foundation grants. In FrameTax DB: IL."),
    TerritoryClassification("IM", "Isle of Man", "PROGRAMS_FOUND",
        "Isle of Man Film equity investment and production support. "
        "Added to FrameTax DB in migration 0060."),
    TerritoryClassification("IN", "India", "PROGRAMS_FOUND",
        "India International Film Incentive (NFDC cash rebate) and Film Facilitation Office. "
        "In FrameTax DB: IN."),
    TerritoryClassification("IO", "British Indian Ocean Territory", "NO_KNOWN_PROGRAM_FOUND",
        "Military installation (Diego Garcia). No permanent civilian population; no film program."),
    TerritoryClassification("IQ", "Iraq", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Iraq National Commission for Cinema has been referenced historically, "
        "but no publicly accessible active incentive program for international productions found. "
        "Ongoing security concerns limit production activity."),
    TerritoryClassification("IR", "Iran", "PROGRAMS_FOUND",
        "Farabi Cinema Foundation support program. In FrameTax DB: IR."),
    TerritoryClassification("IS", "Iceland", "PROGRAMS_FOUND",
        "Iceland Film in Iceland cash rebate (25%) and Icelandic Film Centre grants. "
        "In FrameTax DB: IS."),
    TerritoryClassification("IT", "Italy", "PROGRAMS_FOUND",
        "Italian tax credit (domestic/foreign), APULIA Film Commission, Piedmont, etc. "
        "In FrameTax DB: IT and sub-nationals."),
    # ------------------------------------------------------------------
    # J
    # ------------------------------------------------------------------
    TerritoryClassification("JE", "Jersey", "NO_KNOWN_PROGRAM_FOUND",
        "Crown dependency. No known separate film incentive program."),
    TerritoryClassification("JM", "Jamaica", "PROGRAMS_FOUND",
        "Jamaica Film Commission production support. In FrameTax DB: JM."),
    TerritoryClassification("JO", "Jordan", "PROGRAMS_FOUND",
        "Royal Film Commission (RFC) Jordan cash rebate (up to 50%). In FrameTax DB: JO."),
    TerritoryClassification("JP", "Japan", "PROGRAMS_FOUND",
        "Japan Film Commission (JFC), VIPO, and METI content support. In FrameTax DB: JP."),
    # ------------------------------------------------------------------
    # K
    # ------------------------------------------------------------------
    TerritoryClassification("KE", "Kenya", "PROGRAMS_FOUND",
        "Kenya Film Commission (KFC) production support. In FrameTax DB: KE."),
    TerritoryClassification("KG", "Kyrgyzstan", "NO_KNOWN_PROGRAM_FOUND",
        "State Agency for Cinematography of Kyrgyzstan (Kyrgyz Film) exists as a state studio; "
        "no accessible cash rebate or international grant program identified. "
        "Source: Kyrgyz Film Agency search 2025."),
    TerritoryClassification("KH", "Cambodia", "PROGRAMS_FOUND",
        "Ministry of Culture and Fine Arts / National Film Commission Cambodia. In FrameTax DB: KH."),
    TerritoryClassification("KI", "Kiribati", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Small Pacific island nation."),
    TerritoryClassification("KM", "Comoros", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program."),
    TerritoryClassification("KN", "Saint Kitts and Nevis", "NO_KNOWN_PROGRAM_FOUND",
        "No known cash film incentive program. "
        "St. Kitts Tourism Authority provides filming facilitation only."),
    TerritoryClassification("KP", "Korea, Democratic People's Republic of", "PUBLIC_INFORMATION_UNAVAILABLE",
        "North Korea. Completely inaccessible for international productions. "
        "No publicly accessible information on any incentive program."),
    TerritoryClassification("KR", "Korea, Republic of", "PROGRAMS_FOUND",
        "KOFIC rebate, KOCCA production support, and KTO promotion. In FrameTax DB: KR."),
    TerritoryClassification("KW", "Kuwait", "PROGRAMS_FOUND",
        "National Council for Culture, Arts and Letters (NCCAL) Kuwait support. In FrameTax DB: KW."),
    TerritoryClassification("KY", "Cayman Islands", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. Cayman Islands Film Commission provides facilitation; "
        "no known cash production incentive program."),
    TerritoryClassification("KZ", "Kazakhstan", "PROGRAMS_FOUND",
        "Kazakhfilm state studio support and Arts Fund grants. In FrameTax DB: KZ."),
    # ------------------------------------------------------------------
    # L
    # ------------------------------------------------------------------
    TerritoryClassification("LA", "Lao PDR", "PROGRAM_STATUS_UNCLEAR",
        "Lao National Film Center (Department of Cinema, Ministry of Information, Culture and Tourism) "
        "has been referenced, but no accessible public rebate or grant program details were found. "
        "Film production activity is increasing. Recommend re-checking LAO film body annually. "
        "Source: Ministry of Information and Culture Lao PDR search 2025."),
    TerritoryClassification("LB", "Lebanon", "PROGRAMS_FOUND",
        "Ministry of Culture Lebanon / Liban Art film support. In FrameTax DB: LB."),
    TerritoryClassification("LC", "Saint Lucia", "NO_KNOWN_PROGRAM_FOUND",
        "Invest Saint Lucia and the Saint Lucia Tourist Board offer location facilitation; "
        "no known film-specific cash rebate program."),
    TerritoryClassification("LI", "Liechtenstein", "NO_KNOWN_PROGRAM_FOUND",
        "Principality of Liechtenstein. No known film incentive program; "
        "Liechtenstein does not have its own film commission or fund."),
    TerritoryClassification("LK", "Sri Lanka", "PROGRAMS_FOUND",
        "National Film Corporation (NFC) Sri Lanka support. In FrameTax DB: LK."),
    TerritoryClassification("LR", "Liberia", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("LS", "Lesotho", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("LT", "Lithuania", "PROGRAMS_FOUND",
        "Lithuanian Film Centre (LKC) grant program. In FrameTax DB: LT."),
    TerritoryClassification("LU", "Luxembourg", "PROGRAMS_FOUND",
        "Film Fund Luxembourg (LUFF) production support and tax credit. In FrameTax DB: LU."),
    TerritoryClassification("LV", "Latvia", "PROGRAMS_FOUND",
        "National Film Centre of Latvia (NKC) grant program. In FrameTax DB: LV."),
    TerritoryClassification("LY", "Libya", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict and fragmented governance. "
        "No publicly accessible film incentive program identified."),
    # ------------------------------------------------------------------
    # M
    # ------------------------------------------------------------------
    TerritoryClassification("MA", "Morocco", "PROGRAMS_FOUND",
        "Centre Cinématographique Marocain (CCM) cash rebate and grants. In FrameTax DB: MA."),
    TerritoryClassification("MC", "Monaco", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program. "
        "No film commission or fund found for the Principality of Monaco."),
    TerritoryClassification("MD", "Moldova", "PROGRAMS_FOUND",
        "National Cinema Centre of Moldova grant program. In FrameTax DB: MD."),
    TerritoryClassification("ME", "Montenegro", "PROGRAMS_FOUND",
        "Montenegrin Film Agency (MFA) production support. In FrameTax DB: ME."),
    TerritoryClassification("MF", "Saint Martin (French Part)", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas collectivity. No separate island-specific film incentive."),
    TerritoryClassification("MG", "Madagascar", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program. No government film body website found."),
    TerritoryClassification("MH", "Marshall Islands", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Small Pacific island nation."),
    TerritoryClassification("MK", "North Macedonia", "PROGRAMS_FOUND",
        "Macedonian Film Agency (AFF) grant program. In FrameTax DB: MK."),
    TerritoryClassification("ML", "Mali", "NO_KNOWN_PROGRAM_FOUND",
        "Centre National de la Cinématographie du Mali (CNCM) has been referenced, "
        "but no accessible active grant program for international productions found."),
    TerritoryClassification("MM", "Myanmar", "PROGRAM_STATUS_UNCLEAR",
        "Myanmar Motion Picture Organisation (MMPO) exists as a state entity. "
        "Following the 2021 coup, international production activity is suspended. "
        "No accessible incentive program details found. "
        "Status uncertain pending political normalisation."),
    TerritoryClassification("MN", "Mongolia", "PROGRAMS_FOUND",
        "Mongolian State Production Film Support. In FrameTax DB: MN."),
    TerritoryClassification("MO", "Macao", "PROGRAMS_FOUND",
        "Macao Film Development Fund. In FrameTax DB: MO."),
    TerritoryClassification("MP", "Northern Mariana Islands", "NO_KNOWN_PROGRAM_FOUND",
        "US Commonwealth territory in the Pacific. No known separate film incentive program."),
    TerritoryClassification("MQ", "Martinique", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas region. French CNC programs may apply; "
        "no Martinique-specific cash incentive found."),
    TerritoryClassification("MR", "Mauritania", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("MS", "Montserrat", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. No known film incentive program."),
    TerritoryClassification("MT", "Malta", "PROGRAMS_FOUND",
        "Malta Film Commission cash rebate (40%). In FrameTax DB: MT."),
    TerritoryClassification("MU", "Mauritius", "PROGRAMS_FOUND",
        "Mauritius Film Development Corporation cash rebate. In FrameTax DB: MU."),
    TerritoryClassification("MV", "Maldives", "PROGRAMS_FOUND",
        "Maldives Integrated Tourism Development Corporation film support. In FrameTax DB: MV."),
    TerritoryClassification("MW", "Malawi", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("MX", "Mexico", "PROGRAMS_FOUND",
        "IMCINE Fondo para la Producción Cinematográfica (FOPROCINE/FIDECINE) and EFICINE 226. "
        "In FrameTax DB: MX."),
    TerritoryClassification("MY", "Malaysia", "PROGRAMS_FOUND",
        "FINAS (National Film Development Corporation Malaysia) cash rebate and grants. "
        "In FrameTax DB: MY."),
    TerritoryClassification("MZ", "Mozambique", "PROGRAMS_FOUND",
        "Instituto Nacional de Cinema de Moçambique (INAC) support. In FrameTax DB: MZ."),
    # ------------------------------------------------------------------
    # N
    # ------------------------------------------------------------------
    TerritoryClassification("NA", "Namibia", "PROGRAMS_FOUND",
        "Namibia Film Commission support program. In FrameTax DB: NA."),
    TerritoryClassification("NC", "New Caledonia", "NO_KNOWN_PROGRAM_FOUND",
        "French special collectivity. Limited local film incentive; "
        "French national programs may apply. No NC-specific cash rebate found."),
    TerritoryClassification("NE", "Niger", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("NF", "Norfolk Island", "NO_KNOWN_PROGRAM_FOUND",
        "Australian external territory. No separate film program."),
    TerritoryClassification("NG", "Nigeria", "PROGRAMS_FOUND",
        "National Film and Video Censors Board (NFVCB) and Nollywood support programs. "
        "In FrameTax DB: NG."),
    TerritoryClassification("NI", "Nicaragua", "NO_KNOWN_PROGRAM_FOUND",
        "INCINE (Instituto Nicaragüense de Cine) has existed; "
        "no accessible active production grant program for international use found. "
        "Source: INCINE Nicaragua search 2025."),
    TerritoryClassification("NL", "Netherlands", "PROGRAMS_FOUND",
        "Netherlands Film Fund (NFF) co-production and development grants. In FrameTax DB: NL."),
    TerritoryClassification("NO", "Norway", "PROGRAMS_FOUND",
        "Norwegian Film Institute (NFI) grants, regional funds, "
        "and Norwegian broadcaster support (NRK). In FrameTax DB: NO and sub-nationals."),
    TerritoryClassification("NP", "Nepal", "NO_KNOWN_PROGRAM_FOUND",
        "National Film Development Board (NFDB) Nepal has been referenced, "
        "but no accessible international grant or rebate program found. "
        "Source: Nepal Film Development Board search 2025."),
    TerritoryClassification("NR", "Nauru", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Very small island nation (~10,000 residents)."),
    TerritoryClassification("NU", "Niue", "NO_KNOWN_PROGRAM_FOUND",
        "New Zealand associated state. No known separate film incentive program."),
    TerritoryClassification("NZ", "New Zealand", "PROGRAMS_FOUND",
        "Screen Production Grant (International/Domestic), NZ On Air broadcaster support. "
        "In FrameTax DB: NZ."),
    # ------------------------------------------------------------------
    # O
    # ------------------------------------------------------------------
    TerritoryClassification("OM", "Oman", "PROGRAMS_FOUND",
        "Oman Film Commission (Royal Opera House) production support. In FrameTax DB: OM."),
    # ------------------------------------------------------------------
    # P
    # ------------------------------------------------------------------
    TerritoryClassification("PA", "Panama", "PROGRAMS_FOUND",
        "Panama Film Commission support. In FrameTax DB: PA."),
    TerritoryClassification("PE", "Peru", "PROGRAMS_FOUND",
        "DAFO Peru (Dirección del Audiovisual, la Fonografía y los Nuevos Medios) grants. "
        "In FrameTax DB: PE."),
    TerritoryClassification("PF", "French Polynesia", "NO_KNOWN_PROGRAM_FOUND",
        "French collectivity. Tahiti has attracted productions; "
        "no accessible cash rebate or formal grant program found. "
        "Source: Tahiti Tourisme film facilitation search 2025."),
    TerritoryClassification("PG", "Papua New Guinea", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program. "
        "National Film Institute (NFI PNG) provides classification services only."),
    TerritoryClassification("PH", "Philippines", "PROGRAMS_FOUND",
        "Film Development Council of the Philippines (FDCP) grant program. In FrameTax DB: PH."),
    TerritoryClassification("PK", "Pakistan", "PROGRAMS_FOUND",
        "Pakistan Film Commission cash rebate (20%). Added to FrameTax DB in migration 0060."),
    TerritoryClassification("PL", "Poland", "PROGRAMS_FOUND",
        "Polish Film Institute (PISF) grants and cash rebate. In FrameTax DB: PL."),
    TerritoryClassification("PM", "Saint Pierre and Miquelon", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas collectivity. No separate film incentive program."),
    TerritoryClassification("PN", "Pitcairn", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory (~50 residents). No film program applicable."),
    TerritoryClassification("PS", "Palestine, State of", "PROGRAM_STATUS_UNCLEAR",
        "Palestine Cinema Fund (PCF) / Palestinian Cinema Center (PCC) exists and has awarded grants. "
        "However, operational continuity and accessible program details are uncertain "
        "given ongoing conflict. Recommend monitoring PCC/PCF for accessible program details. "
        "Source: Palestinian Cinema Center website search 2025."),
    TerritoryClassification("PT", "Portugal", "PROGRAMS_FOUND",
        "ICA (Instituto do Cinema e Audiovisual) grants and ICA cash rebate. In FrameTax DB: PT."),
    TerritoryClassification("PW", "Palau", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Small Pacific island nation."),
    TerritoryClassification("PY", "Paraguay", "PROGRAMS_FOUND",
        "CONACINE Paraguay (Consejo Nacional del Cine) Fondo de Fomento Cinematográfico. "
        "Added to FrameTax DB in migration 0060."),
    # ------------------------------------------------------------------
    # Q
    # ------------------------------------------------------------------
    TerritoryClassification("QA", "Qatar", "PROGRAMS_FOUND",
        "Doha Film Institute (DFI) grants and co-production funds. In FrameTax DB: QA."),
    # ------------------------------------------------------------------
    # R
    # ------------------------------------------------------------------
    TerritoryClassification("RE", "Réunion", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas department. French CNC programs may apply; "
        "no Réunion-specific incentive found."),
    TerritoryClassification("RO", "Romania", "PROGRAMS_FOUND",
        "Romanian National Cinema Centre (CNC) grants. In FrameTax DB: RO."),
    TerritoryClassification("RS", "Serbia", "PROGRAMS_FOUND",
        "Serbia Film Commission cash rebate (25%). In FrameTax DB: RS."),
    TerritoryClassification("RU", "Russian Federation", "PROGRAMS_FOUND",
        "Fond Kino (Cinema Fund Russia) grants. In FrameTax DB: RU."),
    TerritoryClassification("RW", "Rwanda", "PROGRAMS_FOUND",
        "Rwanda Film Centre production support. In FrameTax DB: RW."),
    # ------------------------------------------------------------------
    # S
    # ------------------------------------------------------------------
    TerritoryClassification("SA", "Saudi Arabia", "PROGRAMS_FOUND",
        "Saudi Film Commission cash rebate (40%) and development grants. "
        "In FrameTax DB: SA and SA-KSA."),
    TerritoryClassification("SB", "Solomon Islands", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program."),
    TerritoryClassification("SC", "Seychelles", "PROGRAMS_FOUND",
        "Seychelles Tourism Board film facilitation / production support. In FrameTax DB: SC."),
    TerritoryClassification("SD", "Sudan", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict since April 2023. No accessible film incentive program."),
    TerritoryClassification("SE", "Sweden", "PROGRAMS_FOUND",
        "Swedish Film Institute (SFI) grants and regional funds. "
        "In FrameTax DB: SE and sub-nationals."),
    TerritoryClassification("SG", "Singapore", "PROGRAMS_FOUND",
        "IMDA (Infocomm Media Development Authority) Digital Media Fund and MCI grants. "
        "In FrameTax DB: SG."),
    TerritoryClassification("SH", "Saint Helena, Ascension and Tristan da Cunha", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory (approx. 5,000 total residents across islands). "
        "No film incentive program."),
    TerritoryClassification("SI", "Slovenia", "PROGRAMS_FOUND",
        "Slovenian Film Centre (SFC) grant program. In FrameTax DB: SI."),
    TerritoryClassification("SJ", "Svalbard and Jan Mayen", "NO_KNOWN_PROGRAM_FOUND",
        "Norwegian territories. Covered under Norwegian programs if applicable; "
        "no separate Svalbard film incentive."),
    TerritoryClassification("SK", "Slovakia", "PROGRAMS_FOUND",
        "Slovak Film Institute (SFI) / ASFK grants. In FrameTax DB: SK."),
    TerritoryClassification("SL", "Sierra Leone", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("SM", "San Marino", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program for the Republic of San Marino."),
    TerritoryClassification("SN", "Senegal", "PROGRAMS_FOUND",
        "FOPICA (Fonds de Promotion de l'Industrie Cinématographique) Senegal. In FrameTax DB: SN."),
    TerritoryClassification("SO", "Somalia", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict and fragmented governance. No accessible film incentive program."),
    TerritoryClassification("SR", "Suriname", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("SS", "South Sudan", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict. No accessible film incentive or production support program."),
    TerritoryClassification("ST", "São Tomé and Príncipe", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program."),
    TerritoryClassification("SV", "El Salvador", "NO_KNOWN_PROGRAM_FOUND",
        "CONCULTURA (Consejo Nacional para la Cultura y el Arte) has existed; "
        "no accessible cash production incentive found. Source: El Salvador culture ministry search 2025."),
    TerritoryClassification("SX", "Sint Maarten", "NO_KNOWN_PROGRAM_FOUND",
        "Dutch constituent country. No known separate film incentive program."),
    TerritoryClassification("SY", "Syrian Arab Republic", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict since 2011. No accessible film incentive program."),
    TerritoryClassification("SZ", "Eswatini", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    # ------------------------------------------------------------------
    # T
    # ------------------------------------------------------------------
    TerritoryClassification("TC", "Turks and Caicos Islands", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. TCI Film Commission provides facilitation; "
        "no known cash production incentive."),
    TerritoryClassification("TD", "Chad", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("TF", "French Southern Territories", "NO_KNOWN_PROGRAM_FOUND",
        "Uninhabited French territories. No film program applicable."),
    TerritoryClassification("TG", "Togo", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("TH", "Thailand", "PROGRAMS_FOUND",
        "Thailand Incentive Film Program (20% cash rebate). In FrameTax DB: TH."),
    TerritoryClassification("TJ", "Tajikistan", "NO_KNOWN_PROGRAM_FOUND",
        "Tajikfilm state studio exists; no accessible international production incentive found."),
    TerritoryClassification("TK", "Tokelau", "NO_KNOWN_PROGRAM_FOUND",
        "New Zealand non-self-governing territory. No film program applicable."),
    TerritoryClassification("TL", "Timor-Leste", "NO_KNOWN_PROGRAM_FOUND",
        "No known national film incentive program."),
    TerritoryClassification("TM", "Turkmenistan", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Highly closed state. No publicly accessible information on film incentive programs."),
    TerritoryClassification("TN", "Tunisia", "PROGRAMS_FOUND",
        "Centre National du Cinéma et de l'Image (CNCI) Tunisia grants. In FrameTax DB: TN."),
    TerritoryClassification("TO", "Tonga", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Small Pacific island nation."),
    TerritoryClassification("TR", "Türkiye", "PROGRAMS_FOUND",
        "Ministry of Culture and Tourism Turkey Cinema Support Fund and TRT broadcaster. "
        "In FrameTax DB: TR."),
    TerritoryClassification("TT", "Trinidad and Tobago", "PROGRAMS_FOUND",
        "Trinidad and Tobago Film Company (FilmTT) cash rebate. In FrameTax DB: TT."),
    TerritoryClassification("TV", "Tuvalu", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program. Very small island nation (~11,000 residents)."),
    TerritoryClassification("TW", "Taiwan, Province of China", "PROGRAMS_FOUND",
        "Taiwan Film and Audiovisual Institute (TFAI) cash rebate and grants. In FrameTax DB: TW."),
    TerritoryClassification("TZ", "Tanzania", "PROGRAMS_FOUND",
        "Tanzania Film Board (TFB) production support. In FrameTax DB: TZ."),
    # ------------------------------------------------------------------
    # U
    # ------------------------------------------------------------------
    TerritoryClassification("UA", "Ukraine", "PROGRAMS_FOUND",
        "Ukrainian State Film Agency (Derzhkino) grants. In FrameTax DB: UA. "
        "Note: Operations impacted by Russian invasion since Feb 2022; program status may vary."),
    TerritoryClassification("UG", "Uganda", "PROGRAMS_FOUND",
        "Uganda Film Services film support program. In FrameTax DB: UG."),
    TerritoryClassification("UM", "United States Minor Outlying Islands", "NO_KNOWN_PROGRAM_FOUND",
        "Uninhabited US territories. No film program applicable."),
    TerritoryClassification("US", "United States", "PROGRAMS_FOUND",
        "State-level tax credits (GA, NY, CA, LA, NM, OR, WA, IL, NC, MA, CT, PA, MD, VA, CO, "
        "TN, OK, AL, KY, HI, UT, MN, TX, NV, AZ, MS, SC, RI, PR, VI) plus federal development. "
        "In FrameTax DB: US and all sub-nationals."),
    TerritoryClassification("UY", "Uruguay", "PROGRAMS_FOUND",
        "ICAU (Instituto del Cine y Audiovisual del Uruguay) grants. In FrameTax DB: UY."),
    TerritoryClassification("UZ", "Uzbekistan", "PROGRAMS_FOUND",
        "Uzbekkino state film agency support. In FrameTax DB: UZ."),
    # ------------------------------------------------------------------
    # V
    # ------------------------------------------------------------------
    TerritoryClassification("VA", "Holy See", "NO_KNOWN_PROGRAM_FOUND",
        "Vatican City / Holy See. No film incentive program."),
    TerritoryClassification("VC", "Saint Vincent and the Grenadines", "NO_KNOWN_PROGRAM_FOUND",
        "No known cash film incentive program."),
    TerritoryClassification("VE", "Venezuela", "PROGRAMS_FOUND",
        "CNAC (Centro Nacional Autónomo de Cinematografía) grants. In FrameTax DB: VE. "
        "Note: Economic crisis may affect program operability."),
    TerritoryClassification("VG", "Virgin Islands, British", "NO_KNOWN_PROGRAM_FOUND",
        "British Overseas Territory. No known separate film incentive program."),
    TerritoryClassification("VI", "Virgin Islands, U.S.", "NO_KNOWN_PROGRAM_FOUND",
        "US territory. No known separate VI-specific film incentive beyond US federal."),
    TerritoryClassification("VN", "Viet Nam", "PROGRAMS_FOUND",
        "Vietnam National Cinema Center (VDAC) and Vietnam Film Commission. In FrameTax DB: VN."),
    TerritoryClassification("VU", "Vanuatu", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program."),
    # ------------------------------------------------------------------
    # W
    # ------------------------------------------------------------------
    TerritoryClassification("WF", "Wallis and Futuna", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas collectivity. No separate film incentive program."),
    TerritoryClassification("WS", "Samoa", "NO_KNOWN_PROGRAM_FOUND",
        "No known film incentive program."),
    # ------------------------------------------------------------------
    # X (non-ISO but significant)
    # ------------------------------------------------------------------
    TerritoryClassification("XK", "Kosovo", "PROGRAMS_FOUND",
        "Kosovo Cinematography Center (QKK — Qendra Kinematografike e Kosovës) production grants. "
        "Added to FrameTax DB in migration 0060."),
    # ------------------------------------------------------------------
    # Y
    # ------------------------------------------------------------------
    TerritoryClassification("YE", "Yemen", "PUBLIC_INFORMATION_UNAVAILABLE",
        "Active conflict since 2015. No accessible film incentive or production support program."),
    TerritoryClassification("YT", "Mayotte", "NO_KNOWN_PROGRAM_FOUND",
        "French overseas department. No separate film incentive program."),
    # ------------------------------------------------------------------
    # Z
    # ------------------------------------------------------------------
    TerritoryClassification("ZA", "South Africa", "PROGRAMS_FOUND",
        "NFVF incentive, DTI cash rebate, and DTIC support. In FrameTax DB: ZA."),
    TerritoryClassification("ZM", "Zambia", "PROGRAMS_FOUND",
        "National Arts Council of Zambia film support. In FrameTax DB: ZM."),
    TerritoryClassification("ZW", "Zimbabwe", "PROGRAMS_FOUND",
        "Zimbabwe Film Council (ZFC) production support. In FrameTax DB: ZW."),
    # ------------------------------------------------------------------
    # Regional / Supranational groupings (in DB as special codes)
    # ------------------------------------------------------------------
    TerritoryClassification("EU", "European Union", "PROGRAMS_FOUND",
        "Eurimages, MEDIA Fund (Creative Europe), AVMSD obligations. In FrameTax DB: EU."),
    TerritoryClassification("ACP", "African, Caribbean and Pacific Group", "PROGRAMS_FOUND",
        "ACP–EU co-production fund. In FrameTax DB: ACP."),
    TerritoryClassification("IBERO", "Ibero-American Region", "PROGRAMS_FOUND",
        "Ibermedia Programme (multilateral co-production fund). In FrameTax DB: IBERO."),
    TerritoryClassification("NORDIC", "Nordic Region", "PROGRAMS_FOUND",
        "Nordic Film & TV Fund (NFTF). In FrameTax DB: NORDIC."),
]


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_BY_CODE: dict[str, TerritoryClassification] = {t.code: t for t in ALL_TERRITORIES}


def get_classification(code: str) -> TerritoryClassification | None:
    return _BY_CODE.get(code)


def get_by_status(status: TerritoryStatus) -> list[TerritoryClassification]:
    return [t for t in ALL_TERRITORIES if t.status == status]


PROGRAMS_FOUND_CODES: frozenset[str] = frozenset(
    t.code for t in ALL_TERRITORIES if t.status == "PROGRAMS_FOUND"
)
NO_KNOWN_PROGRAM_CODES: frozenset[str] = frozenset(
    t.code for t in ALL_TERRITORIES if t.status == "NO_KNOWN_PROGRAM_FOUND"
)
PUBLIC_INFO_UNAVAILABLE_CODES: frozenset[str] = frozenset(
    t.code for t in ALL_TERRITORIES if t.status == "PUBLIC_INFORMATION_UNAVAILABLE"
)
PROGRAM_STATUS_UNCLEAR_CODES: frozenset[str] = frozenset(
    t.code for t in ALL_TERRITORIES if t.status == "PROGRAM_STATUS_UNCLEAR"
)

# New program codes added specifically in migration 0060
NEW_IN_0060: frozenset[str] = frozenset({"FO", "GL", "IM", "PK", "PY", "XK"})
