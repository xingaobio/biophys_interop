# Changelog

## Maintenance — 2026-10-02

- Link the published public-limited companion (DOI 10.5281/zenodo.23097835), its offline checker and exact scope.
- Correct default `qc()` uncertainty from `source="calibrated"` to `source="estimated"` with `method="heuristic"`.
  The numeric estimate, QC flags, schema version, 72-rule count and feature dimension are unchanged. Consumers
  filtering by `uncertainty.source` should accept `estimated` for this fallback. The optional fitted-calibrator branch
  retains `source="calibrated"`. CLI output now displays the actual uncertainty source and method.
- Resolve GitHub master once per notebook run, install and record that exact commit, and download the demo from
  that commit. Reject a demo with an unexpected SHA-256. Record runtime versions and verify batch outputs.
- Check the package and every notebook code cell on Python 3.9, 3.12 and 3.13 in GitHub Actions.

The archived v0.1.0 tag and existing Zenodo deposits remain immutable. Maintenance code still reports version
0.1.0; use the recorded Git commit to distinguish it from archived v0.1.0. This entry is not a new tagged release.
