# ML Validation Internship

This project builds a small decision-support pipeline for sales data. It runs baseline analytics, generates a simulation result for a price-change scenario, scores the risk, validates the model outputs, and generates a PDF report every time `main.py` runs.

## What the project does

- Loads the sales dataset from `data/sales_data.csv`
- Computes baseline analytics with `dt_ml.baseline_analytics`
- Runs a price-change simulation with `dt_ml.simulation_engine`
- Scores the decision with `dt_ml.risk_scorer`
- Validates predictions with the shared validation utilities
- Generates a report PDF at `validation_report.pdf`

## Project layout

- `main.py` - main entry point that runs the pipeline and generates the PDF
- `config.py` - shared scenario and ground-truth configuration
- `dt_ml/` - analytics, simulation, risk, and validation modules
- `data/` - CSV files used by the project
- `tests/` - lightweight test functions for the core logic

## Requirements

- Python 3.14 or later
- `pandas`
- `scikit-learn`
- `reportlab`

## Setup

Install the dependencies in your environment:

```bash
pip install pandas scikit-learn reportlab
```

If you want to run the tests with `pytest`, also install it:

```bash
pip install pytest
```

## Run the project

Execute the main script:

```bash
python main.py
```

This prints the baseline analytics, simulation result, validation metrics, and risk score to the console. It also generates or overwrites `validation_report.pdf` in the project root.

## Run checks

If `pytest` is installed, you can run the test suite with:

```bash
pytest
```

If you do not have `pytest`, you can still run `main.py` directly to validate the end-to-end flow.

## Report output

The PDF report includes:

- Dataset coverage summary
- Validation metrics and thresholds
- Risk analysis with color coding
- A section that mirrors the runtime instance result from `main.py`

## Notes

- The current implementation focuses on the price-change scenario.
- The report uses A4 size and Times-family fonts.
- Low-risk outcomes are highlighted in green, and risky outcomes are highlighted in red.

