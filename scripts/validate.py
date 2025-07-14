#!/usr/bin/env python3
"""
Validation script for Sports Betting Edge Finder.

This script validates the project structure, syntax, imports, and configuration
without requiring all dependencies to be installed.

Usage:
    python scripts/validate.py                     # Full validation
    python scripts/validate.py --syntax-only      # Syntax check only
    python scripts/validate.py --structure-only   # Structure check only
"""

import argparse
import ast
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectValidator:
    """Validates the project structure and code quality."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.errors = []
        self.warnings = []
        
    def validate_project_structure(self) -> bool:
        """Validate expected project structure."""
        logger.info("Validating project structure...")
        
        expected_structure = {
            "src": ["config", "models", "api", "data_collection", "analysis", "alerts", "utils"],
            "src/config": ["settings.py"],
            "src/models": ["schemas.py", "database.py"],
            "src/api": ["main.py", "dependencies.py", "routers"],
            "src/api/routers": ["odds.py", "analysis.py", "alerts.py"],
            "src/data_collection": ["odds_aggregator.py", "cache_manager.py"],
            "src/analysis": ["ml_models.py", "value_calculator.py"],
            "src/alerts": ["websocket_manager.py", "notification_service.py", "redis_pubsub.py"],
            "tests": ["conftest.py", "test_odds_aggregator.py", "test_value_calculator.py"],
            "scripts": ["train_models.py", "evaluate_models.py", "deploy.py", "setup.py"],
            ".": ["requirements.txt", "docker-compose.yml", "README.md", "alembic.ini"]
        }
        
        structure_valid = True
        
        for directory, expected_files in expected_structure.items():
            if directory == ".":
                dir_path = self.project_root
            else:
                dir_path = self.project_root / directory
            
            if not dir_path.exists():
                self.errors.append(f"Missing directory: {directory}")
                structure_valid = False
                continue
            
            for expected_file in expected_files:
                file_path = dir_path / expected_file
                if not file_path.exists():
                    self.errors.append(f"Missing file: {directory}/{expected_file}")
                    structure_valid = False
        
        if structure_valid:
            logger.info("✅ Project structure is valid")
        else:
            logger.error("❌ Project structure issues found")
        
        return structure_valid
    
    def validate_python_syntax(self) -> bool:
        """Check Python syntax in all source files."""
        logger.info("Validating Python syntax...")
        
        python_files = []
        
        # Find all Python files
        for pattern in ["src/**/*.py", "tests/**/*.py", "scripts/**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))
        
        syntax_valid = True
        checked_files = 0
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Parse the AST to check syntax
                ast.parse(source, filename=str(py_file))
                checked_files += 1
                
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {py_file}: Line {e.lineno}, {e.msg}")
                syntax_valid = False
            except UnicodeDecodeError:
                self.warnings.append(f"Unicode decode error in {py_file}")
            except Exception as e:
                self.warnings.append(f"Could not check {py_file}: {e}")
        
        if syntax_valid:
            logger.info(f"✅ Python syntax is valid ({checked_files} files checked)")
        else:
            logger.error("❌ Python syntax errors found")
        
        return syntax_valid
    
    def validate_imports(self) -> bool:
        """Validate import statements and detect circular imports."""
        logger.info("Validating imports...")
        
        python_files = list(self.project_root.glob("src/**/*.py"))
        imports_valid = True
        
        # Track imports for circular dependency detection
        import_graph = {}
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source, filename=str(py_file))
                
                # Get relative path for module name
                rel_path = py_file.relative_to(self.project_root)
                module_name = str(rel_path).replace('/', '.').replace('\\', '.')[:-3]  # Remove .py
                
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                import_graph[module_name] = imports
                
                # Check for potential issues
                for imp in imports:
                    # Check for relative imports outside package
                    if imp.startswith('.') and not imp.startswith('src.'):
                        self.warnings.append(f"Relative import in {py_file}: {imp}")
                
            except Exception as e:
                self.warnings.append(f"Could not analyze imports in {py_file}: {e}")
                imports_valid = False
        
        # Simple circular import detection
        def has_circular_dependency(module, target, visited=None):
            if visited is None:
                visited = set()
            
            if module in visited:
                return True
            
            visited.add(module)
            
            for imported in import_graph.get(module, []):
                if imported == target:
                    return True
                if has_circular_dependency(imported, target, visited.copy()):
                    return True
            
            return False
        
        # Check for circular dependencies
        for module in import_graph:
            for imported in import_graph[module]:
                if has_circular_dependency(imported, module):
                    self.warnings.append(f"Potential circular import: {module} <-> {imported}")
        
        if imports_valid:
            logger.info("✅ Import structure appears valid")
        else:
            logger.error("❌ Import validation issues found")
        
        return imports_valid
    
    def validate_configuration(self) -> bool:
        """Validate configuration files."""
        logger.info("Validating configuration...")
        
        config_valid = True
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().strip().split('\n')
                
                # Check for essential dependencies
                essential_deps = [
                    'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'celery',
                    'pydantic', 'pytest', 'httpx', 'scikit-learn', 'pandas'
                ]
                
                req_names = [req.split('==')[0].split('>=')[0].split('~=')[0] for req in requirements if req.strip()]
                
                for dep in essential_deps:
                    if dep not in req_names:
                        self.warnings.append(f"Missing essential dependency: {dep}")
                
                logger.info(f"✅ Requirements.txt has {len(requirements)} dependencies")
                
            except Exception as e:
                self.errors.append(f"Could not validate requirements.txt: {e}")
                config_valid = False
        else:
            self.errors.append("Missing requirements.txt")
            config_valid = False
        
        # Check Docker configuration
        docker_file = self.project_root / "Dockerfile"
        if not docker_file.exists():
            self.warnings.append("Missing Dockerfile")
        
        docker_compose = self.project_root / "docker-compose.yml"
        if not docker_compose.exists():
            self.warnings.append("Missing docker-compose.yml")
        
        # Check Alembic configuration
        alembic_ini = self.project_root / "alembic.ini"
        if not alembic_ini.exists():
            self.warnings.append("Missing alembic.ini")
        
        return config_valid
    
    def validate_test_coverage(self) -> bool:
        """Check if main modules have corresponding tests."""
        logger.info("Validating test coverage...")
        
        # Get all source modules
        src_modules = set()
        for py_file in self.project_root.glob("src/**/*.py"):
            if py_file.name != "__init__.py":
                rel_path = py_file.relative_to(self.src_path)
                module_name = str(rel_path)[:-3].replace('/', '_').replace('\\', '_')
                src_modules.add(module_name)
        
        # Get all test files
        test_files = set()
        for py_file in self.project_root.glob("tests/test_*.py"):
            test_name = py_file.name[5:-3]  # Remove "test_" prefix and ".py" suffix
            test_files.add(test_name)
        
        # Check coverage
        coverage_issues = []
        important_modules = [
            'odds_aggregator', 'value_calculator', 'ml_models', 
            'websocket_manager', 'api', 'database'
        ]
        
        for module in important_modules:
            # Check if there's a corresponding test file
            test_exists = any(module in test_file for test_file in test_files)
            if not test_exists:
                coverage_issues.append(f"No test file found for important module: {module}")
        
        if coverage_issues:
            for issue in coverage_issues:
                self.warnings.append(issue)
        
        test_count = len(list(self.project_root.glob("tests/test_*.py")))
        logger.info(f"✅ Found {test_count} test files")
        
        return len(coverage_issues) == 0
    
    def validate_code_quality(self) -> bool:
        """Check basic code quality metrics."""
        logger.info("Validating code quality...")
        
        quality_issues = []
        
        # Check for basic code quality issues
        for py_file in self.project_root.glob("src/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Check file length
                if len(lines) > 500:
                    quality_issues.append(f"Large file (>{len(lines)} lines): {py_file}")
                
                # Check for very long lines
                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        quality_issues.append(f"Long line in {py_file}:{i} ({len(line)} chars)")
                
                # Check for TODO/FIXME comments
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    if 'todo' in line_lower or 'fixme' in line_lower:
                        self.warnings.append(f"TODO/FIXME in {py_file}:{i}")
                
            except Exception as e:
                self.warnings.append(f"Could not check code quality for {py_file}: {e}")
        
        if quality_issues:
            for issue in quality_issues:
                self.warnings.append(issue)
        
        logger.info(f"✅ Code quality check completed")
        return len(quality_issues) == 0
    
    def run_full_validation(self) -> bool:
        """Run all validation checks."""
        logger.info("Starting full project validation...")
        
        checks = [
            ("Project Structure", self.validate_project_structure),
            ("Python Syntax", self.validate_python_syntax),
            ("Import Structure", self.validate_imports),
            ("Configuration", self.validate_configuration),
            ("Test Coverage", self.validate_test_coverage),
            ("Code Quality", self.validate_code_quality),
        ]
        
        results = {}
        overall_success = True
        
        for check_name, check_func in checks:
            logger.info(f"\n🔍 Running {check_name} validation...")
            try:
                success = check_func()
                results[check_name] = success
                if not success:
                    overall_success = False
            except Exception as e:
                logger.error(f"Validation check '{check_name}' failed with error: {e}")
                results[check_name] = False
                overall_success = False
        
        self.print_validation_summary(results)
        return overall_success
    
    def print_validation_summary(self, results: Dict[str, bool]):
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        # Print check results
        for check_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {check_name}")
        
        # Print errors
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        # Print warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        # Overall status
        print("\n" + "="*80)
        if not self.errors and all(results.values()):
            print("🎉 ALL VALIDATION CHECKS PASSED!")
        elif not self.errors:
            print("✅ VALIDATION COMPLETED WITH WARNINGS")
        else:
            print("❌ VALIDATION FAILED - ISSUES FOUND")
        
        print("="*80)


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description='Validate Sports Betting Edge Finder project')
    parser.add_argument('--syntax-only', action='store_true',
                       help='Only check Python syntax')
    parser.add_argument('--structure-only', action='store_true',
                       help='Only check project structure')
    parser.add_argument('--imports-only', action='store_true',
                       help='Only check import structure')
    
    args = parser.parse_args()
    
    validator = ProjectValidator()
    
    try:
        if args.syntax_only:
            success = validator.validate_python_syntax()
        elif args.structure_only:
            success = validator.validate_project_structure()
        elif args.imports_only:
            success = validator.validate_imports()
        else:
            success = validator.run_full_validation()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()