# Release verification record

Release candidate: `0.1.0`  
Verification date: 2026-11-10

- Unit tests: **11 passed** using Python 3.13.5.
- Python compatibility: all package and test modules parsed successfully using the Python 3.9 grammar. A Python 3.9 interpreter was not installed in the build environment, so execution under 3.9 itself was not directly tested here.
- End-to-end smoke run: completed with the bundled synthetic panel; the command produced `metrics.json`, `test_predictions.csv` and `run_metadata.json` in a temporary output directory.
- Synthetic input: 5,244 valid panel rows and 4,884 supervised examples in the checked fixture. These are simulated software-test records, not empirical Pakistan observations.
- External PBS-derived Parquet download/conversion: **not executed in this build environment**. The source catalogue and download URL were verified from the published dataset page, but no official-source file is bundled and no real-data model score is claimed.
- Archive integrity: checked separately on the delivered ZIP using `unzip -t` and Python's `ZipFile.testzip()`.
