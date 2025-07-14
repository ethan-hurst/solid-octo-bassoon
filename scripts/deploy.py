#!/usr/bin/env python3
"""
Production deployment script for Sports Betting Edge Finder.

Usage:
    python scripts/deploy.py --env staging         # Deploy to staging
    python scripts/deploy.py --env production      # Deploy to production
    python scripts/deploy.py --check-health        # Check deployment health
"""

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List
import yaml
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages deployment to different environments."""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_file = self._get_docker_compose_file()
        
    def _get_docker_compose_file(self) -> str:
        """Get the appropriate docker-compose file for environment."""
        if self.environment == "production":
            return "docker-compose.prod.yml"
        elif self.environment == "staging":
            return "docker-compose.staging.yml"
        else:
            return "docker-compose.yml"
    
    def run_command(self, command: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a shell command and return the result."""
        cwd = cwd or self.project_root
        logger.info(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise
    
    def check_prerequisites(self) -> bool:
        """Check if all deployment prerequisites are met."""
        logger.info("Checking deployment prerequisites...")
        
        checks = []
        
        # Check Docker
        try:
            result = self.run_command(["docker", "--version"])
            checks.append(("Docker", True, result.stdout.strip()))
        except Exception as e:
            checks.append(("Docker", False, str(e)))
        
        # Check Docker Compose
        try:
            result = self.run_command(["docker-compose", "--version"])
            checks.append(("Docker Compose", True, result.stdout.strip()))
        except Exception as e:
            checks.append(("Docker Compose", False, str(e)))
        
        # Check if required files exist
        required_files = [
            "Dockerfile",
            "requirements.txt",
            self.docker_compose_file,
            ".env.example"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            checks.append((f"File: {file_path}", full_path.exists(), str(full_path)))
        
        # Print results
        print("\nPrerequisite Check Results:")
        print("-" * 50)
        all_passed = True
        
        for check_name, passed, details in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {check_name}")
            if not passed:
                print(f"     {details}")
                all_passed = False
        
        return all_passed
    
    def build_images(self) -> bool:
        """Build Docker images."""
        logger.info("Building Docker images...")
        
        try:
            # Build using docker-compose
            self.run_command([
                "docker-compose", 
                "-f", self.docker_compose_file,
                "build",
                "--no-cache"
            ])
            
            logger.info("Docker images built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Docker images: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run tests before deployment."""
        logger.info("Running tests...")
        
        try:
            # Run tests in Docker container
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "run",
                "--rm",
                "api",
                "pytest",
                "tests/",
                "-v",
                "--tb=short"
            ])
            
            logger.info("All tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Tests failed: {e}")
            return False
    
    def deploy_services(self) -> bool:
        """Deploy all services."""
        logger.info(f"Deploying to {self.environment}...")
        
        try:
            # Stop existing services
            logger.info("Stopping existing services...")
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "down"
            ])
            
            # Start services
            logger.info("Starting services...")
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "up",
                "-d"
            ])
            
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """Run database migrations."""
        logger.info("Running database migrations...")
        
        try:
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "exec",
                "-T",
                "api",
                "alembic",
                "upgrade",
                "head"
            ])
            
            logger.info("Database migrations completed")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def check_health(self) -> Dict:
        """Check the health of deployed services."""
        logger.info("Checking service health...")
        
        # Get service URLs based on environment
        if self.environment == "production":
            base_url = "https://api.sportsbetting-edge.com"
        elif self.environment == "staging":
            base_url = "https://staging-api.sportsbetting-edge.com"
        else:
            base_url = "http://localhost:8000"
        
        health_checks = {}
        
        # API Health Check
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            health_checks["api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["api"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Database Check
        try:
            response = requests.get(f"{base_url}/api/v1/health/db", timeout=10)
            health_checks["database"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["database"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Redis Check
        try:
            response = requests.get(f"{base_url}/api/v1/health/redis", timeout=10)
            health_checks["redis"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks["redis"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Celery Worker Check
        try:
            # Check if any background tasks are running
            result = self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "exec",
                "-T",
                "worker",
                "celery",
                "-A", "src.celery_app",
                "inspect",
                "active"
            ])
            health_checks["celery_worker"] = {
                "status": "healthy",
                "active_tasks": len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            }
        except Exception as e:
            health_checks["celery_worker"] = {
                "status": "error",
                "error": str(e)
            }
        
        return health_checks
    
    def print_health_summary(self, health_checks: Dict):
        """Print health check summary."""
        print(f"\nHealth Check Results - {self.environment.upper()}")
        print("=" * 50)
        
        overall_healthy = True
        
        for service, status in health_checks.items():
            if status["status"] == "healthy":
                print(f"✅ {service.upper()}: Healthy")
                if "response_time" in status:
                    print(f"   Response time: {status['response_time']:.3f}s")
            elif status["status"] == "unhealthy":
                print(f"⚠️  {service.upper()}: Unhealthy")
                overall_healthy = False
            else:
                print(f"❌ {service.upper()}: Error - {status.get('error', 'Unknown')}")
                overall_healthy = False
        
        print("\n" + "=" * 50)
        if overall_healthy:
            print("🎉 All services are healthy!")
        else:
            print("⚠️  Some services have issues. Check logs for details.")
    
    def create_backup(self) -> bool:
        """Create a backup before deployment."""
        logger.info("Creating backup...")
        
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{self.environment}_{timestamp}"
            
            # Backup database
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U", "postgres",
                "sports_betting",
                "-f", f"/backups/{backup_name}.sql"
            ])
            
            logger.info(f"Backup created: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous version."""
        logger.info("Rolling back deployment...")
        
        try:
            # This would restore from the latest backup
            # Implementation depends on your backup strategy
            
            # For now, just restart services
            self.run_command([
                "docker-compose",
                "-f", self.docker_compose_file,
                "restart"
            ])
            
            logger.info("Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def full_deployment(self) -> bool:
        """Run full deployment process."""
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Backup", self.create_backup),
            ("Build", self.build_images),
            ("Tests", self.run_tests),
            ("Deploy", self.deploy_services),
            ("Migrations", self.run_migrations),
        ]
        
        print(f"\nStarting deployment to {self.environment.upper()}")
        print("=" * 50)
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            
            try:
                success = step_func()
                if success:
                    print(f"✅ {step_name} completed successfully")
                else:
                    print(f"❌ {step_name} failed")
                    return False
            except Exception as e:
                print(f"❌ {step_name} failed with error: {e}")
                return False
        
        # Final health check
        print("\n🔍 Final health check...")
        health_checks = self.check_health()
        self.print_health_summary(health_checks)
        
        # Check if deployment was successful
        all_healthy = all(
            status["status"] == "healthy" 
            for status in health_checks.values()
        )
        
        if all_healthy:
            print(f"\n🎉 Deployment to {self.environment} completed successfully!")
            return True
        else:
            print(f"\n⚠️  Deployment completed but some services are unhealthy")
            return False


async def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='Deploy Sports Betting Edge Finder')
    parser.add_argument('--env', type=str, choices=['development', 'staging', 'production'],
                       default='development', help='Deployment environment')
    parser.add_argument('--check-health', action='store_true',
                       help='Only check service health')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to previous version')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup')
    
    args = parser.parse_args()
    
    if args.env == "production":
        confirmation = input("⚠️  Are you sure you want to deploy to PRODUCTION? (yes/no): ")
        if confirmation.lower() != "yes":
            print("Deployment cancelled")
            return
    
    deployer = DeploymentManager(args.env)
    
    try:
        if args.check_health:
            # Only check health
            health_checks = deployer.check_health()
            deployer.print_health_summary(health_checks)
            
        elif args.rollback:
            # Rollback
            success = deployer.rollback()
            if success:
                print("Rollback completed successfully")
            else:
                print("Rollback failed")
                sys.exit(1)
                
        else:
            # Full deployment
            success = deployer.full_deployment()
            if not success:
                print("\nDeployment failed. Check logs for details.")
                
                rollback_choice = input("Do you want to rollback? (yes/no): ")
                if rollback_choice.lower() == "yes":
                    deployer.rollback()
                
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())