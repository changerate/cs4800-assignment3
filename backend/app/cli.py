import click
from flask import Flask

from app.extensions import db
from app.models import Vehicle


def register_commands(app: Flask) -> None:
    @app.cli.command("seed-vehicles")
    def seed_vehicles() -> None:
        """Insert default vehicles if the table is empty."""
        if Vehicle.query.count() > 0:
            click.echo("Vehicles already seeded.")
            return
        defaults = [
            Vehicle(name="Compact"),
            Vehicle(name="Sedan"),
            Vehicle(name="SUV"),
            Vehicle(name="Truck"),
        ]
        db.session.add_all(defaults)
        db.session.commit()
        click.echo(f"Seeded {len(defaults)} vehicles.")
