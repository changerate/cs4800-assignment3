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
                "title": "Protein Language Models Capture Evolutionary Constraints Without Explicit Structure",
                "topic": "Computational Biology",
                "venue": "Nature Methods",
                "published_at": "2025-03-12",
                "abstract": (
                    "Self-supervised learning on millions of amino-acid sequences recovers "
                    "contact maps and mutational effects competitive with coevolution-based "
                    "methods, suggesting that evolutionary information is encoded compactly in "
                    "sequence alone. We evaluate generalization across protein families, compare "
                    "scaling laws for model width versus depth, and release a lightweight checkpoint "
                    "for community benchmarking on stability prediction tasks."
                ),
            },
            {
                "title": "When Do Sparse Training Trajectories Generalize? A PAC-Bayes Lens",
                "topic": "Machine Learning",
                "venue": "ICML",
                "published_at": "2025-07-18",
                "abstract": (
                    "Modern deep networks trained with aggressive sparsity masks exhibit brittle "
                    "optimization paths: small perturbations to mask schedules can flip generalization. "
                    "We derive data-dependent bounds showing that implicit regularization from "
                    "layerwise magnitude growth is insufficient when masks are rewired frequently, "
                    "and propose a simple stabilization rule grounded in empirical risk control."
                ),
            },
            {
                "title": "Attributing Extreme Precipitation in Coastal Cities to Ocean Warming Rates",
                "topic": "Climate Science",
                "venue": "Science Advances",
                "published_at": "2024-11-02",
                "abstract": (
                    "Combining convection-permitting regional simulations with a surrogate model of "
                    "sea-surface temperature trends, we quantify how hour-scale rainfall extremes "
                    "intensify when background warming is concentrated in the upper ocean mixed layer. "
                    "Results highlight asymmetries between Eastern and Western boundary currents and "
                    "inform infrastructure design standards for stormwater systems."
                ),
            },
            {
                "title": "Working Memory Precision Tracks Laminar Dynamics in Human Parietal Cortex",
                "topic": "Cognitive Neuroscience",
                "venue": "Neuron",
                "published_at": "2025-01-30",
                "abstract": (
                    "Using ultra-high-field fMRI and a delayed-estimation paradigm, we show that "
                    "trial-by-trial variability in recall precision aligns with layer-specific BOLD "
                    "profiles consistent with recurrent attractor dynamics. Modeling indicates that "
                    "noise injected at input stages is partially corrected by later parietal feedback, "
                    "revising purely feed-forward accounts of mnemonic noise."
                ),
            },
            {
                "title": "Fault-Tolerant Gates for Low-Overhead Bosonic Codes in Superconducting Circuits",
                "topic": "Quantum Computing",
                "venue": "Physical Review X",
                "published_at": "2024-08-21",
                "abstract": (
                    "We implement a hardware-efficient ancilla coupling scheme that preserves "
                    "the error-detecting properties of cat qubits while reducing the number of "
                    "Josepson junctions per logical operation by 35 percent. Characterizations on "
                    "a three-module processor demonstrate repeated error detection rounds with "
                    "stable logical coherence times exceeding single-physical-qubit limits."
                ),
            },
            {
                "title": "Participatory Auditing Interfaces Reduce Over-trust in Automated Hiring Tools",
                "topic": "HCI & Social Computing",
                "venue": "CSCW",
                "published_at": "2025-02-14",
                "abstract": (
                    "We study decision makers who interact with resume-screening systems that surface "
                    "uncertainty ranges for inferred skills. A longitudinal field deployment suggests "
                    "that lightweight explanation panels and contractor-authored critiques jointly "
                    "decrease automation bias without harming throughput, especially when audit trails "
                    "are shared across hiring managers."
                ),
            },
            {
                "title": "Graph Neural Operators for Mesoscale OceanTracer Transport",
                "topic": "Climate Science",
                "venue": "Journal of Advances in Modeling Earth Systems",
                "published_at": "2025-06-05",
                "abstract": (
                    "Neural surrogates trained on high-resolution tracer releases learn advection "
                    "patterns that remain stable under seasonal wind shifts. Coupling the surrogate "
                    "to a coarse climate model reduces bias in anthropogenic carbon uptake estimates "
                    "by improving representation of submesoscale filaments absent in standard closures."
                ),
            },
            {
                "title": "Certified Robustness for Vision Transformers Under Patch Corruptions",
                "topic": "Machine Learning",
                "venue": "NeurIPS",
                "published_at": "2024-12-09",
                "abstract": (
                    "Randomized smoothing with structured noise distributions yields non-vacuous "
                    "radius certificates for ViTs under localized patch occlusions common in "
                    "autonomous sensing. We analyze how positional embeddings interact with "
                    "smoothing variance and release an open toolkit for certifying patch-level "
                    "defenses on standard detection backbones."
                ),
            },
            {
                "title": "Single-Cell Atlas of Human Thymic Development Reveals Stochastic Commitment Windows",
                "topic": "Computational Biology",
                "venue": "Cell",
                "published_at": "2025-05-22",
                "abstract": (
                    "Multimodal profiling of pediatric thymic tissue resolves rare transitional states "
                    "between double-positive and single-positive T cells. A branching process model "
                    "fit to lineage tracing data supports a short stochastic window regulating "
                    "negative selection efficiency, with implications for engineered thymic organoids."
                ),
            },
            {
                "title": "Mechanistic Interpretability for Scientific Foundation Models: A Case Study in Materials",
                "topic": "Machine Learning",
                "venue": "Nature Machine Intelligence",
                "published_at": "2025-04-08",
                "abstract": (
                    "We trace intermediate activations of transformer models trained on crystal "
                    "structures and show that certain attention heads selectively lock onto symmetry "
                    "operations analogous to group convolution priors. Ablation studies connect those "
                    "heads to accurate formation-energy ranking on out-of-distribution space groups."
                ),
            },
            {
                "title": "Sleep Spindle Coupling Predicts Next-Day Skill Consolidation Better Than REM Duration",
                "topic": "Cognitive Neuroscience",
                "venue": "Current Biology",
                "published_at": "2024-10-17",
                "abstract": (
                    "In a preregistered motor learning study with dense polysomnography, multivariate "
                    "indices of spindle–slow-oscillation coupling explain more variance in overnight "
                    "gains than conventional sleep-stage durations. Closed-loop auditory stimulation "
                    "targeting coupling phases enhanced consolidation without increasing total sleep time."
                ),
            },
            {
                "title": "Sustainable CS Education: Measuring Carbon Footprint of Large Programming Courses",
                "topic": "HCI & Social Computing",
                "venue": "SIGCSE",
                "published_at": "2025-03-01",
                "abstract": (
                    "We instrument autograding clusters, cloud IDE sessions, and CI pipelines for a "
                    "multi-campus introductory CS sequence. The largest contributors are redundant "
                    "container rebuilds and always-on GPU sandboxes; modest scheduling changes and "
                    "result caching cut operational emissions by forty percent semester-over-semester."
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
