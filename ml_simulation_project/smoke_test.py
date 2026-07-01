import pandas as pd
from memory_cleaner import clear_memory

from dt_ml.simulation_engine import run
from dt_ml.baseline_analytics import compute
from dt_ml.risk_scorer import score


def main():

    print("\nLoading dataset...\n")

    df = pd.read_csv("data/sales_data.csv")

    print(df.head())

    print("\nRunning baseline analytics...\n")

    baseline = compute(df)

    print(baseline)

    print("\nRunning simulation...\n")

    result = run(
        df=df,
        decision_type="price_change",
        parameter="price_per_unit",
        magnitude=10,
        magnitude_type="percentage",
    )

    print("\nSimulation Result:\n")

    print(result)
    print("\nRunning risk scoring...\n")

    risk = score(
    "price_change",
    10,
    result,
    )

    print(risk)
    clear_memory()

if __name__ == "__main__":
    main()
