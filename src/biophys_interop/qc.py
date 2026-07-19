"""qc(record) -> record + QC flags + calibrated uncertainty (INTEROP_SPEC §5).

The program's MOAT: biophysics judgment distilled into deterministic, method-aware rules. Each rule is a
registry entry with a literature/best-practice `basis` and an `action`. Adding a new "Xin rule" = append one
`@rule(...)` function. `RULES` currently holds 72 method-aware rules (RULE_COUNT) spanning the 24-modality
schema: all-modality/generic (14), cross-modality (18), SAXS (6), ITC (5), DMS (5), NMR (4), XL-MS (4),
MST (3), cryoEM (3), mass photometry (3), HDX-MS (2), and BLI / AUC / native MS / smFRET /
fluorescence polarization (1 each). RULE_COUNT is the single source of truth — cite it, not a frozen number.

Literature bases used (corpus work_ids):
  lit-jarmoskaite-2020-measure-affinity, lit-patrone-2024-uq-antibody, lit-geng-2016-dacum,
  lit-tsishyn-2023-ddg-biases, lit-miller-2023-aff-features, lit-arsiwala-2025-prophet-ab
"""
from __future__ import annotations
import math

LN2 = math.log(2.0)
KIN = frozenset({"SPR", "BLI", "MST", "GCI", "switchSENSE"})   # surface/solution label-free kinetics families
_CV = {"SPR": 0.15, "BLI": 0.20, "MST": 0.25, "ITC": 0.15, "SAXS": 0.10, "DMS": 0.30,
       "NMR": 0.10, "XL-MS": 0.20, "cryoEM": 0.10, "GCI": 0.15, "mass_photometry": 0.20,
       "fluorescence_polarization": 0.20, "native_MS": 0.20, "HDX-MS": 0.25, "smFRET": 0.20,
       "DSC": 0.15, "switchSENSE": 0.20, "other": 0.25}

RULES: list[dict] = []


def rule(code, modalities, severity, basis, action):
    def deco(fn):
        RULES.append({"code": code, "modalities": modalities, "severity": severity,
                      "basis": basis, "action": action, "check": fn})
        return fn
    return deco


def _num(x):
    return x if isinstance(x, (int, float)) else None


# ───────────────────────── SPR / BLI / MST ─────────────────────────
@rule("titration_regime", KIN, "fail", "lit-jarmoskaite-2020-measure-affinity", "treat KD as lower-limit; re-measure with [R]<<KD")
def _r(rec):
    m = rec["measurement"]; KD = _num(m.get("KD")); tr = _num(m.get("trace_conc") or m.get("limiting_conc"))
    if KD and tr and tr >= KD:
        return f"trace conc {tr:.2e} M >= KD {KD:.2e} M: titration regime; KD is only a lower bound."
    return False

@rule("titration_regime_marginal", KIN, "warn", "lit-jarmoskaite-2020-measure-affinity", "prefer quadratic fit / lower [R]")
def _r(rec):
    m = rec["measurement"]; KD = _num(m.get("KD")); tr = _num(m.get("trace_conc") or m.get("limiting_conc"))
    if KD and tr and KD / 10 <= tr < KD:
        return f"[R]/KD={tr/KD:.2f} (not <<1): possible intermediate regime."
    return False

@rule("equilibration", KIN, "fail", "lit-jarmoskaite-2020-measure-affinity", "distrust KD; extend incubation")
def _r(rec):
    m = rec["measurement"]; koff = _num(m.get("koff")); t = _num(m.get("incubation_time"))
    if koff and t and t < (5 * LN2 / koff) / 5:
        return f"incubation {t:.0f}s << 5 half-lives ({5*LN2/koff:.0f}s): far from equilibrium."
    return False

@rule("equilibration_marginal", KIN, "warn", "lit-jarmoskaite-2020-measure-affinity", "extend incubation or report apparent KD")
def _r(rec):
    m = rec["measurement"]; koff = _num(m.get("koff")); t = _num(m.get("incubation_time"))
    if koff and t and (5 * LN2 / koff) / 5 <= t < 5 * LN2 / koff:
        return f"incubation {t:.0f}s < 5 half-lives ({5*LN2/koff:.0f}s)."
    return False

@rule("mass_transport_limited", KIN, "warn", "wiley-cpz1-1030", "vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density")
def _r(rec):
    kon = _num(rec["measurement"].get("kon"))
    return f"kon {kon:.1e} 1/Ms near diffusion limit." if kon and kon > 1e7 else False

@rule("kon_implausible", KIN, "fail", "wiley-appl-70055", "reject; kon above diffusion limit")
def _r(rec):
    kon = _num(rec["measurement"].get("kon"))
    return f"kon {kon:.1e} 1/Ms exceeds physical diffusion limit (~1e9)." if kon and kon > 1e8 else False

@rule("koff_unmeasurably_slow", KIN, "warn", "wiley-jmr-1159", "ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS)")
def _r(rec):
    koff = _num(rec["measurement"].get("koff"))
    return f"koff {koff:.1e} 1/s very slow: dissociation hard to measure." if koff and koff < 1e-5 else False

@rule("kd_kinetics_inconsistent", KIN, "warn", "wiley-appl-70055", "reconcile steady-state vs kinetic KD")
def _r(rec):
    m = rec["measurement"]; KD = _num(m.get("KD")); kon = _num(m.get("kon")); koff = _num(m.get("koff"))
    if KD and kon and koff and koff > 0 and kon > 0:
        pred = koff / kon
        if pred > 0 and abs(math.log10(KD) - math.log10(pred)) > 0.5:
            return f"KD {KD:.2e} != koff/kon {pred:.2e} (>3x)."
    return False

@rule("non_1to1_kinetics", KIN, "warn", "wiley-appl-70055", "heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model")
def _r(rec):
    m = rec["measurement"]; chi2 = _num(m.get("chi2")); rmax = _num(m.get("Rmax"))
    return "high fit residual: 1:1 model may not hold." if chi2 and rmax and chi2 > 0.1 * rmax else False

@rule("steady_state_no_equilibration_proof", KIN, "warn", "lit-jarmoskaite-2020-measure-affinity", "show time-invariance")
def _r(rec):
    m = rec["measurement"]
    return "steady-state KD without koff or incubation time: equilibration unproven." \
        if (m.get("KD") and not m.get("koff") and not m.get("incubation_time")) else False

@rule("active_fraction_unknown", KIN, "warn", "lit-jarmoskaite-2020-measure-affinity", "measure active fraction by titration")
def _r(rec):
    return "active protein fraction not reported." if "active_fraction" not in rec.get("_qc_inputs", {}) else False

@rule("baseline_drift", KIN, "warn", "wiley-appl-70055", "re-reference / re-run (buffer mismatch, evaporation, temperature)")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("baseline_drift", False) and "baseline drift flagged."

@rule("regeneration_loss", KIN, "warn", "wiley-appl-70055", "harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("regeneration_loss", False) and "surface regeneration loss flagged."

@rule("analyte_aggregation", KIN, "fail", "wiley-appl-70055", "reject; re-purify")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("aggregation", False) and "analyte aggregation flagged."

@rule("bli_weak_binder_limit", {"BLI"}, "warn", "wiley-appl-70055", "validate weak (KD>10uM) BLI affinities by SPR")
def _r(rec):
    KD = _num(rec["measurement"].get("KD"))
    return f"BLI KD {KD:.1e} M > 10 uM near BLI weak-binder limit: validate by SPR." if KD and KD > 1e-5 else False

@rule("mst_low_response_amplitude", {"MST"}, "warn", "wiley-cpz1-14", "low Fnorm response: S/N too low for a reliable KD")
def _r(rec):
    a = _num(rec["measurement"].get("response_amplitude"))
    return f"MST response amplitude {a:.1f} < 5: S/N too low for reliable KD." if a is not None and a < 5 else False

@rule("mst_fluorescence_control_missing", {"MST"}, "warn", "wiley-nph-19917", "run an SDS-Test/denaturation control to exclude ligand-induced fluorescence change")
def _r(rec):
    return ("sds_test" not in rec.get("_qc_inputs", {})) and "no SDS-Test reported: ligand-induced fluorescence-change artifact not excluded."

@rule("mst_labeling_heterogeneity", {"MST"}, "warn", "wiley-cpz1-14", "use site-specific labeling; heterogeneous/over-labeling biases KD")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("labeling_homogeneous") is False and "heterogeneous fluorescent labeling: biases MST KD."


# ───────────────────────── ITC ─────────────────────────
@rule("itc_low_enthalpy", {"ITC"}, "warn", "lit-upadhyay-2024-itc-spr", "confirm by orthogonal method")
def _r(rec):
    dH = _num(rec["measurement"].get("dH"))
    return f"|dH|={abs(dH):.2f} kcal/mol low: ITC may miss binding." if dH is not None and abs(dH) < 1.0 else False

@rule("itc_stoichiometry_off", {"ITC"}, "warn", "lit-upadhyay-2024-itc-spr", "check purity / active fraction")
def _r(rec):
    n = _num(rec["measurement"].get("n"))
    return f"n={n:.2f} far from integer." if n is not None and abs(n - round(n)) > 0.2 else False

@rule("itc_c_value_out_of_range", {"ITC"}, "warn", "lit-upadhyay-2024-itc-spr", "tune cell concentration to c in 5-500")
def _r(rec):
    m = rec["measurement"]; KD = _num(m.get("KD")); cell = _num(m.get("cell_conc"))
    if KD and cell and KD > 0:
        c = cell / KD
        if c < 1 or c > 1000:
            return f"Wiseman c={c:.1f} outside 1-1000: KD poorly constrained."
    return False

@rule("itc_dG_KD_mismatch", {"ITC"}, "warn", "lit-upadhyay-2024-itc-spr", "reconcile dG(dH,dS) with KD")
def _r(rec):
    m = rec["measurement"]; KD = _num(m.get("KD")); dH = _num(m.get("dH")); dS = _num(m.get("dS"))
    T = _num((rec.get("conditions") or {}).get("temperature_K")) or 298.15
    if KD and dH is not None and dS is not None and KD > 0:
        try:
            dG = dH - T * dS / 1000.0          # kcal/mol (dS in cal/mol/K)
            kd_pred = math.exp(dG * 1000.0 / (1.987 * T))
            if kd_pred > 0 and abs(math.log10(KD) - math.log10(kd_pred)) > 1.0:
                return f"KD {KD:.2e} inconsistent with dG from dH/dS (~{kd_pred:.2e})."
        except (ValueError, OverflowError):
            return False
    return False

@rule("itc_heat_of_dilution_uncorrected", {"ITC"}, "warn", "lit-upadhyay-2024-itc-spr", "subtract heat of dilution")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("heat_of_dilution_corrected") is False and "heat of dilution not corrected."


# ───────────────────────── SAXS ─────────────────────────
@rule("guinier_upward_curvature", {"SAXS"}, "fail", "lit-grant-2015-saxs", "reject; SEC-SAXS")
def _r(rec):
    m = rec["measurement"]; gq = _num(m.get("guinier_quality"))
    if rec.get("_qc_inputs", {}).get("aggregation") or (gq is not None and gq < 0.9):
        return "Guinier upturn / poor quality: aggregation likely."
    return False

@rule("radiation_damage", {"SAXS"}, "warn", "lit-hopkins-2016-saxs-raddamage", "use early frames")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("radiation_damage", False) and "radiation damage flagged."

@rule("rg_inconsistent", {"SAXS"}, "warn", "lit-grant-2015-saxs", "inspect data range")
def _r(rec):
    m = rec["measurement"]; rg = _num(m.get("Rg")); rgp = _num(m.get("rg_from_pr"))
    return "Rg(Guinier) vs Rg(P(r)) disagree >10%." if rg and rgp and abs(rg - rgp) / rg > 0.1 else False

@rule("saxs_conc_dependence_unchecked", {"SAXS"}, "warn", "lit-grant-2015-saxs", "run a dilution series")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("dilution_series") is False and "no dilution series: interparticle interference risk."

@rule("dmax_rg_ratio_anomaly", {"SAXS"}, "warn", "lit-grant-2015-saxs", "inspect P(r) / oligomeric state")
def _r(rec):
    m = rec["measurement"]; dmax = _num(m.get("Dmax")); rg = _num(m.get("Rg"))
    if dmax and rg and rg > 0:
        r = dmax / rg
        if r < 2.0 or r > 4.5:
            return f"Dmax/Rg={r:.2f} atypical (globular ~2.5-3.5)."
    return False

@rule("saxs_mw_inconsistent", {"SAXS"}, "warn", "lit-grant-2015-saxs", "check oligomeric state / aggregation")
def _r(rec):
    m = rec["measurement"]; mw_i0 = _num(m.get("mw_from_i0")); mw_seq = _num(m.get("mw_sequence"))
    return "MW(I0) inconsistent with sequence MW (>30%)." if mw_i0 and mw_seq and abs(mw_i0 - mw_seq) / mw_seq > 0.3 else False


# ───────────────────────── NMR ─────────────────────────
@rule("nmr_referencing_unreported", {"NMR"}, "warn", "lit-laurents-2022-af2-nmr", "report DSS/TMS referencing")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("referencing_reported") is False and "chemical-shift referencing not reported."

@rule("nmr_csp_saturation", {"NMR"}, "warn", "lit-laurents-2022-af2-nmr", "titrate to saturation / check fast-exchange")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("csp_saturation", False) and "CSP near saturation: KD poorly defined."

@rule("nmr_restraint_violation_high", {"NMR"}, "fail", "lit-laurents-2022-af2-nmr", "re-examine assignments")
def _r(rec):
    v = _num(rec["measurement"].get("restraint_violation"))
    return f"restraint violation {v:.2f} A high." if v is not None and v > 0.5 else False

@rule("nmr_exchange_broadening", {"NMR"}, "warn", "lit-laurents-2022-af2-nmr", "vary temperature/field")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("exchange_broadening", False) and "intermediate-exchange broadening flagged."


# ───────────────────────── XL-MS ─────────────────────────
@rule("xlms_fdr_high", {"XL-MS"}, "warn", "lit-stahl-2024-alphalink2-complexes", "tighten FDR <= 5%")
def _r(rec):
    fdr = _num(rec["measurement"].get("fdr"))
    return f"crosslink FDR {fdr:.0%} > 5%." if fdr is not None and fdr > 0.05 else False

@rule("xlms_crosslinker_long", {"XL-MS"}, "warn", "lit-bullock-2018-xlms-restraints", "account for Euclidean vs SASD")
def _r(rec):
    d = _num(rec["measurement"].get("max_distance"))
    return f"crosslinker max distance {d:.0f} A long: restraint ambiguous." if d is not None and d > 35 else False

@rule("xlms_monolink_only", {"XL-MS"}, "warn", "lit-bullock-2018-xlms-restraints", "low structural information")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("monolink_only", False) and "only mono-links: limited distance info."

@rule("xlms_distance_violation", {"XL-MS"}, "fail", "lit-bullock-2018-xlms-restraints", "false crosslink or wrong conformation")
def _r(rec):
    m = rec["measurement"]; obs = _num(m.get("model_distance")); mx = _num(m.get("max_distance"))
    return f"model Ca-Ca {obs:.0f} A > crosslinker max+tol." if obs and mx and obs > mx + 5 else False


# ───────────────────────── cryoEM ─────────────────────────
@rule("cryoem_resolution_insufficient", {"cryoEM"}, "warn", "lit-lawson-2021-cryoem-validation", "do not claim atomic detail")
def _r(rec):
    res = _num(rec["measurement"].get("resolution"))
    return f"resolution {res:.1f} A > 4 A: atomic claims unsupported." if res is not None and res > 4.0 else False

@rule("cryoem_fsc_low", {"cryoEM"}, "warn", "lit-lawson-2021-cryoem-validation", "check map-model FSC")
def _r(rec):
    fsc = _num(rec["measurement"].get("map_model_fsc"))
    return f"map-model FSC {fsc:.2f} low." if fsc is not None and fsc < 0.5 else False

@rule("cryoem_local_resolution_variation", {"cryoEM"}, "warn", "lit-lawson-2021-cryoem-validation", "report local resolution")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("local_resolution_variation", False) and "large local-resolution variation."


# ───────────────────────── DMS ─────────────────────────
@rule("low_read_count", {"DMS"}, "warn", "lit-matuszewski-2016-dms-design", "require min read depth")
def _r(rec):
    rc = _num(rec["measurement"].get("read_count"))
    return f"read_count={rc} low: noisy fitness." if rc is not None and rc < 50 else False

@rule("dms_stop_codon_control_missing", {"DMS"}, "warn", "lit-matuszewski-2016-dms-design", "include stop-codon negative control")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("stop_codon_control") is False and "no stop-codon negative control."

@rule("dms_wt_normalization_missing", {"DMS"}, "warn", "lit-matuszewski-2016-dms-design", "normalize to wild-type")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("wt_normalization") is False and "fitness not normalized to wild-type."

@rule("dms_dynamic_range_censored", {"DMS"}, "warn", "lit-matuszewski-2016-dms-design", "treat as censored value")
def _r(rec):
    f = _num(rec["measurement"].get("fitness"))
    return "fitness near assay floor/ceiling: censored." if f is not None and (f <= -3 or f >= 3) else False

@rule("dms_epistasis_unaccounted", {"DMS"}, "warn", "lit-matuszewski-2016-dms-design", "model epistasis for multi-mutants")
def _r(rec):
    mut = rec["measurement"].get("mutation")
    return "multi-mutation entry: epistasis unmodeled." if isinstance(mut, str) and ("," in mut or ";" in mut) else False


# ─────────────── solution-state size/shape/dispersity (AUC/FIDA/DLS/SEC-MALS/nDSF) ───────────────
@rule("high_polydispersity", {"DLS", "SEC-MALS"}, "warn", "wiley-appl-70055", "polydisperse: aggregation/heterogeneity; SEC/filter")
def _r(rec):
    pdi = _num(rec["measurement"].get("PDI"))
    return f"PDI={pdi:.2f} > 0.2: polydisperse (aggregation/heterogeneity)." if pdi is not None and pdi > 0.2 else False

@rule("rh_mw_inconsistent", {"FIDA", "DLS", "SEC-MALS", "AUC"}, "warn", "wiley-febs-16312", "Rh too large for MW: aggregation/elongation")
def _r(rec):
    m = rec["measurement"]; rh = _num(m.get("Rh")); mw = _num(m.get("MW")) or _num(m.get("mw_sequence"))
    if rh and mw and mw > 0:
        exp = 0.0515 * (mw ** 0.392)          # nm; folded-globular Rh-MW relation (Erickson 2009)
        if rh > 1.5 * exp:
            return f"Rh {rh:.1f} nm >> expected {exp:.1f} nm for MW {mw:.0f} Da: aggregation/elongation."
    return False

@rule("secmals_mw_inconsistent", {"SEC-MALS", "AUC"}, "warn", "wiley-appl-70055", "measured MW != sequence MW: unexpected oligomeric state")
def _r(rec):
    m = rec["measurement"]; mw = _num(m.get("MW")); seq = _num(m.get("mw_sequence"))
    return f"MW {mw:.0f} vs sequence {seq:.0f} differ >30%: check oligomeric state." if mw and seq and abs(mw - seq) / seq > 0.3 else False

@rule("auc_oligomeric_heterogeneity", {"AUC"}, "warn", "wiley-appl-70055", "multiple sedimenting species: heterogeneity/aggregation")
def _r(rec):
    n = _num(rec["measurement"].get("n_species"))
    return f"{int(n)} sedimenting species: oligomeric heterogeneity / aggregation." if n is not None and n > 1 else False

@rule("low_thermal_stability", {"nDSF", "DSC", "CD"}, "warn", "wiley-pro-3622", "low Tm: marginal stability / developability risk")
def _r(rec):
    tm = _num(rec["measurement"].get("Tm"))
    return f"Tm {tm:.0f} C < 40 C: marginal thermal stability." if tm is not None and tm < 40 else False


# ─────────────── round-3 modalities: native MS / HDX-MS / smFRET / FP / DSC ───────────────
@rule("nms_response_factor_uncorrected", {"native_MS"}, "warn", "lit-bui-2024-slomo-nms",
      "gas-phase ion abundance != solution concentration; use SLOMO/response-factor correction before quoting KD")
def _r(rec):
    qi = rec.get("_qc_inputs", {})
    has_kd = _num(rec["measurement"].get("KD")) is not None
    return has_kd and qi.get("response_factor_corrected") is False and "native-MS KD without response-factor correction: abundance!=concentration bias."

@rule("hdx_low_sequence_coverage", {"HDX-MS"}, "warn", "lit-oganesyan-2018-hdx-ms",
      "low peptide coverage: interface/epitope call unreliable; improve digestion/coverage")
def _r(rec):
    cov = _num(rec["measurement"].get("sequence_coverage"))
    return f"HDX peptide coverage {cov:.0%} < 70%: interface mapping incomplete." if cov is not None and cov < 0.7 else False

@rule("hdx_back_exchange_uncontrolled", {"HDX-MS"}, "warn", "lit-oganesyan-2018-hdx-ms",
      "report/limit back-exchange (maintain low T/pH; include fully-deuterated control)")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("back_exchange_control") is False and "no back-exchange control: deuterium-uptake values not corrected."

@rule("smfret_dye_perturbation_unchecked", {"smFRET"}, "warn", "lit-agam-2022-smfret-blind",
      "check dye-position/photophysics perturbation (Agam 2022 interlab: distance accuracy ~5 A only if controlled)")
def _r(rec):
    return rec.get("_qc_inputs", {}).get("dye_perturbation_checked") is False and "smFRET dye perturbation not assessed: distance/efficiency may be biased."

@rule("fp_tracer_affinity_mismatch", {"fluorescence_polarization"}, "warn", "lit-prystay-2001-fp-kd",
      "FP tracer Kd should bracket the measured Kd; mismatch compresses dynamic range")
def _r(rec):
    qi = rec.get("_qc_inputs", {}); kd = _num(rec["measurement"].get("KD")); tkd = _num(qi.get("tracer_kd"))
    if kd and tkd and (tkd > 100 * kd or tkd < 0.01 * kd):
        return "FP tracer Kd far from analyte Kd: poor dynamic range / unreliable fit."
    return False


# ─────────────── mass photometry (single-molecule mass, label-free, in solution) ───────────────
@rule("mp_oligomeric_heterogeneity", {"mass_photometry"}, "warn", "lit-wu-2020-mass-photometry-affinity",
      "multiple mass species: oligomeric heterogeneity; report the full mass distribution, not one KD")
def _r(rec):
    n = _num(rec["measurement"].get("n_species"))
    return f"{int(n)} mass species resolved by MP: heterogeneous sample / multivalent complex." if n is not None and n > 1 else False

@rule("mp_low_monomer_fraction", {"mass_photometry"}, "warn", "lit-foley-2021-mass-photometry-nmeth",
      "low monomer fraction: aggregation/oligomerization; purify or report species-resolved")
def _r(rec):
    mf = _num(rec["measurement"].get("monomer_fraction"))
    return f"monomer fraction {mf:.0%} < 80%: significant oligomer/aggregate population." if mf is not None and mf < 0.8 else False

@rule("mp_concentration_out_of_window", {"mass_photometry"}, "warn", "lit-wu-2020-mass-photometry-affinity",
      "MP works ~1-100 nM landing rate; outside this, counts are unreliable")
def _r(rec):
    c = _num((rec.get("conditions") or {}).get("analyte_conc_M"))
    return f"MP analyte conc {c:.1e} M outside ~1e-9..1e-7 working window: unreliable particle counting." if c is not None and (c < 1e-9 or c > 1e-7) else False


# ───────────────────────── cross-modality ─────────────────────────
@rule("simulated", "*", "warn", "lit-geng-2016-dacum", "flag derivation=simulated; keep out of held-out test")
def _r(rec):
    return rec.get("provenance", {}).get("derivation") == "simulated" and "simulated signal: exclude from clean test."

@rule("temperature_unreported", "*", "warn", "lit-jarmoskaite-2020-measure-affinity", "report temperature (affinity is T-dependent)")
def _r(rec):
    return (rec.get("conditions") or {}).get("temperature_K") is None and "temperature not reported."

@rule("ph_unreported", "*", "warn", "lit-jarmoskaite-2020-measure-affinity", "report pH")
def _r(rec):
    return (rec.get("conditions") or {}).get("pH") is None and "pH not reported."

@rule("buffer_unreported", "*", "warn", "lit-jarmoskaite-2020-measure-affinity", "report buffer/ionic strength")
def _r(rec):
    return not (rec.get("conditions") or {}).get("buffer") and "buffer/ionic strength not reported."

@rule("affinity_out_of_range", "*", "warn", "lit-jarmoskaite-2020-measure-affinity", "verify units / measurement")
def _r(rec):
    KD = _num(rec["measurement"].get("KD"))
    return f"KD {KD:.2e} M outside plausible 1e-15..1e-2." if KD and (KD < 1e-15 or KD > 1e-2) else False

@rule("uncertainty_unreported", "*", "warn", "lit-patrone-2024-uq-antibody", "report measurement uncertainty")
def _r(rec):
    return not isinstance((rec.get("uncertainty") or {}).get("value"), (int, float)) and "no reported uncertainty (estimated floor used)."

@rule("single_replicate", "*", "warn", "lit-arsiwala-2025-prophet-ab", "replicate for an error estimate")
def _r(rec):
    n = _num(rec.get("n_replicates"))
    return f"only {int(n)} replicate(s): no robust error estimate." if n is not None and n < 2 else False

@rule("replicate_unreported", "*", "warn", "lit-arsiwala-2025-prophet-ab", "report number of replicates")
def _r(rec):
    return rec.get("n_replicates") is None and "number of replicates not reported."

@rule("entity_sequence_missing", "*", "warn", "interop-spec", "attach sequence to link structure/features")
def _r(rec):
    return not (rec.get("entity") or {}).get("sequence") and "entity sequence missing: cannot link to structure/features."

@rule("provenance_incomplete", "*", "warn", "interop-spec", "record source_db + DOI for traceability")
def _r(rec):
    p = rec.get("provenance", {})
    return (not p.get("doi") or p.get("source_db") in (None, "unknown")) and "provenance incomplete (source_db/DOI)."

@rule("method_assay_mismatch", "*", "warn", "lit-geng-2016-dacum", "record the specific assay_type")
def _r(rec):
    at = rec.get("assay_type")
    return (not at or at == rec.get("modality")) and "assay_type not specified beyond modality."

@rule("batch_effect_uncontrolled", "*", "warn", "lit-geng-2016-dacum", "include plate/batch controls")
def _r(rec):
    qi = rec.get("_qc_inputs", {})
    return (qi.get("batch_id") is not None and not qi.get("batch_control")) and "batch id present but no batch control."

@rule("cross_assay_pooling_noise", "*", "warn", "lit-landrum-2024-combining-ic50-noise",
      "do not pool IC50/Ki across assays without maximal metadata-matched curation; flag pooled-source records")
def _r(rec):
    # _qc_inputs.pooled_assays = number of distinct assays merged for this (target, ligand) value.
    # Landrum 2024 (JCIM): minimally-curated cross-assay IC50 pooling -> 65% of pairs differ >0.3 log, 27% >1 log,
    # Kendall tau ~0.51; "maximal curation" (match assay metadata) raises tau to ~0.71. Kalliokoski 2013: Ki->IC50 offset ~2x.
    n = _num(rec.get("_qc_inputs", {}).get("pooled_assays"))
    mt = rec["measurement"].get("type") or rec.get("standard_type")
    if n is not None and n > 1 and (mt in (None, "IC50", "Ki", "Kd", "KD")):
        return f"value pooled across {int(n)} assays: cross-assay noise (Landrum 2024: ~27% of such pairs differ >1 log); curate by matched assay metadata."
    return False

@rule("replicate_disagreement", "*", "warn", "chembl-data-validity", "exclude the outlier measurement before pooling/calibration")
def _r(rec):
    # _qc_inputs.replicate_log_range = ln(max/min) across repeated measurements of the same (entity, variant/ligand)
    rng = rec.get("_qc_inputs", {}).get("replicate_log_range")
    if rng and rng >= LN2 * (math.log2(100)):   # >= 100x spread
        fold = math.exp(min(rng, 30))
        return f">={fold:.0f}x disagreement among repeated measurements of this pair: likely transcription/range error in one."
    return False


# ───────────────────────── runner ─────────────────────────
def _primary_value(rec):
    m = rec["measurement"]
    for k in ("KD", "ddG", "fitness", "Rg", "I0"):
        if isinstance(m.get(k), (int, float)):
            return k, float(m[k])
    return None, None


def qc(record: dict, calibrator=None) -> dict:
    rec = dict(record)
    mod = rec.get("modality", "other")
    reasons: list[dict] = []
    for r in RULES:
        if r["modalities"] != "*" and mod not in r["modalities"]:
            continue
        out = r["check"](rec)
        if out:
            reasons.append({"code": r["code"], "severity": r["severity"],
                            "message": out if isinstance(out, str) else r["action"],
                            "basis": r["basis"], "action": r["action"]})

    n_warn = sum(1 for r in reasons if r["severity"] == "warn")
    n_fail = sum(1 for r in reasons if r["severity"] == "fail")
    key, val = _primary_value(rec)
    reported = (rec.get("uncertainty") or {}).get("value")
    flag = "fail" if n_fail else ("warn" if n_warn else "pass")
    rec["qc"] = {"flag": flag, "score": round(max(0.0, 1.0 - (0.2 * n_warn + 0.5 * n_fail)), 3),
                 "reasons": reasons, "n_warn": n_warn, "n_fail": n_fail}
    if calibrator is not None:                       # fitted model (preferred)
        cal_val, rel = calibrator.predict_uncertainty(rec)
        rec["uncertainty"] = {"value": cal_val, "type": "std", "source": "calibrated",
                              "method": "model", "applies_to": key,
                              "rel_error": round(rel, 4), "reported": reported}
    else:                                            # hand-tuned fallback
        base = reported if isinstance(reported, (int, float)) else (abs(val) * _CV.get(mod, 0.25) if val else None)
        inflate = 1.0 + 0.5 * n_warn + 1.0 * n_fail
        rec["uncertainty"] = {"value": (base * inflate) if base is not None else None, "type": "std",
                              "source": "calibrated", "method": "heuristic", "applies_to": key,
                              "inflation_factor": round(inflate, 2), "reported": reported}
    return rec


RULE_COUNT = len(RULES)
