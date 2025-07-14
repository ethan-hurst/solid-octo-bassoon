#!/usr/bin/env python3
"""
Initial setup script for Sports Betting Edge Finder.

This script sets up the development environment, initializes the database,
and prepares the application for first use.

Usage:
    python scripts/setup.py                    # Full setup
    python scripts/setup.py --docker          # Setup with Docker
    python scripts/setup.py --db-only         # Database setup only
"""

import argparse
import asyncio
import logging
import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import List, Dict
import secrets

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SetupManager:
    """Manages initial setup of the application."""
    
    def __init__(self, use_docker: bool = False):
        self.use_docker = use_docker
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv_linux"
        
    def run_command(self, command: List[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command."""
        cwd = cwd or self.project_root
        logger.info(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stdout:
                logger.error(f"STDOUT: {e.stdout}")
            if e.stderr:
                logger.error(f"STDERR: {e.stderr}")
            if check:
                raise
            return e
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if required tools are installed."""
        logger.info("Checking prerequisites...")
        
        checks = {}
        
        # Check Python version
        try:
            import sys
            version = sys.version_info
            python_ok = version.major == 3 and version.minor >= 11
            checks["python"] = python_ok
            if python_ok:
                logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
            else:
                logger.error(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        except Exception:
            checks["python"] = False
            logger.error("❌ Python not found")
        
        # Check pip
        try:
            result = self.run_command(["pip", "--version"], check=False)
            checks["pip"] = result.returncode == 0
            if checks["pip"]:
                logger.info("✅ pip is available")
        except Exception:
            checks["pip"] = False
            logger.error("❌ pip not found")
        
        # Check Docker (if using Docker)
        if self.use_docker:
            try:
                result = self.run_command(["docker", "--version"], check=False)
                checks["docker"] = result.returncode == 0
                if checks["docker"]:
                    logger.info("✅ Docker is available")
            except Exception:
                checks["docker"] = False
                logger.error("❌ Docker not found")
            
            try:
                result = self.run_command(["docker-compose", "--version"], check=False)
                checks["docker_compose"] = result.returncode == 0
                if checks["docker_compose"]:
                    logger.info("✅ Docker Compose is available")
            except Exception:
                checks["docker_compose"] = False
                logger.error("❌ Docker Compose not found")
        
        return checks
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment."""
        if self.use_docker:
            logger.info("Skipping virtual environment (using Docker)")
            return True
            
        logger.info("Creating virtual environment...")
        
        try:
            if self.venv_path.exists():
                logger.info("Virtual environment already exists")
                return True
            
            # Create virtual environment
            self.run_command([sys.executable, "-m", "venv", str(self.venv_path)])
            
            # Activate and upgrade pip
            if os.name == 'nt':  # Windows
                pip_path = self.venv_path / "Scripts" / "pip"
            else:  # Unix/Linux
                pip_path = self.venv_path / "bin" / "pip"
            
            self.run_command([str(pip_path), "install", "--upgrade", "pip"])
            
            logger.info("✅ Virtual environment created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        logger.info("Installing dependencies...")
        
        try:
            if self.use_docker:
                # Use Docker to install dependencies
                self.run_command([
                    "docker", "build", "-t", "sports-betting-setup", "."
                ])
            else:
                # Use pip in virtual environment
                if os.name == 'nt':  # Windows
                    pip_path = self.venv_path / "Scripts" / "pip"
                else:  # Unix/Linux
                    pip_path = self.venv_path / "bin" / "pip"
                
                self.run_command([
                    str(pip_path), "install", "-r", "requirements.txt"
                ])
            
            logger.info("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env file from template."""
        logger.info("Creating environment file...")
        
        try:
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if env_file.exists():
                logger.info(".env file already exists")
                return True
            
            if not env_example.exists():
                logger.warning(".env.example not found, creating basic .env")
                self._create_basic_env_file(env_file)
            else:
                # Copy from example and update with generated values
                shutil.copy(env_example, env_file)
                self._update_env_file(env_file)
            
            logger.info("✅ Environment file created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def _create_basic_env_file(self, env_file: Path):
        """Create a basic .env file."""
        content = f"""# Sports Betting Edge Finder Environment Configuration

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sports_betting
REDIS_URL=redis://localhost:6379

# The Odds API
ODDS_API_KEY=your_api_key_here
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4

# Security
SECRET_KEY={secrets.token_urlsafe(32)}
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application Settings
MIN_EDGE_THRESHOLD=0.05
MAX_KELLY_FRACTION=0.25
MAX_BANKROLL_PERCENTAGE=0.10

# Environment
ENVIRONMENT=development
DEBUG=true
"""
        env_file.write_text(content)
    
    def _update_env_file(self, env_file: Path):
        """Update .env file with generated values."""
        content = env_file.read_text()
        
        # Generate secure secret key
        if "SECRET_KEY=changeme" in content or "SECRET_KEY=" in content:
            secret_key = secrets.token_urlsafe(32)
            content = content.replace("SECRET_KEY=changeme", f"SECRET_KEY={secret_key}")
        
        env_file.write_text(content)
    
    def setup_database(self) -> bool:
        """Set up the database."""
        logger.info("Setting up database...")
        
        try:
            if self.use_docker:
                # Start database with Docker
                self.run_command([
                    "docker-compose", "up", "-d", "postgres", "redis"
                ])
                
                # Wait for database to be ready
                import time
                logger.info("Waiting for database to be ready...")
                time.sleep(10)
                
                # Run migrations
                self.run_command([
                    "docker-compose", "run", "--rm", "api",
                    "alembic", "upgrade", "head"
                ])
            else:
                # Check if PostgreSQL and Redis are running locally
                logger.info("Make sure PostgreSQL and Redis are running locally")
                logger.info("Creating database if it doesn't exist...")
                
                # Try to create database (might fail if it exists, which is OK)
                try:
                    self.run_command([
                        "createdb", "-U", "postgres", "sports_betting"
                    ], check=False)
                except Exception:
                    pass  # Database might already exist
                
                # Run migrations
                if os.name == 'nt':  # Windows
                    python_path = self.venv_path / "Scripts" / "python"
                else:  # Unix/Linux
                    python_path = self.venv_path / "bin" / "python"
                
                # Create alembic.ini if it doesn't exist
                self._ensure_alembic_config()
                
                self.run_command([
                    str(python_path), "-m", "alembic", "upgrade", "head"
                ])
            
            logger.info("✅ Database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
    
    def _ensure_alembic_config(self):
        """Ensure alembic.ini exists."""
        alembic_ini = self.project_root / "alembic.ini"
        if not alembic_ini.exists():
            content = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %(rev)s

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# The output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql+asyncpg://postgres:password@localhost:5432/sports_betting

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
            alembic_ini.write_text(content)
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        logger.info("Creating directories...")
        
        directories = [
            "logs",
            "models",
            "backups",
            "evaluation_results"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                
                # Create .gitkeep for empty directories
                gitkeep = dir_path / ".gitkeep"
                if not any(dir_path.iterdir()):
                    gitkeep.touch()
            
            logger.info("✅ Directories created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def run_initial_tests(self) -> bool:
        """Run initial tests to verify setup."""
        logger.info("Running initial tests...")
        
        try:
            if self.use_docker:
                self.run_command([
                    "docker-compose", "run", "--rm", "api",
                    "pytest", "tests/", "-v", "--tb=short", "-x"
                ])
            else:
                if os.name == 'nt':  # Windows
                    python_path = self.venv_path / "Scripts" / "python"
                else:  # Unix/Linux
                    python_path = self.venv_path / "bin" / "python"
                
                self.run_command([
                    str(python_path), "-m", "pytest", "tests/", "-v", "--tb=short", "-x"
                ])
            
            logger.info("✅ Initial tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Tests failed: {e}")
            return False
    
    def print_setup_complete(self):
        """Print setup completion message."""
        print("\n" + "="*80)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        if self.use_docker:
            print("\nTo start the application with Docker:")
            print("  docker-compose up")
            print("\nTo stop the application:")
            print("  docker-compose down")
        else:
            print("\nTo activate the virtual environment:")
            if os.name == 'nt':  # Windows
                print(f"  {self.venv_path}\\Scripts\\activate")
            else:  # Unix/Linux
                print(f"  source {self.venv_path}/bin/activate")
            
            print("\nTo start the application:")
            print("  uvicorn src.api.main:app --reload")
            print("\nTo start Celery worker:")
            print("  celery -A src.celery_app worker --loglevel=info")
        
        print("\nNext steps:")
        print("1. Get an API key from The Odds API (https://the-odds-api.com/)")
        print("2. Update ODDS_API_KEY in .env file")
        print("3. Start the application")
        print("4. Visit http://localhost:8000/docs for API documentation")
        
        print("\nUseful commands:")
        print("  python scripts/train_models.py     # Train ML models")
        print("  python scripts/evaluate_models.py  # Evaluate models")
        print("  pytest tests/                      # Run tests")
        
        print("\n" + "="*80)
    
    def full_setup(self) -> bool:
        """Run the complete setup process."""
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Virtual Environment", self.create_virtual_environment),
            ("Dependencies", self.install_dependencies),
            ("Environment File", self.create_env_file),
            ("Directories", self.create_directories),
            ("Database", self.setup_database),
            ("Tests", self.run_initial_tests),
        ]
        
        print(f"\nStarting setup ({'Docker' if self.use_docker else 'Local'})")
        print("=" * 50)
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            
            try:
                if step_name == "Prerequisites":
                    checks = step_func()
                    success = all(checks.values())
                else:
                    success = step_func()
                
                if success:
                    print(f"✅ {step_name} completed")
                else:
                    print(f"❌ {step_name} failed")
                    return False
                    
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                return False
        
        self.print_setup_complete()
        return True


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Setup Sports Betting Edge Finder')
    parser.add_argument('--docker', action='store_true',
                       help='Use Docker for setup')
    parser.add_argument('--db-only', action='store_true',
                       help='Only setup database')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip running tests')
    
    args = parser.parse_args()
    
    setup_manager = SetupManager(use_docker=args.docker)
    
    try:
        if args.db_only:
            success = setup_manager.setup_database()
        else:
            success = setup_manager.full_setup()
        
        if not success:
            print("\n❌ Setup failed. Check the logs above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()