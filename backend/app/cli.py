from datetime import date

import click
from flask import Flask

from app.extensions import db
from app.models import ResearchPaper


def register_commands(app: Flask) -> None:
    @app.cli.command("seed-papers")
    def seed_papers() -> None:
        """Insert realistic mock papers if the table is empty."""
        if ResearchPaper.query.count() > 0:
            click.echo("Research papers already seeded.")
            return

        samples = [
            {
                "title": "Campus-Wide Air Quality Networks Reveal Hidden Hourly Pollution Spikes",
                "topic": "Environmental Engineering",
                "venue": "Environmental Science & Technology",
                "published_at": "2026-02-11",
                "abstract": (
                    "A low-cost sensor network across ten universities captures short pollution spikes "
                    "that city monitors miss. Pairing calibration transfer with weather features improves "
                    "hourly PM2.5 estimation and helps facilities teams time ventilation changes during "
                    "high-risk windows near roads and loading zones."
                ),
            },
            {
                "title": "Retrieval-Augmented Tutors Improve Intro CS Learning Without Increasing Study Time",
                "topic": "Learning Sciences",
                "venue": "LAK",
                "published_at": "2026-01-24",
                "abstract": (
                    "In a randomized classroom deployment, students using a retrieval-augmented tutor "
                    "showed higher debugging accuracy and stronger transfer on unseen problems, while "
                    "spending similar total time in the platform. Gains were largest for students in "
                    "the middle performance band."
                ),
            },
            {
                "title": "Fast Protein Function Search from Embedding Indexes at Million-Sequence Scale",
                "topic": "Computational Biology",
                "venue": "Nature Biotechnology",
                "published_at": "2025-12-18",
                "abstract": (
                    "Approximate nearest-neighbor indexing over protein language embeddings enables "
                    "function retrieval in milliseconds for large metagenomic catalogs. The pipeline "
                    "recovers distant homologs missed by alignment-only baselines and supports "
                    "interactive hypothesis generation for enzyme screening."
                ),
            },
            {
                "title": "Local LLM Inference on Student Laptops with Distillation and Quantization",
                "topic": "Machine Learning",
                "venue": "NeurIPS Datasets and Benchmarks",
                "published_at": "2025-11-09",
                "abstract": (
                    "A compact distilled model with mixed-precision quantization reaches practical "
                    "latency on commodity laptops while preserving instruction-following quality for "
                    "academic tasks. The study reports energy usage, thermal behavior, and a reproducible "
                    "setup for classroom-scale deployments without cloud dependence."
                ),
            },
            {
                "title": "Sleep Regularity Predicts Midterm Performance Better Than Total Sleep Duration",
                "topic": "Cognitive Neuroscience",
                "venue": "Current Biology",
                "published_at": "2025-10-03",
                "abstract": (
                    "Across a semester-long wearable study, consistency in bedtime and wake time "
                    "outperformed total nightly sleep as a predictor of exam outcomes. Effects remained "
                    "after controlling for prior GPA and course load, suggesting schedule stability is "
                    "a high-value intervention target for student success programs."
                ),
            },
            {
                "title": "Reliable Drone Delivery Routing Under Rapid Weather Shifts",
                "topic": "Robotics",
                "venue": "IEEE RA-L",
                "published_at": "2025-08-27",
                "abstract": (
                    "A robust planner that blends short-horizon forecasts with route-level risk budgets "
                    "reduces cancellations in high-variance wind conditions. Field trials show improved "
                    "on-time delivery and fewer emergency returns compared with deterministic planning."
                ),
            },
            {
                "title": "Secure Federated Analytics for Multi-Hospital Sepsis Prediction",
                "topic": "Health Informatics",
                "venue": "JAMIA",
                "published_at": "2025-07-14",
                "abstract": (
                    "Federated training with differential privacy enables cross-site model improvement "
                    "without centralizing sensitive records. The method maintains calibration across "
                    "hospitals and preserves early-warning performance under strict privacy budgets."
                ),
            },
            {
                "title": "Auditable Hiring Dashboards Reduce Automation Bias in Screening Decisions",
                "topic": "HCI & Social Computing",
                "venue": "CSCW",
                "published_at": "2025-05-29",
                "abstract": (
                    "Adding confidence bands, decision logs, and reviewer disagreement prompts to hiring "
                    "dashboards decreases blind acceptance of model scores. Teams using the dashboard "
                    "made fewer high-confidence errors and documented clearer justifications."
                ),
            },
            {
                "title": "Patch-Robust Vision Transformers for Low-Visibility Autonomous Driving",
                "topic": "Machine Learning",
                "venue": "CVPR",
                "published_at": "2025-04-15",
                "abstract": (
                    "Structured corruption training and uncertainty-aware ensembling improve detection "
                    "stability when camera frames contain glare, rain artifacts, or missing regions. "
                    "The approach raises recall in safety-critical classes without major throughput loss."
                ),
            },
            {
                "title": "Submesoscale Ocean Modeling Sharpens Regional Flood Forecasts",
                "topic": "Climate Science",
                "venue": "Science Advances",
                "published_at": "2025-02-20",
                "abstract": (
                    "Integrating submesoscale ocean dynamics into coastal forecast systems increases "
                    "lead-time accuracy for heavy-rain events near major estuaries. The combined model "
                    "captures heat and moisture gradients that drive sudden storm intensification."
                ),
            },
            {
                "title": "Bosonic Error-Correcting Gates with Fewer Hardware Components",
                "topic": "Quantum Computing",
                "venue": "Physical Review X",
                "published_at": "2024-12-06",
                "abstract": (
                    "A simplified coupling strategy for bosonic codes lowers control complexity while "
                    "maintaining repeated error detection performance. Prototype experiments demonstrate "
                    "longer logical coherence than comparable single-qubit baselines."
                ),
            },
            {
                "title": "Measuring and Cutting the Carbon Cost of Intro Programming Courses",
                "topic": "Education Technology",
                "venue": "SIGCSE",
                "published_at": "2024-10-25",
                "abstract": (
                    "Instrumentation of CI pipelines, autograders, and cloud IDE sessions identifies "
                    "avoidable compute waste in large programming courses. Scheduling and cache-policy "
                    "changes reduce operational emissions substantially without affecting turnaround time."
                ),
            },
        ]

        for row in samples:
            raw_date = row.get("published_at")
            pub = date.fromisoformat(raw_date) if raw_date else None
            db.session.add(
                ResearchPaper(
                    title=row["title"],
                    abstract=row["abstract"],
                    topic=row["topic"],
                    venue=row.get("venue"),
                    published_at=pub,
                )
            )
        db.session.commit()
        click.echo(f"Seeded {len(samples)} research papers.")
