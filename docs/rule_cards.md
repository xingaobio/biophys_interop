# biophys_interop QC rule cards

*Registry export — 72 deterministic, method-aware rules (package v0.1.0, generated 2026-07-02T10:35:52Z).*

## Scope of validation

- **validated** (1 per-record rule): Empirically validated at scale against an independent curator's labels (ChEMBL data_validity_comment; Results §1-2). Per-record: the value-range rule (R1 -> affinity_out_of_range). The duplicate rule (R5b) is also validated but is a dataset-level canonicalization step, not a per-record rule in this registry.

- **literature-grounded** (71 rules): Cited to measurement best practice but not empirically validated here; no repository publishes per-record ground-truth flags for the readout.

- Severity mix: fail 7, warn 65


> A rule that spans multiple modalities is listed under each; the `code` is unique.


## All modalities (generic / cross-cutting)  (14 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `affinity_out_of_range` | warn | validated | lit-jarmoskaite-2020-measure-affinity | verify units / measurement |
| `batch_effect_uncontrolled` | warn | literature-grounded | lit-geng-2016-dacum | include plate/batch controls |
| `buffer_unreported` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | report buffer/ionic strength |
| `cross_assay_pooling_noise` | warn | literature-grounded | lit-landrum-2024-combining-ic50-noise | do not pool IC50/Ki across assays without maximal metadata-matched curation; flag pooled-source records |
| `entity_sequence_missing` | warn | literature-grounded | interop-spec | attach sequence to link structure/features |
| `method_assay_mismatch` | warn | literature-grounded | lit-geng-2016-dacum | record the specific assay_type |
| `ph_unreported` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | report pH |
| `provenance_incomplete` | warn | literature-grounded | interop-spec | record source_db + DOI for traceability |
| `replicate_disagreement` | warn | literature-grounded | chembl-data-validity | exclude the outlier measurement before pooling/calibration |
| `replicate_unreported` | warn | literature-grounded | lit-arsiwala-2025-prophet-ab | report number of replicates |
| `simulated` | warn | literature-grounded | lit-geng-2016-dacum | flag derivation=simulated; keep out of held-out test |
| `single_replicate` | warn | literature-grounded | lit-arsiwala-2025-prophet-ab | replicate for an error estimate |
| `temperature_unreported` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | report temperature (affinity is T-dependent) |
| `uncertainty_unreported` | warn | literature-grounded | lit-patrone-2024-uq-antibody | report measurement uncertainty |

## AUC  (3 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `auc_oligomeric_heterogeneity` | warn | literature-grounded | wiley-appl-70055 | multiple sedimenting species: heterogeneity/aggregation |
| `rh_mw_inconsistent _(+3 modalities)_` | warn | literature-grounded | wiley-febs-16312 | Rh too large for MW: aggregation/elongation |
| `secmals_mw_inconsistent _(+1 modalities)_` | warn | literature-grounded | wiley-appl-70055 | measured MW != sequence MW: unexpected oligomeric state |

## BLI  (15 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `analyte_aggregation _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; re-purify |
| `equilibration _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | distrust KD; extend incubation |
| `kon_implausible _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; kon above diffusion limit |
| `titration_regime _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | treat KD as lower-limit; re-measure with [R]<<KD |
| `active_fraction_unknown _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | measure active fraction by titration |
| `baseline_drift _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | re-reference / re-run (buffer mismatch, evaporation, temperature) |
| `bli_weak_binder_limit` | warn | literature-grounded | wiley-appl-70055 | validate weak (KD>10uM) BLI affinities by SPR |
| `equilibration_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | extend incubation or report apparent KD |
| `kd_kinetics_inconsistent _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | reconcile steady-state vs kinetic KD |
| `koff_unmeasurably_slow _(+4 modalities)_` | warn | literature-grounded | wiley-jmr-1159 | ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS) |
| `mass_transport_limited _(+4 modalities)_` | warn | literature-grounded | wiley-cpz1-1030 | vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density |
| `non_1to1_kinetics _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model |
| `regeneration_loss _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles |
| `steady_state_no_equilibration_proof _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | show time-invariance |
| `titration_regime_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | prefer quadratic fit / lower [R] |

## CD  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `low_thermal_stability _(+2 modalities)_` | warn | literature-grounded | wiley-pro-3622 | low Tm: marginal stability / developability risk |

## DLS  (2 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `high_polydispersity _(+1 modalities)_` | warn | literature-grounded | wiley-appl-70055 | polydisperse: aggregation/heterogeneity; SEC/filter |
| `rh_mw_inconsistent _(+3 modalities)_` | warn | literature-grounded | wiley-febs-16312 | Rh too large for MW: aggregation/elongation |

## DMS  (5 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `dms_dynamic_range_censored` | warn | literature-grounded | lit-matuszewski-2016-dms-design | treat as censored value |
| `dms_epistasis_unaccounted` | warn | literature-grounded | lit-matuszewski-2016-dms-design | model epistasis for multi-mutants |
| `dms_stop_codon_control_missing` | warn | literature-grounded | lit-matuszewski-2016-dms-design | include stop-codon negative control |
| `dms_wt_normalization_missing` | warn | literature-grounded | lit-matuszewski-2016-dms-design | normalize to wild-type |
| `low_read_count` | warn | literature-grounded | lit-matuszewski-2016-dms-design | require min read depth |

## DSC  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `low_thermal_stability _(+2 modalities)_` | warn | literature-grounded | wiley-pro-3622 | low Tm: marginal stability / developability risk |

## FIDA  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `rh_mw_inconsistent _(+3 modalities)_` | warn | literature-grounded | wiley-febs-16312 | Rh too large for MW: aggregation/elongation |

## GCI  (14 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `analyte_aggregation _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; re-purify |
| `equilibration _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | distrust KD; extend incubation |
| `kon_implausible _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; kon above diffusion limit |
| `titration_regime _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | treat KD as lower-limit; re-measure with [R]<<KD |
| `active_fraction_unknown _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | measure active fraction by titration |
| `baseline_drift _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | re-reference / re-run (buffer mismatch, evaporation, temperature) |
| `equilibration_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | extend incubation or report apparent KD |
| `kd_kinetics_inconsistent _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | reconcile steady-state vs kinetic KD |
| `koff_unmeasurably_slow _(+4 modalities)_` | warn | literature-grounded | wiley-jmr-1159 | ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS) |
| `mass_transport_limited _(+4 modalities)_` | warn | literature-grounded | wiley-cpz1-1030 | vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density |
| `non_1to1_kinetics _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model |
| `regeneration_loss _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles |
| `steady_state_no_equilibration_proof _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | show time-invariance |
| `titration_regime_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | prefer quadratic fit / lower [R] |

## HDX-MS  (2 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `hdx_back_exchange_uncontrolled` | warn | literature-grounded | lit-oganesyan-2018-hdx-ms | report/limit back-exchange (maintain low T/pH; include fully-deuterated control) |
| `hdx_low_sequence_coverage` | warn | literature-grounded | lit-oganesyan-2018-hdx-ms | low peptide coverage: interface/epitope call unreliable; improve digestion/coverage |

## ITC  (5 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `itc_c_value_out_of_range` | warn | literature-grounded | lit-upadhyay-2024-itc-spr | tune cell concentration to c in 5-500 |
| `itc_dG_KD_mismatch` | warn | literature-grounded | lit-upadhyay-2024-itc-spr | reconcile dG(dH,dS) with KD |
| `itc_heat_of_dilution_uncorrected` | warn | literature-grounded | lit-upadhyay-2024-itc-spr | subtract heat of dilution |
| `itc_low_enthalpy` | warn | literature-grounded | lit-upadhyay-2024-itc-spr | confirm by orthogonal method |
| `itc_stoichiometry_off` | warn | literature-grounded | lit-upadhyay-2024-itc-spr | check purity / active fraction |

## MST  (17 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `analyte_aggregation _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; re-purify |
| `equilibration _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | distrust KD; extend incubation |
| `kon_implausible _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; kon above diffusion limit |
| `titration_regime _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | treat KD as lower-limit; re-measure with [R]<<KD |
| `active_fraction_unknown _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | measure active fraction by titration |
| `baseline_drift _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | re-reference / re-run (buffer mismatch, evaporation, temperature) |
| `equilibration_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | extend incubation or report apparent KD |
| `kd_kinetics_inconsistent _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | reconcile steady-state vs kinetic KD |
| `koff_unmeasurably_slow _(+4 modalities)_` | warn | literature-grounded | wiley-jmr-1159 | ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS) |
| `mass_transport_limited _(+4 modalities)_` | warn | literature-grounded | wiley-cpz1-1030 | vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density |
| `mst_fluorescence_control_missing` | warn | literature-grounded | wiley-nph-19917 | run an SDS-Test/denaturation control to exclude ligand-induced fluorescence change |
| `mst_labeling_heterogeneity` | warn | literature-grounded | wiley-cpz1-14 | use site-specific labeling; heterogeneous/over-labeling biases KD |
| `mst_low_response_amplitude` | warn | literature-grounded | wiley-cpz1-14 | low Fnorm response: S/N too low for a reliable KD |
| `non_1to1_kinetics _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model |
| `regeneration_loss _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles |
| `steady_state_no_equilibration_proof _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | show time-invariance |
| `titration_regime_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | prefer quadratic fit / lower [R] |

## NMR  (4 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `nmr_restraint_violation_high` | fail | literature-grounded | lit-laurents-2022-af2-nmr | re-examine assignments |
| `nmr_csp_saturation` | warn | literature-grounded | lit-laurents-2022-af2-nmr | titrate to saturation / check fast-exchange |
| `nmr_exchange_broadening` | warn | literature-grounded | lit-laurents-2022-af2-nmr | vary temperature/field |
| `nmr_referencing_unreported` | warn | literature-grounded | lit-laurents-2022-af2-nmr | report DSS/TMS referencing |

## SAXS  (6 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `guinier_upward_curvature` | fail | literature-grounded | lit-grant-2015-saxs | reject; SEC-SAXS |
| `dmax_rg_ratio_anomaly` | warn | literature-grounded | lit-grant-2015-saxs | inspect P(r) / oligomeric state |
| `radiation_damage` | warn | literature-grounded | lit-hopkins-2016-saxs-raddamage | use early frames |
| `rg_inconsistent` | warn | literature-grounded | lit-grant-2015-saxs | inspect data range |
| `saxs_conc_dependence_unchecked` | warn | literature-grounded | lit-grant-2015-saxs | run a dilution series |
| `saxs_mw_inconsistent` | warn | literature-grounded | lit-grant-2015-saxs | check oligomeric state / aggregation |

## SEC-MALS  (3 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `high_polydispersity _(+1 modalities)_` | warn | literature-grounded | wiley-appl-70055 | polydisperse: aggregation/heterogeneity; SEC/filter |
| `rh_mw_inconsistent _(+3 modalities)_` | warn | literature-grounded | wiley-febs-16312 | Rh too large for MW: aggregation/elongation |
| `secmals_mw_inconsistent _(+1 modalities)_` | warn | literature-grounded | wiley-appl-70055 | measured MW != sequence MW: unexpected oligomeric state |

## SPR  (14 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `analyte_aggregation _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; re-purify |
| `equilibration _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | distrust KD; extend incubation |
| `kon_implausible _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; kon above diffusion limit |
| `titration_regime _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | treat KD as lower-limit; re-measure with [R]<<KD |
| `active_fraction_unknown _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | measure active fraction by titration |
| `baseline_drift _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | re-reference / re-run (buffer mismatch, evaporation, temperature) |
| `equilibration_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | extend incubation or report apparent KD |
| `kd_kinetics_inconsistent _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | reconcile steady-state vs kinetic KD |
| `koff_unmeasurably_slow _(+4 modalities)_` | warn | literature-grounded | wiley-jmr-1159 | ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS) |
| `mass_transport_limited _(+4 modalities)_` | warn | literature-grounded | wiley-cpz1-1030 | vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density |
| `non_1to1_kinetics _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model |
| `regeneration_loss _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles |
| `steady_state_no_equilibration_proof _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | show time-invariance |
| `titration_regime_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | prefer quadratic fit / lower [R] |

## XL-MS  (4 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `xlms_distance_violation` | fail | literature-grounded | lit-bullock-2018-xlms-restraints | false crosslink or wrong conformation |
| `xlms_crosslinker_long` | warn | literature-grounded | lit-bullock-2018-xlms-restraints | account for Euclidean vs SASD |
| `xlms_fdr_high` | warn | literature-grounded | lit-stahl-2024-alphalink2-complexes | tighten FDR <= 5% |
| `xlms_monolink_only` | warn | literature-grounded | lit-bullock-2018-xlms-restraints | low structural information |

## cryoEM  (3 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `cryoem_fsc_low` | warn | literature-grounded | lit-lawson-2021-cryoem-validation | check map-model FSC |
| `cryoem_local_resolution_variation` | warn | literature-grounded | lit-lawson-2021-cryoem-validation | report local resolution |
| `cryoem_resolution_insufficient` | warn | literature-grounded | lit-lawson-2021-cryoem-validation | do not claim atomic detail |

## fluorescence_polarization  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `fp_tracer_affinity_mismatch` | warn | literature-grounded | lit-prystay-2001-fp-kd | FP tracer Kd should bracket the measured Kd; mismatch compresses dynamic range |

## mass_photometry  (3 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `mp_concentration_out_of_window` | warn | literature-grounded | lit-wu-2020-mass-photometry-affinity | MP works ~1-100 nM landing rate; outside this, counts are unreliable |
| `mp_low_monomer_fraction` | warn | literature-grounded | lit-foley-2021-mass-photometry-nmeth | low monomer fraction: aggregation/oligomerization; purify or report species-resolved |
| `mp_oligomeric_heterogeneity` | warn | literature-grounded | lit-wu-2020-mass-photometry-affinity | multiple mass species: oligomeric heterogeneity; report the full mass distribution, not one KD |

## nDSF  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `low_thermal_stability _(+2 modalities)_` | warn | literature-grounded | wiley-pro-3622 | low Tm: marginal stability / developability risk |

## native_MS  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `nms_response_factor_uncorrected` | warn | literature-grounded | lit-bui-2024-slomo-nms | gas-phase ion abundance != solution concentration; use SLOMO/response-factor correction before quoting KD |

## smFRET  (1 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `smfret_dye_perturbation_unchecked` | warn | literature-grounded | lit-agam-2022-smfret-blind | check dye-position/photophysics perturbation (Agam 2022 interlab: distance accuracy ~5 A only if controlled) |

## switchSENSE  (14 rules)

| code | severity | tier | basis | recommended action |
|---|---|---|---|---|
| `analyte_aggregation _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; re-purify |
| `equilibration _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | distrust KD; extend incubation |
| `kon_implausible _(+4 modalities)_` | fail | literature-grounded | wiley-appl-70055 | reject; kon above diffusion limit |
| `titration_regime _(+4 modalities)_` | fail | literature-grounded | lit-jarmoskaite-2020-measure-affinity | treat KD as lower-limit; re-measure with [R]<<KD |
| `active_fraction_unknown _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | measure active fraction by titration |
| `baseline_drift _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | re-reference / re-run (buffer mismatch, evaporation, temperature) |
| `equilibration_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | extend incubation or report apparent KD |
| `kd_kinetics_inconsistent _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | reconcile steady-state vs kinetic KD |
| `koff_unmeasurably_slow _(+4 modalities)_` | warn | literature-grounded | wiley-jmr-1159 | ultratight binding; KD a lower bound (SPR-unmeasurable; cf. DFS) |
| `mass_transport_limited _(+4 modalities)_` | warn | literature-grounded | wiley-cpz1-1030 | vary flow rate / compare Langmuir vs Langmuir-mass-transport; lower ligand density |
| `non_1to1_kinetics _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | heterogeneous ligand/multiphasic; try heterogeneous-ligand or bivalent-analyte model |
| `regeneration_loss _(+4 modalities)_` | warn | literature-grounded | wiley-appl-70055 | harsh regeneration denatures ligand -> fluctuating Rmax; down-weight late cycles |
| `steady_state_no_equilibration_proof _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | show time-invariance |
| `titration_regime_marginal _(+4 modalities)_` | warn | literature-grounded | lit-jarmoskaite-2020-measure-affinity | prefer quadratic fit / lower [R] |
