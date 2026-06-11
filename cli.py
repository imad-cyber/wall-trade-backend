"""
CLI commands and utilities for project management.
Run with: python cli.py --help
"""
import click
import os
from pathlib import Path
from dotenv import load_dotenv


@click.group()
def cli():
    """Wall-Trade-Backend CLI utility."""
    pass


@cli.command()
def create_env():
    """Create .env file from template."""
    env_template = Path(".env.example")
    env_file = Path(".env")

    if env_file.exists():
        click.echo("❌ .env file already exists!")
        return

    if not env_template.exists():
        click.echo("❌ .env.example not found!")
        return

    env_file.write_text(env_template.read_text())
    click.echo("✅ .env file created from template. Please configure it!")


@cli.command()
def create_logs_dir():
    """Create logs directory."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    click.echo("✅ Logs directory created!")


@cli.command()
def init_project():
    """Initialize project with all necessary setup."""
    click.echo("🚀 Initializing Wall-Trade-Backend...")

    # Create .env
    try:
        create_env()
    except Exception as e:
        click.echo(f"⚠️  Could not create .env: {str(e)}")

    # Create logs directory
    try:
        create_logs_dir()
    except Exception as e:
        click.echo(f"⚠️  Could not create logs directory: {str(e)}")

    click.echo("✅ Project initialization complete!")
    click.echo("\n📝 Next steps:")
    click.echo("1. Edit .env file with your configuration")
    click.echo("2. Run: pip install -r requirements.txt")
    click.echo("3. Run: python run.py")


@cli.command()
def health_check():
    """Check if application is properly configured."""
    load_dotenv()

    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        click.echo(
            f"❌ Missing required environment variables: {', '.join(missing_vars)}"
        )
        return

    click.echo("✅ Application is properly configured!")
    click.echo(f"✅ Environment: {os.getenv('ENVIRONMENT', 'development')}")
    click.echo(f"✅ Debug mode: {os.getenv('DEBUG', 'False')}")


if __name__ == "__main__":
    cli()
