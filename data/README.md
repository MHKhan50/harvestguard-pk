# Data directory

- `synthetic_crop_panel.csv` — generated, simulated smoke-test data. **Not real Pakistan observations.**
- `SYNTHETIC_DATA_NOTICE.md` — provenance and safe-use notice.
- `pbs_crop_panel.csv` — created locally by `fetch-pbs`; not bundled in this ZIP.

For the real-source workflow, run `python -m pip install -e '.[data]'` and then `python -m harvestguard_pk.cli fetch-pbs --output data/pbs_crop_panel.csv`. Record retrieval date and source checksum before research publication.
