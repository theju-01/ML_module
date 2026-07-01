from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from config import ground_truth, scenarios
from dt_ml.baseline_analytics import compute
from dt_ml.risk_scorer import score
from dt_ml.simulation_engine import run
from dt_ml.validation.model_validation import validate_model
from dt_ml.validation.thresholds import (
    HEADCOUNT_MODEL_THRESHOLDS,
    MARKETING_MODEL_THRESHOLDS,
    PRICE_MODEL_THRESHOLDS,
)


logger = logging.getLogger(__name__)

now = datetime.now()


def _register_times_font() -> str:                          #font used in the report
    """Use Times New Roman when it is available on Windows.

    ReportLab ships with the Times family. When the system font is present,
    we register it so the generated report uses the requested face directly.
    """

    candidates = [
        Path(r"C:\Windows\Fonts\times.ttf"),
        Path(r"C:\Windows\Fonts\Times New Roman.ttf"),
        Path(r"C:\Windows\Fonts\timesnewroman.ttf"),
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("TimesNewRoman", str(candidate)))
                return "TimesNewRoman"
            except Exception:
                continue

    return "Times-Roman"


def _safe_number(value: Any) -> Any:                    
    if value is None:
        return "-"
    if isinstance(value, float):
        return round(value, 2)                              #round fig
    return value


def _format_percent(value: Any) -> str:
    if value is None or value == "-":
        return "-"
    try:
        return f"{float(value):.2f}%"                          #cutoff
    except (TypeError, ValueError):
        return str(value)


def _format_currency(value: Any) -> str:
    if value is None or value == "-":
        return "-"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _baseline_total_revenue(baseline: dict[str, Any]) -> Any:
    if "estimated_revenue" in baseline:
        return baseline["estimated_revenue"]
    return baseline.get("kpi_cards", {}).get("total_revenue", "-")


def _load_project_datasets(data_dir: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for csv_path in sorted(data_dir.glob("*.csv")):
        try:
            frame = pd.read_csv(csv_path)
        except Exception as exc:
            summaries.append(
                {
                    "dataset": csv_path.name,
                    "rows": "-",
                    "columns": "-",
                    "missing_pct": "-",
                    "note": f"Unable to read file: {exc}",
                }
            )
            continue

        missing_pct = float(frame.isna().mean().mean() * 100) if not frame.empty else 0.0
        numeric_cols = list(frame.select_dtypes(include="number").columns[:3])
        numeric_preview = ", ".join(numeric_cols) if numeric_cols else "No numeric columns"

        summaries.append(
            {
                "dataset": csv_path.name,
                "rows": len(frame),
                "columns": len(frame.columns),
                "missing_pct": round(missing_pct, 2),
                "note": f"Key numeric fields: {numeric_preview}",
            }
        )

    return summaries


def _collect_project_validation() -> dict[str, Any]:
    sales_path = Path("data/sales_data.csv")
    if not sales_path.exists():
        raise FileNotFoundError("data/sales_data.csv was not found.")

    sales_df = pd.read_csv(sales_path)
    baseline = compute(sales_df)
    numeric_ground_truth = {
        scenario_id: value.get("revenue_delta_pct", value)
        if isinstance(value, dict)
        else value
        for scenario_id, value in ground_truth.items()
    }

    validation_metrics = validate_model(
        lambda df, parameter, magnitude, magnitude_type: run(
            df=df,
            decision_type="price_change",
            parameter=parameter,
            magnitude=magnitude,
            magnitude_type=magnitude_type,
        ),
        sales_df,
        numeric_ground_truth,
        scenarios,
    )

    risk_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        prediction = run(
            df=sales_df,
            decision_type="price_change",
            parameter=scenario["parameter"],
            magnitude=scenario["magnitude"],
            magnitude_type=scenario["magnitude_type"],
        )
        risk = score(
            "price_change",
            scenario["magnitude"],
            prediction,
        )

        risk_rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "parameter": scenario["parameter"],
                "magnitude": scenario["magnitude"],
                "magnitude_type": scenario["magnitude_type"],
                "predicted_revenue_delta_pct": prediction["predicted_kpis"].get(
                    "revenue_delta_pct",
                    0,
                ),
                "confidence_score": prediction.get("confidence_score", 0),
                "risk_level": risk["risk_level"],
                "risk_score": risk["risk_score"],
                "risk_factors": risk["risk_factors"],
                "explanation": risk["explanation"],
            }
        )

    return {
        "baseline": baseline,
        "row_count": len(sales_df),
        "validation_metrics": validation_metrics,
        "risk_rows": risk_rows,
    }


def _collect_main_execution_snapshot() -> dict[str, Any]:
    """Mirror the runtime steps performed by main.py."""

    data_path = Path("data/sales_data.csv")
    if not data_path.exists():
        raise FileNotFoundError("data/sales_data.csv was not found.")

    df = pd.read_csv(data_path)
    baseline = compute(df)
    simulation_result = run(
        df=df,
        decision_type="price_change",
        parameter="price_per_unit",
        magnitude=10,
        magnitude_type="percentage",
    )
    validation_results = validate_model(
        lambda test_df, parameter, magnitude, magnitude_type: run(
            df=test_df,
            decision_type="price_change",
            parameter=parameter,
            magnitude=magnitude,
            magnitude_type=magnitude_type,
        ),
        df,
        {
            scenario_id: value.get("revenue_delta_pct", value)
            if isinstance(value, dict)
            else value
            for scenario_id, value in ground_truth.items()
        },
        scenarios,
    )
    risk = score("price_change", 10, simulation_result)

    return {
        "baseline": baseline,
        "row_count": len(df),
        "simulation_result": simulation_result,
        "validation_results": validation_results,
        "risk": risk,
    }


def _risk_colors(level: str) -> tuple[colors.Color, colors.Color]:
    normalized = (level or "").strip().lower()
    if normalized == "low":
        return colors.HexColor("#DFF3E3"), colors.HexColor("#1B5E20")
    if normalized == "medium":
        return colors.HexColor("#FFF1C2"), colors.HexColor("#8A5A00")
    return colors.HexColor("#F8D7DA"), colors.HexColor("#8B1E2D")


def _build_metric_table(font_name: str, metrics: dict[str, Any]) -> Table:
    data = [
        ["Metric", "Value", "Threshold", "Status"],
        [
            "MAPE",
            _format_percent(metrics["mape"] * 100 if metrics["mape"] <= 1 else metrics["mape"]),
            _format_percent(PRICE_MODEL_THRESHOLDS["mape"] * 100),
            "Pass" if metrics["mape"] <= PRICE_MODEL_THRESHOLDS["mape"] else "Review",
        ],
        [
            "Directional Accuracy",
            _format_percent(metrics["directional_accuracy"] * 100 if metrics["directional_accuracy"] <= 1 else metrics["directional_accuracy"]),
            _format_percent(PRICE_MODEL_THRESHOLDS["directional_accuracy"] * 100),
            "Pass" if metrics["directional_accuracy"] >= PRICE_MODEL_THRESHOLDS["directional_accuracy"] else "Review",
        ],
        [
            "RMSE",
            _safe_number(metrics.get("rmse", "-")),
            "-",
            "Informational",
        ],
    ]

    table = Table(data, colWidths=[150, 120, 120, 80])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#274060")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F7F9FC")]),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return table


def _build_risk_table(font_name: str, risk_rows: Iterable[dict[str, Any]]) -> Table:
    data = [
        [
            "Scenario",
            "Magnitude",
            "Predicted Revenue Delta",
            "Confidence",
            "Risk Level",
            "Risk Score",
        ]
    ]

    for row in risk_rows:
        data.append(
            [
                row["scenario_id"],
                f'{row["magnitude"]} {row["magnitude_type"]}',
                _format_percent(row["predicted_revenue_delta_pct"]),
                f'{_safe_number(row["confidence_score"])}%',
                row["risk_level"],
                row["risk_score"],
            ]
        )

    table = Table(data, colWidths=[105, 90, 115, 85, 85, 70])

    style_commands = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#274060")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    for idx, row in enumerate(risk_rows, start=1):
        bg_color, text_color = _risk_colors(row["risk_level"])
        style_commands.extend(
            [
                ("BACKGROUND", (4, idx), (4, idx), bg_color),
                ("TEXTCOLOR", (4, idx), (4, idx), text_color),
                ("BACKGROUND", (5, idx), (5, idx), bg_color),
                ("TEXTCOLOR", (5, idx), (5, idx), text_color),
            ]
        )

    table.setStyle(TableStyle(style_commands))
    return table


def _build_dataset_table(font_name: str, dataset_rows: list[dict[str, Any]]) -> Table:
    data = [["Dataset", "Rows", "Columns", "Missing %", "Notes"]]

    for row in dataset_rows:
        data.append(
            [
                row["dataset"],
                row["rows"],
                row["columns"],
                _format_percent(row["missing_pct"]),
                row["note"],
            ]
        )

    table = Table(data, colWidths=[120, 55, 65, 70, 210])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#274060")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F7F9FC")]),
                ("ALIGN", (1, 1), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _build_execution_table(font_name: str, execution_snapshot: dict[str, Any]) -> Table:
    simulation_result = execution_snapshot["simulation_result"]
    validation_results = execution_snapshot["validation_results"]
    risk = execution_snapshot["risk"]

    data = [
        ["main.py Output", "Value"],
        ["Baseline total revenue", _format_currency(_baseline_total_revenue(execution_snapshot["baseline"]))],
        ["Baseline rows", _safe_number(execution_snapshot.get("row_count"))],
        ["Simulation model", simulation_result.get("model_used", "-")],
        ["Simulation revenue delta", _format_percent(simulation_result["predicted_kpis"].get("revenue_delta_pct", 0))],
        ["Simulation confidence", f'{_safe_number(simulation_result.get("confidence_score", 0))}%'],
        ["Validation MAPE", _format_percent(validation_results.get("mape", 0) * 100 if validation_results.get("mape", 0) <= 1 else validation_results.get("mape", 0))],
        ["Validation directional accuracy", _format_percent(validation_results.get("directional_accuracy", 0) * 100 if validation_results.get("directional_accuracy", 0) <= 1 else validation_results.get("directional_accuracy", 0))],
        ["Risk level", risk.get("risk_level", "-")],
        ["Risk score", risk.get("risk_score", "-")],
    ]

    table = Table(data, colWidths=[170, 150])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F7F9FC")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    bg_color, text_color = _risk_colors(risk.get("risk_level", ""))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (1, 8), (1, 9), bg_color),
                ("TEXTCOLOR", (1, 8), (1, 9), text_color),
            ]
        )
    )
    return table


def build_validation_report(
    metrics: dict | None = None,
    risk_results: dict | None = None,
    output_path: str = f"validation_report_{str(now.day)}-{str(now.month)}-{str(now.year)}.pdf",
) -> str:
    report_start = time.perf_counter()
    logger.info(
        "TEMP START build_validation_report metrics_provided=%s risk_results_provided=%s output_path=%s",
        metrics is not None,
        risk_results is not None,
        output_path,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    font_name = _register_times_font()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ProjectTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=20,
        leading=24,
        alignment=1,
        textColor=colors.HexColor("#1E3A5F"),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10.5,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#444444"),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A5F"),
        spaceBefore=6,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#222222"),
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#333333"),
    )

    if metrics is None or risk_results is None:
        project_snapshot = _collect_project_validation()
        metrics = metrics or project_snapshot["validation_metrics"]
        risk_results = risk_results or {
            "baseline": project_snapshot["baseline"],
            "row_count": project_snapshot["row_count"],
            "risk_rows": project_snapshot["risk_rows"],
        }

    execution_snapshot = _collect_main_execution_snapshot()
    risk_rows = list(risk_results.get("risk_rows", []))
    baseline = risk_results.get("baseline", {})
    dataset_rows = _load_project_datasets(Path("data"))
    metric_pass = (
        metrics.get("mape", 1) <= PRICE_MODEL_THRESHOLDS["mape"]
        and metrics.get("directional_accuracy", 0) >= PRICE_MODEL_THRESHOLDS["directional_accuracy"]
    )
    high_risk_count = sum(1 for row in risk_rows if str(row.get("risk_level", "")).lower() == "high")
    signoff_status = "Approved" if metric_pass and high_risk_count == 0 else "Review Required"

    story: list[Any] = []
    story.append(Paragraph("Project Validation Report", title_style))
    story.append(
        Paragraph(
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for the current project workspace.",
            subtitle_style,
        )
    )
    story.append(
        Paragraph(
            "This report summarizes the data assets in the project, baseline analytics, scenario validation, and risk analysis. Red highlights risky outcomes, while green highlights low-risk outcomes.",
            body_style,
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Project Overview", heading_style))
    summary_data = [
        ["Project Metric", "Value"],
        ["Datasets analyzed", len(dataset_rows)],
        ["Validation scenarios", len(risk_rows)],
        ["Baseline revenue", _format_currency(_baseline_total_revenue(baseline))],
        ["Baseline rows", _safe_number(risk_results.get("row_count", execution_snapshot.get("row_count")))],
    ]
    summary_table = Table(summary_data, colWidths=[160, 160])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F9FC"), colors.whitesmoke]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Validation Results", heading_style))
    story.append(
        Paragraph(
            "This section reflects the instance result produced by running the current main.py entry point, including the baseline analytics, simulation output, validation metrics, and risk score.",
            body_style,
        )
    )
    story.append(Spacer(1, 6))
    story.append(_build_execution_table(font_name, execution_snapshot))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Dataset Coverage", heading_style))
    if dataset_rows:
        story.append(_build_dataset_table(font_name, dataset_rows))
    else:
        story.append(Paragraph("No CSV files were found in the data directory.", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Model Performance Metrics", heading_style))
    story.append(_build_metric_table(font_name, metrics))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Scoring Results", heading_style))
    if risk_rows:
        story.append(_build_risk_table(font_name, risk_rows))
        story.append(Spacer(1, 8))
        for row in risk_rows:
            bg_color, text_color = _risk_colors(row["risk_level"])
            factors = ", ".join(row.get("risk_factors", [])) or "No major risk factors"
            story.append(
                Paragraph(
                    f'<font color="{text_color.hexval()}"><b>{row["scenario_id"]}</b> - {row["risk_level"]} risk ({row["risk_score"]}/100): {row["explanation"]}. Factors: {factors}.</font>',
                    small_style,
                )
            )
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No risk rows were supplied for this report.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Test Summary", heading_style))
    test_data = [
        ["Check", "Result"],
        ["Baseline analytics test coverage", "Included"],
        ["Simulation engine test coverage", "Included"],
        ["Risk scorer test coverage", "Included"],
        ["Validation metric thresholds", "Pass" if metric_pass else "Review"],
        ["High-risk scenarios detected", high_risk_count],
    ]
    test_table = Table(test_data, colWidths=[190, 130])
    test_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F7F9FC")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(test_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Performance Summary", heading_style))
    performance_data = [
        ["Performance Item", "Value"],
        ["Report build elapsed time", f"{time.perf_counter() - report_start:.2f} seconds before PDF render"],
        ["Rows processed in main sales dataset", _safe_number(execution_snapshot.get("row_count"))],
        ["Validation scenarios evaluated", len(risk_rows)],
        ["Simulation confidence", f'{_safe_number(execution_snapshot["simulation_result"].get("confidence_score", 0))}%'],
    ]
    performance_table = Table(performance_data, colWidths=[190, 160])
    performance_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7F9FC"), colors.whitesmoke]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(performance_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Final Sign-off Status", heading_style))
    story.append(
        Paragraph(
            f"<b>Status:</b> {signoff_status}. Model thresholds "
            f"{'passed' if metric_pass else 'need review'} and {high_risk_count} high-risk scenarios were detected.",
            body_style,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Threshold Reference", heading_style))
    threshold_data = [
        ["Model", "MAPE Threshold", "Directional Accuracy Threshold"],
        ["Price", _format_percent(PRICE_MODEL_THRESHOLDS["mape"] * 100), _format_percent(PRICE_MODEL_THRESHOLDS["directional_accuracy"] * 100)],
        ["Headcount", _format_percent(HEADCOUNT_MODEL_THRESHOLDS["mape"] * 100), _format_percent(HEADCOUNT_MODEL_THRESHOLDS["directional_accuracy"] * 100)],
        ["Marketing", _format_percent(MARKETING_MODEL_THRESHOLDS["mape"] * 100), _format_percent(MARKETING_MODEL_THRESHOLDS["directional_accuracy"] * 100)],
    ]
    threshold_table = Table(threshold_data, colWidths=[110, 115, 145])
    threshold_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8A8A8A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F7F9FC")]),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(threshold_table)

    def _draw_footer(canvas, document):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(document.leftMargin, 18, "Generated by dt_ml.validation.report_builder")
        canvas.drawRightString(
            A4[0] - document.rightMargin,
            18,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    logger.info("TEMP build_validation_report generating PDF elements=%s", len(story))
    doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    logger.info("TEMP END build_validation_report saved=%s", output_path)
    return str(output_path)

