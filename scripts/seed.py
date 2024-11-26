# scripts/seed.py
import asyncio
import typer
from typing import Optional
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

# Then import the rest
from app.db.session import AsyncSessionLocal
from app.database.seeder_registry import SeederRegistry
from app.models.seeder_version import SeederVersion

app = typer.Typer()


async def get_seeded_versions(session) -> set:
    # Import select at the top of the file
    from sqlalchemy import select

    # Use select() instead of query()
    result = await session.execute(select(SeederVersion.version_num))
    # Use scalars() to get the actual values
    return {r for r in result.scalars()}


@app.command()
def seed(version: Optional[str] = None):
    """Run database seeders"""

    async def run_seeder():
        async with AsyncSessionLocal() as session:
            seeded_versions = await get_seeded_versions(session)

            for seeder in SeederRegistry.get_all_seeders():
                if version and seeder.version != version:
                    continue

                if seeder.version not in seeded_versions:
                    typer.echo(f"Running seeder: {seeder.version}")
                    await seeder.seed(session)
                else:
                    typer.echo(f"Seeder already run: {seeder.version}")

    asyncio.run(run_seeder())


@app.command()
def unseed(version: Optional[str] = None):
    """Remove seeded data"""

    async def run_unseeder():
        async with AsyncSessionLocal() as session:
            seeded_versions = await get_seeded_versions(session)

            for seeder in reversed(SeederRegistry.get_all_seeders()):
                if version and seeder.version != version:
                    continue

                if seeder.version in seeded_versions:
                    typer.echo(f"Removing seeded data: {seeder.version}")
                    await seeder.unseed(session)

    asyncio.run(run_unseeder())


if __name__ == "__main__":
    app()


# Run semua seeder
# poetry run python -m scripts.seed seed
# poetry run python -m scripts.seed unseed
