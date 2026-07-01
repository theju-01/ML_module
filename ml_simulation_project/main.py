from pathlib import Path
import logging
from datetime import datetime
import pandas as pd
from config import ground_truth, scenarios
from dt_ml.baseline_analytics import compute
from dt_ml.risk_scorer import score
from dt_ml.simulation_engine import run
from dt_ml.validation import validate_model
from dt_ml.validation.report_builder import build_validation_report
from memory_cleaner import clear_memory
import time

start_time = time.time()

PROJECT_ROOT = Path(__file__).resolve().parent      
logger = logging.getLogger(__name__)
now = datetime.now()

def load_dataset(file_path):
    logger.info("TEMP START load_dataset file=%s", file_path)
    df = pd.read_csv(file_path)
    logger.info("TEMP END load_dataset shape=%s rows=%s cols=%s", df.shape, len(df), len(df.columns))
    return df


def price_model_wrapper(test_df, parameter, magnitude, magnitude_type):
    #this function is a wrapper around the simulation engine to run the price change
    # scenario with the given parameters and return the predicted KPIs.
    return run(
        df=test_df,
        decision_type="price_change",
        parameter=parameter,
        magnitude=magnitude,
        magnitude_type=magnitude_type,
    )


def main():
    logger.info("TEMP START main")
    print("_" * 50)

    data_path = PROJECT_ROOT / "data" / "sales_data.csv"
    df = load_dataset(data_path)

    logger.info("TEMP main input shape=%s rows=%s cols=%s", df.shape, len(df), len(df.columns))
    print("Baseline Analytics:")
    baseline = compute(df)
    print(baseline)
    logger.info("TEMP main baseline complete keys=%s", list(baseline.keys()))
    print("_" * 50)

    print("\nSimulation Result:")
    logger.info("TEMP main running simulation")
    simulation_result = run(
        df=df,
        decision_type="price_change",
        parameter="price_per_unit",
        magnitude=10,
        magnitude_type="percentage",
    )
    print(simulation_result)
    logger.info("TEMP main simulation complete keys=%s", list(simulation_result.keys()))
    print("_" * 50)

    print("\nValidation Results:")
    logger.info("TEMP main running validation scenarios=%s", len(scenarios))
    validation_results = validate_model(
        price_model_wrapper,
        test_df=df,
        scenarios=scenarios,
        ground_truth=ground_truth,
    )
    for metric, value in validation_results.items():
        print(f"{metric}: {value}")
    logger.info("TEMP main validation complete keys=%s", list(validation_results.keys()))
    print("_" * 50)

    print("\nRisk Score:")
    logger.info("TEMP main running risk scoring")
    risk = score(
        "price_change",
        10,
        simulation_result,
    )
    print(risk)
    logger.info("TEMP main risk complete keys=%s", list(risk.keys()))
    print("_" * 50)

    report_path = PROJECT_ROOT / now.strftime("validation_report_%d-%m-%Y_%H-%M.pdf")

    logger.info("TEMP main generating report path=%s", report_path)
    generated_report = build_validation_report(output_path=str(report_path))           
    print(f"\nPDF report generated: {generated_report}")
    print("_" * 50)

    logger.info("TEMP main clearing memory")
    clear_memory()

    end_time = time.time()
    logger.info("TEMP END main execution time=%.2f seconds", end_time - start_time)


if __name__ == "__main__":
    main()