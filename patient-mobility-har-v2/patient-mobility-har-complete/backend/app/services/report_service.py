
    """
    Report generation: daily, weekly, and monthly mobility reports
    for a patient in PDF, CSV, or XLSX format.

    Includes an illustrative activity-based recovery indicator.
    This is NOT a medically validated recovery rate.

    Reports exclude fall events, inactivity events, and alert history.
    Report dates and timestamps use the system's local time.
    """

    import csv
    from datetime import datetime, timedelta
    from pathlib import Path
    from typing import Optional
    from io import BytesIO

    from openpyxl import Workbook
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image,
        KeepTogether,
    )
    from reportlab.lib.styles import getSampleStyleSheet
    from sqlalchemy.orm import Session

    from app.models.patient import Patient
    from app.models.report import Report, ReportType, ReportFormat
    from app.services.activity_service import get_history
    from app.services.analytics_service import (
        activity_distribution,
        daily_activity_duration,
    )
    from app.services.monitoring_session_service import total_monitoring_seconds
    from app.services.report_charts import (
        render_activity_distribution_pie,
        render_weekly_trend_chart,
        render_activity_timeline,
        add_xlsx_summary_and_charts,
    )
    from app.utils.file_storage import new_report_path, to_relative_url
    from app.utils.logger import get_logger

    logger = get_logger(__name__)

    _PERIOD_DAYS = {
        ReportType.daily: 1,
        ReportType.weekly: 7,
        ReportType.monthly: 30,
    }


    def _system_now() -> datetime:
        """Return current system-local date and time as a naive datetime."""
        return datetime.now().astimezone().replace(tzinfo=None)


    def _period_window(
        report_type: ReportType,
    ) -> tuple[datetime, datetime]:
        """Calculate the reporting period using system-local time."""
        date_to = _system_now()
        date_from = date_to - timedelta(
            days=_PERIOD_DAYS[report_type]
        )
        return date_from, date_to


    def calculate_recovery_indicator(distribution: dict) -> dict:
        """
        Calculate an illustrative activity-based mobility score.

        Expected input:
            Activity labels mapped to durations in seconds.

        Illustrative weights:
            Walking     = 100
            Standing    = 70
            Sitting     = 30
            Lying down  = 0

        Only the score and interpretation are returned.
        Activity durations remain in the existing activity section.

        This is not a medically validated recovery rate.
        """

        durations = {
            "walking": 0.0,
            "standing": 0.0,
            "sitting": 0.0,
            "lying": 0.0,
        }

        for label, seconds in distribution.items():
            name = str(label).strip().lower().replace("_", " ")

            try:
                duration = max(0.0, float(seconds or 0))
            except (TypeError, ValueError):
                continue

            if "walk" in name:
                durations["walking"] += duration
            elif "stand" in name:
                durations["standing"] += duration
            elif "sit" in name:
                durations["sitting"] += duration
            elif any(
                word in name
                for word in ("lying", "lie", "lay", "sleep")
            ):
                durations["lying"] += duration

        total_seconds = sum(durations.values())

        if total_seconds <= 0:
            return {
                "score": None,
                "interpretation": "Insufficient activity data",
            }

        score = (
            durations["walking"] * 100
            + durations["standing"] * 70
            + durations["sitting"] * 30
            + durations["lying"] * 0
        ) / total_seconds

        score = round(max(0.0, min(100.0, score)), 1)

        if score >= 70:
            interpretation = "Higher activity-based mobility score"
        elif score >= 40:
            interpretation = "Moderate activity-based mobility score"
        else:
            interpretation = "Lower activity-based mobility score"

        return {
            "score": score,
            "interpretation": interpretation,
        }


    def _report_context(
        patient: Patient,
        report_type: ReportType,
        date_from: datetime,
        date_to: datetime,
        db: Session,
    ) -> dict:
        """Collect activity and monitoring data for reports."""

        activities = get_history(
            db,
            patient.id,
            date_from,
            date_to,
            limit=10000,
        )

        distribution = activity_distribution(
            db,
            patient.id,
            date_from,
            date_to,
        )

        recovery = calculate_recovery_indicator(distribution)

        trend_days = min(_PERIOD_DAYS[report_type], 30)

        daily_points = daily_activity_duration(
            db,
            patient.id,
            days=trend_days,
        )

        monitoring_seconds = total_monitoring_seconds(
            db,
            patient.id,
            date_from,
            date_to,
        )

        return {
            "activities": activities,
            "distribution": distribution,
            "daily_points": daily_points,
            "monitoring_seconds": monitoring_seconds,
            "recovery": recovery,
        }


    def _write_recovery_csv(writer, recovery: dict) -> None:
        """Write one recovery score without duplicate activity durations."""

        writer.writerow([])
        writer.writerow([
            "Recovery Rate (%)",
            (
                recovery["score"]
                if recovery["score"] is not None
                else "Insufficient activity data"
            ),
        ])
        writer.writerow([
            "Interpretation",
            recovery["interpretation"],
        ])
        writer.writerow([
            "Note",
            "Illustrative activity-based mobility score; "
            "not a medically validated recovery rate.",
        ])


    def _generate_csv(
        patient: Patient,
        report_type: ReportType,
        date_from: datetime,
        date_to: datetime,
        db: Session,
    ) -> str:
        """Generate CSV without fall, inactivity, or alert information."""

        destination = new_report_path(
            patient.id,
            report_type.value,
            "csv",
        )

        ctx = _report_context(
            patient,
            report_type,
            date_from,
            date_to,
            db,
        )

        with open(
            destination,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                f"Patient Mobility Report - {report_type.value.title()}"
            ])
            writer.writerow(["Patient", patient.name])
            writer.writerow(["Room", patient.room_number or "N/A"])
            writer.writerow([
                "Report generated on",
                datetime.now().astimezone().strftime(
                    "%d-%m-%Y %I:%M:%S %p %Z"
                ),
            ])
            writer.writerow([
                "Monitoring period",
                f"{date_from.strftime('%d-%m-%Y %H:%M')} to "
                f"{date_to.strftime('%d-%m-%Y %H:%M')}",
            ])
            writer.writerow([
                "Total monitoring time (min)",
                round(ctx["monitoring_seconds"] / 60, 1),
            ])

            # Existing activity-duration rows are retained.
            writer.writerow([])
            writer.writerow(["Activity Distribution"])
            writer.writerow(["Activity Type", "Total Minutes"])

            for activity_type, seconds in ctx["distribution"].items():
                try:
                    minutes = round(float(seconds or 0) / 60, 1)
                except (TypeError, ValueError):
                    minutes = 0.0

                writer.writerow([
                    str(activity_type).title(),
                    minutes,
                ])

            # Add only one recovery score.
            _write_recovery_csv(writer, ctx["recovery"])

            writer.writerow([])
            writer.writerow(["Activity Timeline"])
            writer.writerow([
                "Activity",
                "Confidence",
                "Started At",
                "Ended At",
                "Duration (sec)",
            ])

            for activity in ctx["activities"]:
                writer.writerow([
                    activity.activity_type.value,
                    f"{activity.confidence:.2f}",
                    activity.started_at.isoformat(),
                    (
                        activity.ended_at.isoformat()
                        if activity.ended_at
                        else ""
                    ),
                    activity.duration_sec or "",
                ])

        return str(destination)


    def _generate_xlsx(
        patient: Patient,
        report_type: ReportType,
        date_from: datetime,
        date_to: datetime,
        db: Session,
    ) -> str:
        """Generate Excel without fall statistics or alert history."""

        destination = new_report_path(
            patient.id,
            report_type.value,
            "xlsx",
        )

        ctx = _report_context(
            patient,
            report_type,
            date_from,
            date_to,
            db,
        )

        workbook = Workbook()

        # Activity timeline worksheet.
        timeline_sheet = workbook.active
        timeline_sheet.title = "Activity Timeline"

        timeline_sheet.append([
            "Activity",
            "Confidence",
            "Started At",
            "Ended At",
            "Duration (sec)",
        ])

        for activity in ctx["activities"]:
            timeline_sheet.append([
                activity.activity_type.value,
                round(activity.confidence, 2),
                activity.started_at.isoformat(),
                (
                    activity.ended_at.isoformat()
                    if activity.ended_at
                    else ""
                ),
                activity.duration_sec or "",
            ])

        # Preserve existing activity charts and summary.
        add_xlsx_summary_and_charts(
            workbook,
            ctx["distribution"],
            ctx["daily_points"],
        )

        summary_sheet = (
            workbook["Summary"]
            if "Summary" in workbook.sheetnames
            else workbook.worksheets[0]
        )

        next_row = summary_sheet.max_row + 3

        summary_rows = [
            ("Patient", patient.name),
            ("Room", patient.room_number or "N/A"),
            (
                "Report generated on",
                datetime.now().astimezone().strftime(
                    "%d-%m-%Y %I:%M:%S %p %Z"
                ),
            ),
            (
                "Monitoring period",
                f"{date_from.strftime('%d-%m-%Y %H:%M')} to "
                f"{date_to.strftime('%d-%m-%Y %H:%M')}",
            ),
            (
                "Total monitoring time (min)",
                round(ctx["monitoring_seconds"] / 60, 1),
            ),
        ]

        for offset, (label, value) in enumerate(summary_rows):
            summary_sheet.cell(
                row=next_row + offset,
                column=1,
                value=label,
            )
            summary_sheet.cell(
                row=next_row + offset,
                column=2,
                value=value,
            )

        # Add one recovery rate; don't repeat the activity durations.
        recovery = ctx["recovery"]
        recovery_row = next_row + len(summary_rows) + 2

        summary_sheet.cell(
            row=recovery_row,
            column=1,
            value="Recovery Rate (%)",
        )
        summary_sheet.cell(
            row=recovery_row,
            column=2,
            value=(
                recovery["score"]
                if recovery["score"] is not None
                else "Insufficient activity data"
            ),
        )

        summary_sheet.cell(
            row=recovery_row + 1,
            column=1,
            value="Interpretation",
        )
        summary_sheet.cell(
            row=recovery_row + 1,
            column=2,
            value=recovery["interpretation"],
        )

        summary_sheet.cell(
            row=recovery_row + 2,
            column=1,
            value="Note",
        )
        summary_sheet.cell(
            row=recovery_row + 2,
            column=2,
            value=(
                "Illustrative activity-based mobility score; "
                "not a medically validated recovery rate."
            ),
        )

        workbook.save(str(destination))
        return str(destination)


    def _generate_pdf(
        patient: Patient,
        report_type: ReportType,
        date_from: datetime,
        date_to: datetime,
        db: Session,
    ) -> str:
        """Generate PDF without fall, inactivity, or alert information."""

        destination = new_report_path(
            patient.id,
            report_type.value,
            "pdf",
        )

        styles = getSampleStyleSheet()

        doc = SimpleDocTemplate(
            str(destination),
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements = []

        elements.append(
            Paragraph(
                f"Patient Mobility Report - {report_type.value.title()}",
                styles["Title"],
            )
        )

        patient_line = (
            f"Patient: {patient.name} | "
            f"Room: {patient.room_number or 'N/A'}"
        )

        if patient.age:
            patient_line += f" | Age: {patient.age}"

        if patient.disease:
            patient_line += f" | Condition: {patient.disease}"

        elements.append(
            Paragraph(patient_line, styles["Normal"])
        )

        elements.append(
            Paragraph(
                "Report generated on: "
                f"{datetime.now().astimezone().strftime('%d-%m-%Y %I:%M:%S %p %Z')}",
                styles["Normal"],
            )
        )

        elements.append(
            Paragraph(
                "Monitoring period: "
                f"{date_from.strftime('%d-%m-%Y %H:%M')} to "
                f"{date_to.strftime('%d-%m-%Y %H:%M')}",
                styles["Normal"],
            )
        )

        elements.append(Spacer(1, 14))

        ctx = _report_context(
            patient,
            report_type,
            date_from,
            date_to,
            db,
        )

        distribution = ctx["distribution"]
        daily_points = ctx["daily_points"]
        activities = ctx["activities"]
        recovery = ctx["recovery"]

        # Keep the existing activity durations, with no duplicate rows.
        summary_data = [["Metric", "Value"]]

        summary_data.append([
            "Total monitoring time",
            f"{ctx['monitoring_seconds'] / 60:.1f} min",
        ])

        for activity_type, seconds in distribution.items():
            try:
                minutes = float(seconds or 0) / 60
            except (TypeError, ValueError):
                minutes = 0.0

            summary_data.append([
                f"{str(activity_type).title()} duration",
                f"{minutes:.1f} min",
            ])

        # Single recovery score.
        summary_data.append([
            "Recovery Rate (%)",
            (
                f"{recovery['score']:.1f}%"
                if recovery["score"] is not None
                else "Insufficient activity data"
            ),
        ])

        summary_data.append([
            "Interpretation",
            recovery["interpretation"],
        ])

        table = Table(
            summary_data,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1e40af"),
                ),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 8))


        elements.append(Spacer(1, 18))

        # Activity distribution chart.
        pie_png = render_activity_distribution_pie(distribution)

        elements.append(
            KeepTogether([
                Paragraph(
                    "Activity Distribution",
                    styles["Heading2"],
                ),
                Image(
                    BytesIO(pie_png),
                    width=9 * cm,
                    height=6.8 * cm,
                ),
            ])
        )

        elements.append(Spacer(1, 12))

        # Activity trend chart for weekly and monthly reports.
        if report_type != ReportType.daily and daily_points:
            trend_png = render_weekly_trend_chart(daily_points)

            elements.append(
                KeepTogether([
                    Paragraph(
                        "Activity Trend",
                        styles["Heading2"],
                    ),
                    Image(
                        BytesIO(trend_png),
                        width=15 * cm,
                        height=6.8 * cm,
                    ),
                ])
            )

            elements.append(Spacer(1, 12))

        # Activity timeline.
        timeline_png = render_activity_timeline(
            activities,
            timeline_date=date_to,
        )

        elements.append(
            KeepTogether([
                Paragraph(
                    f"Activity Timeline - {date_to.strftime('%d-%m-%Y')}",
                    styles["Heading2"],
                ),
                Image(
                    BytesIO(timeline_png),
                    width=15 * cm,
                    height=4.3 * cm,
                ),
            ])
        )

        # No alert history or fall/inactivity statistics.
        doc.build(elements)

        return str(destination)


    def generate_report(
        db: Session,
        patient: Patient,
        report_type: ReportType,
        report_format: ReportFormat,
    ) -> Report:
        """Generate and save a daily, weekly, or monthly report."""

        date_from, date_to = _period_window(report_type)

        if report_format == ReportFormat.csv:
            file_path = _generate_csv(
                patient,
                report_type,
                date_from,
                date_to,
                db,
            )
        elif report_format == ReportFormat.xlsx:
            file_path = _generate_xlsx(
                patient,
                report_type,
                date_from,
                date_to,
                db,
            )
        else:
            file_path = _generate_pdf(
                patient,
                report_type,
                date_from,
                date_to,
                db,
            )

        report = Report(
            patient_id=patient.id,
            report_type=report_type,
            report_format=report_format,
            file_path=to_relative_url(Path(file_path)),
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(
            "Generated %s %s report for patient_id=%s",
            report_type.value,
            report_format.value,
            patient.id,
        )

        return report


    def list_reports(
        db: Session,
        patient_id: Optional[int] = None,
    ):
        """List reports, optionally filtered by patient."""

        query = db.query(Report)

        if patient_id:
            query = query.filter(
                Report.patient_id == patient_id
            )

        return query.order_by(
            Report.generated_at.desc()
        ).all()


    def get_report(
        db: Session,
        report_id: int,
    ) -> Optional[Report]:
        """Retrieve a report by ID."""

        return (
            db.query(Report)
            .filter(Report.id == report_id)
            .first()
        )


    def build_download_filename(
        report: Report,
        patient_name: str,
    ) -> str:
        """Build a human-readable filename for a downloaded report."""

        safe_name = "".join(
            c if c.isalnum() or c in " -_" else "_"
            for c in patient_name
        ).strip().replace(" ", "_")

        date_str = report.generated_at.strftime("%Y-%m-%d")
        extension = Path(report.file_path).suffix.lstrip(".")

        return (
            f"{safe_name}_{report.report_type.value}_report_"
            f"{date_str}.{extension}"
        )
                                                                                                    