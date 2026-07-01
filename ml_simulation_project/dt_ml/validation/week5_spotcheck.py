from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dt_ml.simulation_engine import run
from dt_ml.risk_scorer import score
from dt_ml.validation.week5_plausibility import check_all_plausibility
from dt_ml.validation.week5_issues_logger import Week5IssueLogger
import json
from datetime import datetime
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data"

def load_test_datasets():
    test_data_path = DATA_PATH
    datasets = {}
    
    required_files = [
        "sales_data.csv",
        "hr_data.csv",
        "marketing_data.csv",
    ]
    
    for file in required_files:
        file_path = os.path.join(test_data_path, file)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            datasets[file.replace('.csv', '')] = df
        else:
            print(f"Warning: {file} not found in {test_data_path}")
    
    if not datasets:
        print("Creating fallback test datasets...")
        datasets = create_fallback_datasets()
    
    return datasets

def create_fallback_datasets():
    datasets = {}
    
    clean_df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=36, freq='ME'),
        'revenue': [100000 + i * 3000 for i in range(36)],
        'units_sold': [2000 - i * 10 for i in range(36)],
        'price_per_unit': [50 + (i % 6) * 2 for i in range(36)],
    })
    datasets['sales_data'] = clean_df
    
    hr_df = pd.DataFrame({
        'employee_id': [f'EMP-{1000 + i}' for i in range(24)],
        'role': ['Engineer'] * 24,
        'salary': [70000 + (i % 4) * 2500 for i in range(24)],
        'hire_date': pd.date_range('2022-01-01', periods=24, freq='ME'),
        'department': ['Engineering'] * 24,
    })
    datasets['hr_data'] = hr_df

    marketing_df = pd.DataFrame({
        'campaign_id': [f'CMP-{100 + i}' for i in range(24)],
        'budget': [20000 + (i % 6) * 1500 for i in range(24)],
        'leads': [1500 + (i % 5) * 100 for i in range(24)],
        'conversions': [100 + (i % 4) * 10 for i in range(24)],
        'channel': ['Search'] * 24,
    })
    datasets['marketing_data'] = marketing_df
    
    return datasets

def generate_test_scenarios():
    scenarios = []
    
    price_scenarios = [-20, -10, -5, -1, 0, 1, 5, 10, 15, 25]
    for mag in price_scenarios:
        scenarios.append(("price_change", "price_per_unit", mag, "percentage"))
    
    headcount_scenarios = [-50, -20, -10, -5, -1, 0, 1, 5, 10, 25]
    for mag in headcount_scenarios:
        scenarios.append(("headcount", "headcount", mag, "absolute"))
    
    marketing_scenarios = [-20000, -10000, -5000, -1000, 0, 1000, 5000, 10000, 20000, 30000]
    for mag in marketing_scenarios:
        scenarios.append(("marketing", "budget", mag, "absolute"))
    
    return scenarios[:30]

def run_spotcheck():
    datasets = load_test_datasets()
    scenarios = generate_test_scenarios()
    log_file = PROJECT_ROOT / "week5_issues_log.json"

    if log_file.exists():
        log_file.unlink()

    logger = Week5IssueLogger(log_file=str(log_file))
    dataset_map = {
        "price_change": datasets.get("sales_data"),
        "headcount": datasets.get("hr_data"),
        "marketing": datasets.get("marketing_data"),
    }
    
    all_results = []
    
    print("\n" + "="*70)
    print("WEEK 5: SPOT CHECKING 30 SCENARIOS")
    print("="*70 + "\n")
    
    for dataset_name, df in datasets.items():
        print(f"\n📊 Dataset: {dataset_name}")
        print("-" * 50)

    for idx, (decision_type, parameter, magnitude, mag_type) in enumerate(scenarios):
        df = dataset_map[decision_type]
        dataset_name = decision_type

        try:
            prediction = run(df, decision_type, parameter, magnitude, mag_type)
            risk = score(decision_type, magnitude, prediction)
            
            result = {
                "dataset": dataset_name,
                "scenario_id": idx + 1,
                "decision_type": decision_type,
                "magnitude": magnitude,
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
                "risk_factors": risk["risk_factors"]
            }
            all_results.append(result)
            
            plausibility_issues = check_all_plausibility(decision_type, magnitude, risk)
            
            for issue_desc in plausibility_issues:
                issue_id = logger.log_issue(
                    scenario=f"{decision_type}: {magnitude}{'%' if mag_type == 'percentage' else ' units'}",
                    issue_type="plausibility",
                    description=issue_desc,
                    severity="high" if "High Risk" in issue_desc or "Low Risk" in issue_desc else "medium"
                )
                print(f"  ⚠️ Issue #{issue_id}: {issue_desc}")
            
            if (idx + 1) % 10 == 0:
                print(f"  ✓ Completed {idx + 1}/{len(scenarios)} scenarios")
                
        except Exception as e:
            issue_id = logger.log_issue(
                scenario=f"{decision_type}: {magnitude}",
                issue_type="runtime_error",
                description=str(e),
                severity="high"
            )
            print(f"  ❌ Error #{issue_id}: {e}")
    
    return all_results, logger

def analyze_results(results, logger):
    print("\n" + "="*70)
    print("SPOTCHECK ANALYSIS")
    print("="*70)
    
    low_risk_count = len([r for r in results if r["risk_score"] <= 33])
    medium_risk_count = len([r for r in results if 34 <= r["risk_score"] <= 66])
    high_risk_count = len([r for r in results if r["risk_score"] >= 67])
    
    print(f"\nRisk Distribution across {len(results)} scenarios:")
    print(f"  Low Risk (0-33):   {low_risk_count} ({low_risk_count/len(results)*100:.1f}%)")
    print(f"  Medium Risk (34-66): {medium_risk_count} ({medium_risk_count/len(results)*100:.1f}%)")
    print(f"  High Risk (67-100):  {high_risk_count} ({high_risk_count/len(results)*100:.1f}%)")
    
    by_decision_type = {}
    for r in results:
        dt = r["decision_type"]
        if dt not in by_decision_type:
            by_decision_type[dt] = {"total_score": 0, "count": 0}
        by_decision_type[dt]["total_score"] += r["risk_score"]
        by_decision_type[dt]["count"] += 1
    
    print("\nAverage Risk Score by Decision Type:")
    for dt, data in by_decision_type.items():
        avg = data["total_score"] / data["count"]
        print(f"  {dt}: {avg:.1f}")
    
    summary = logger.generate_summary()
    print(f"\nIssue Summary:")
    print(f"  Total Issues: {summary['total_issues']}")
    print(f"  Open Issues: {summary['open_issues']}")
    print(f"  Resolved: {summary['resolved_issues']}")
    
    return summary

def save_final_report(results, logger, summary):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "week": 5,
        "timestamp": datetime.now().isoformat(),
        "scenarios_tested": len(results),
        "datasets_used": 3,
        "risk_distribution": summary,
        "rubric_version_current": "v1",
        "rubric_version_next": "v2",
        "next_actions": [
            "Update risk_scorer.py RUBRIC_VERSION to 'v2'",
            "Adjust magnitude thresholds based on plausibility issues",
            "Add new risk factor for negative revenue impact",
            "Re-run validation suite with updated rubric",
            "Generate Week 6 Validation Report"
        ]
    }
    
    with open(f"week5_final_report_{timestamp}.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Final report saved: week5_final_report_{timestamp}.json")
    
    pm_report = logger.export_for_pm(f"week5_rubric_refinements_{timestamp}.md")
    print(f"✓ PM report saved: {pm_report}")
    
    return report

if __name__ == "__main__":
    results, logger = run_spotcheck()
    summary = analyze_results(results, logger)
    save_final_report(results, logger, summary)
    
    print("\n" + "="*70)
    print("✅ WEEK 5 COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("1. Review week5_rubric_refinements_*.md")
    print("2. Update dt_ml/risk_scorer.py with refinements")
    print("3. Increment RUBRIC_VERSION to 'v2'")
    print("4. Run: pytest tests/test_week5_rubric.py")
    print("5. Proceed to Week 6 Validation Report")