#!/usr/bin/env python3
"""
Code Review Agent for PostgreSQL Query Tool
Validates codebase against architectural guidelines, coding standards,
security requirements, and production safety rules.
"""

import os
import re
import ast
import json
import argparse
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class Severity(Enum):
    """Violation severity levels."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Violation:
    """Represents a code review violation."""
    file: str
    line: int
    severity: Severity
    category: str
    message: str
    suggestion: str
    code_snippet: Optional[str] = None


class CodeChecker(ABC):
    """Abstract base class for code checkers."""
    
    @abstractmethod
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        """
        Check a file for violations.
        
        Args:
            filepath: Path to the file being checked
            content: File content as string
            ast_tree: Parsed AST (if available)
            
        Returns:
            List of violations found
        """
        pass


class ArchitectureChecker(CodeChecker):
    """Validates architectural integrity and modularity."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        # Determine module type
        is_backend = '/backend/' in filepath
        is_frontend = '/frontend/' in filepath
        is_state = filepath.endswith('state.py')
        
        # Check for cross-contamination between backend and frontend
        for i, line in enumerate(lines, 1):
            # Backend importing frontend
            if is_backend and re.search(r'from\s+.*\.frontend\s+import|import\s+.*\.frontend', line):
                violations.append(Violation(
                    file=filepath,
                    line=i,
                    severity=Severity.CRITICAL,
                    category="Architecture",
                    message="Backend module importing from frontend",
                    suggestion="Backend logic must remain separate from frontend. Move shared logic to state.py or a separate utility module.",
                    code_snippet=line.strip()
                ))
            
            # Frontend importing backend (some imports are allowed for types/config)
            if is_frontend and re.search(r'from\s+.*\.backend\s+import|import\s+.*\.backend', line):
                # Allow specific imports like config_mgr, history_mgr for state access
                if not re.search(r'(config_mgr|history_mgr|discovery|log_engine|log_parser)', line):
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.WARNING,
                        category="Architecture",
                        message="Frontend module importing from backend (verify necessity)",
                        suggestion="Frontend should primarily interact through state.py. Only import backend modules if absolutely necessary for type hints or configuration.",
                        code_snippet=line.strip()
                    ))
            
            # Check for direct rx.State usage outside state.py
            if not is_state and 'class' in line and 'rx.State' in line:
                violations.append(Violation(
                    file=filepath,
                    line=i,
                    severity=Severity.CRITICAL,
                    category="Architecture",
                    message="State class defined outside state.py",
                    suggestion="All state management must be centralized in state.py as single source of truth.",
                    code_snippet=line.strip()
                ))
        
        return violations


class CodingStandardsChecker(CodeChecker):
    """Validates async patterns, type hints, and thread safety."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        # Check for blocking psycopg2 calls
        for i, line in enumerate(lines, 1):
            if 'psycopg2' in line and 'import' in line:
                violations.append(Violation(
                    file=filepath,
                    line=i,
                    severity=Severity.CRITICAL,
                    category="Coding Standards",
                    message="Blocking psycopg2 import detected",
                    suggestion="Use asyncpg for all database operations. psycopg2 should only be used as optional fallback, never in main thread.",
                    code_snippet=line.strip()
                ))
            
            # Check for missing async with self in background tasks
            if '@rx.background' in lines[max(0, i-2):i]:
                # Check if function has state modifications without async with self
                func_start = i
                func_content = []
                indent_level = len(line) - len(line.lstrip())
                
                for j in range(i, min(i + 50, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent <= indent_level and j > i:
                            break
                        func_content.append(lines[j])
                
                func_text = '\n'.join(func_content)
                has_state_mod = re.search(r'self\.\w+\s*=', func_text)
                has_async_with = 'async with self:' in func_text
                
                if has_state_mod and not has_async_with:
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.CRITICAL,
                        category="Coding Standards",
                        message="State modification in background task without 'async with self:'",
                        suggestion="Every state modification within a background task must be wrapped in 'async with self:' for thread safety.",
                        code_snippet=line.strip()
                    ))
        
        # Use AST to check type hints if available
        if ast_tree:
            for node in ast.walk(ast_tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip special methods and simple property getters
                    if node.name.startswith('_') or len(node.body) <= 2:
                        continue
                    
                    # Check for missing type hints
                    missing_hints = []
                    if node.args.args:
                        for arg in node.args.args:
                            if arg.arg != 'self' and arg.annotation is None:
                                missing_hints.append(arg.arg)
                    
                    if node.returns is None and node.name not in ['__init__', '__str__', '__repr__']:
                        missing_hints.append('return')
                    
                    if missing_hints and len(node.body) > 3:  # Only flag substantive functions
                        violations.append(Violation(
                            file=filepath,
                            line=node.lineno,
                            severity=Severity.WARNING,
                            category="Coding Standards",
                            message=f"Function '{node.name}' missing type hints for: {', '.join(missing_hints)}",
                            suggestion="Use Python type hints for all function signatures to ensure clarity.",
                            code_snippet=f"def {node.name}(...)"
                        ))
        
        return violations


class DatabaseSecurityChecker(CodeChecker):
    """Validates database security and credential handling."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for f-string SQL queries (injection risk)
            if re.search(r'f["\'].*?(SELECT|INSERT|UPDATE|DELETE|ALTER|DROP|CREATE)', line, re.IGNORECASE):
                violations.append(Violation(
                    file=filepath,
                    line=i,
                    severity=Severity.CRITICAL,
                    category="Database Security",
                    message="SQL query using f-string (injection risk)",
                    suggestion="Use asyncpg parameterization with $1, $2 placeholders. Never use f-strings for SQL queries.",
                    code_snippet=line.strip()
                ))
            
            # Check for .format() in SQL
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE|ALTER|DROP|CREATE).*?\.format\(', line, re.IGNORECASE):
                violations.append(Violation(
                    file=filepath,
                    line=i,
                    severity=Severity.CRITICAL,
                    category="Database Security",
                    message="SQL query using .format() (injection risk)",
                    suggestion="Use asyncpg parameterization with $1, $2 placeholders instead of .format().",
                    code_snippet=line.strip()
                ))
            
            # Check for plain-text password strings
            if re.search(r'password\s*=\s*["\'](?!.*\$\{)(?!.*keyring)', line, re.IGNORECASE):
                if 'keyring' not in lines[max(0, i-3):min(i+3, len(lines))]:
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.CRITICAL,
                        category="Database Security",
                        message="Potential plain-text password assignment",
                        suggestion="Use keyring library for secure credential storage. Never store passwords in plain text.",
                        code_snippet=line.strip()
                    ))
            
            # Check for superuser validation
            if 'connect' in line.lower() and 'asyncpg' in content:
                # Look ahead for superuser check
                next_50_lines = '\n'.join(lines[i:min(i+50, len(lines))])
                if 'superuser' not in next_50_lines.lower() and 'usesuper' not in next_50_lines.lower():
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.WARNING,
                        category="Database Security",
                        message="Database connection without apparent superuser privilege check",
                        suggestion="Every session must begin with a privilege check. If usesuper is false, the app must hard-lock.",
                        code_snippet=line.strip()
                    ))
        
        return violations


class ProductionSafetyChecker(CodeChecker):
    """Validates production safety requirements."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        # Track ALTER SYSTEM commands and their RESET counterparts
        alter_system_lines = []
        reset_lines = []
        
        for i, line in enumerate(lines, 1):
            if 'ALTER SYSTEM SET' in line:
                alter_system_lines.append((i, line))
            if 'ALTER SYSTEM RESET' in line or 'RESET' in line:
                reset_lines.append((i, line))
        
        # Check if ALTER SYSTEM has corresponding RESET logic
        if alter_system_lines and not reset_lines:
            violations.append(Violation(
                file=filepath,
                line=alter_system_lines[0][0],
                severity=Severity.CRITICAL,
                category="Production Safety",
                message="ALTER SYSTEM command without corresponding RESET logic",
                suggestion="Every ALTER SYSTEM command must have a corresponding RESET logic mapped to the Stop button and cleanup.py (Clean Exit Rule).",
                code_snippet=alter_system_lines[0][1].strip()
            ))
        
        # Check for asyncio.Semaphore in network scanning code
        if 'scan' in filepath.lower() or 'discovery' in filepath.lower():
            has_semaphore = any('Semaphore' in line for line in lines)
            has_network_scan = any(re.search(r'(socket|asyncio.*connect|probe)', line) for line in lines)
            
            if has_network_scan and not has_semaphore:
                violations.append(Violation(
                    file=filepath,
                    line=1,
                    severity=Severity.CRITICAL,
                    category="Production Safety",
                    message="Network scanning without asyncio.Semaphore throttling",
                    suggestion="Network scans must use asyncio.Semaphore(20) to avoid socket exhaustion (Resource Throttling).",
                ))
        
        # Check for memory guards on list operations
        for i, line in enumerate(lines, 1):
            # Look for list assignments or append operations
            if re.search(r'query_log|activities|results.*=.*\[', line):
                # Check if there's a length limit mentioned nearby
                surrounding = '\n'.join(lines[max(0, i-5):min(i+10, len(lines))])
                if '1000' not in surrounding and 'slice' not in surrounding.lower() and 'limit' not in surrounding.lower():
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.WARNING,
                        category="Production Safety",
                        message="List operation without apparent memory cap",
                        suggestion="Frontend lists must never exceed 1,000 items; slice data immediately upon ingestion (Memory Guard).",
                        code_snippet=line.strip()
                    ))
        
        return violations


class UILogicChecker(CodeChecker):
    """Validates UI and UX logic requirements."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        # Check for long-running tasks without @rx.background
        for i, line in enumerate(lines, 1):
            # Look for async functions with potential long operations
            if re.match(r'\s*async def', line):
                func_content = []
                for j in range(i, min(i + 30, len(lines))):
                    func_content.append(lines[j])
                    if j > i and lines[j] and not lines[j][0].isspace():
                        break
                
                func_text = '\n'.join(func_content)
                has_long_op = any(keyword in func_text for keyword in ['while', 'asyncio.sleep', 'scan', 'poll', 'stream'])
                has_background = '@rx.background' in lines[max(0, i-3):i]
                
                if has_long_op and not has_background and 'state.py' in filepath:
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.WARNING,
                        category="UI Logic",
                        message="Long-running task without @rx.background decorator",
                        suggestion="Long-running tasks (scanning/polling) must run in @rx.background to keep the interface responsive (Non-Blocking UI).",
                        code_snippet=line.strip()
                    ))
        
        # Check for overlay usage in critical states
        if 'overlay' in filepath.lower() or 'state.py' in filepath:
            has_restart_overlay = any('restart' in line.lower() and 'overlay' in line.lower() for line in lines)
            has_pause_overlay = any('pause' in line.lower() and 'overlay' in line.lower() for line in lines)
            
            if 'restart required' in content.lower() and not has_restart_overlay:
                violations.append(Violation(
                    file=filepath,
                    line=1,
                    severity=Severity.INFO,
                    category="UI Logic",
                    message="Restart required state without overlay implementation",
                    suggestion="System-critical states (Restart required, Inactivity pause) must use full-screen overlays that prevent user bypass (Stateful Overlays).",
                ))
        
        return violations


class ErrorHandlingChecker(CodeChecker):
    """Validates error handling and graceful degradation."""
    
    def check(self, filepath: str, content: str, ast_tree: Optional[ast.AST] = None) -> List[Violation]:
        violations = []
        lines = content.split('\n')
        
        # Check for connection handling without try/except
        for i, line in enumerate(lines, 1):
            if re.search(r'(pool\.acquire|conn\.|connect\()', line):
                # Look for try/except in surrounding context
                preceding = '\n'.join(lines[max(0, i-10):i])
                following = '\n'.join(lines[i:min(i+10, len(lines))])
                
                if 'try:' not in preceding and 'try:' not in following:
                    violations.append(Violation(
                        file=filepath,
                        line=i,
                        severity=Severity.WARNING,
                        category="Error Handling",
                        message="Database operation without apparent error handling",
                        suggestion="If the DB connection drops, the app must show a 'Reconnecting' status rather than crashing (Graceful Degradation).",
                        code_snippet=line.strip()
                    ))
        
        # Check regex parsing for error handling
        if 'log_parser' in filepath or 'parse' in content.lower():
            has_regex = any(re.search(r're\.(match|search|findall|compile)', line) for line in lines)
            has_error_handling = any('except' in line or 'if.*match' in line for line in lines)
            
            if has_regex and not has_error_handling:
                violations.append(Violation(
                    file=filepath,
                    line=1,
                    severity=Severity.WARNING,
                    category="Error Handling",
                    message="Regex parsing without error handling",
                    suggestion="The log parser must handle malformed lines or incomplete multi-line strings without breaking the streaming loop (Regex Robustness).",
                ))
        
        return violations


class CodeReviewAgent:
    """Main code review agent orchestrator."""
    
    def __init__(self, root_dir: str, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize code review agent.
        
        Args:
            root_dir: Root directory to scan
            exclude_patterns: Patterns to exclude from scanning
        """
        self.root_dir = Path(root_dir)
        self.exclude_patterns = exclude_patterns or [
            '__pycache__',
            '.venv',
            'venv',
            '.git',
            'node_modules',
            'build',
            'dist',
            '.pytest_cache'
        ]
        
        self.checkers: List[CodeChecker] = [
            ArchitectureChecker(),
            CodingStandardsChecker(),
            DatabaseSecurityChecker(),
            ProductionSafetyChecker(),
            UILogicChecker(),
            ErrorHandlingChecker()
        ]
    
    def discover_files(self) -> List[Path]:
        """
        Discover all Python files in the project.
        
        Returns:
            List of Python file paths
        """
        python_files = []
        
        for path in self.root_dir.rglob('*.py'):
            # Check if path should be excluded
            if any(pattern in str(path) for pattern in self.exclude_patterns):
                continue
            python_files.append(path)
        
        return sorted(python_files)
    
    def analyze_file(self, filepath: Path) -> List[Violation]:
        """
        Analyze a single file with all checkers.
        
        Args:
            filepath: Path to file to analyze
            
        Returns:
            List of violations found
        """
        violations = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            ast_tree = None
            try:
                ast_tree = ast.parse(content)
            except SyntaxError:
                violations.append(Violation(
                    file=str(filepath),
                    line=1,
                    severity=Severity.CRITICAL,
                    category="Syntax",
                    message="File has syntax errors",
                    suggestion="Fix syntax errors before running code review."
                ))
                return violations
            
            # Run all checkers
            for checker in self.checkers:
                violations.extend(checker.check(str(filepath), content, ast_tree))
        
        except Exception as e:
            violations.append(Violation(
                file=str(filepath),
                line=1,
                severity=Severity.WARNING,
                category="System",
                message=f"Error analyzing file: {e}",
                suggestion="Check file encoding and permissions."
            ))
        
        return violations
    
    def generate_report(self, violations: List[Violation], format: str = 'terminal') -> str:
        """
        Generate formatted report from violations.
        
        Args:
            violations: List of all violations
            format: Output format ('terminal', 'markdown', 'json')
            
        Returns:
            Formatted report string
        """
        if format == 'json':
            return json.dumps([
                {
                    'file': v.file,
                    'line': v.line,
                    'severity': v.severity.value,
                    'category': v.category,
                    'message': v.message,
                    'suggestion': v.suggestion,
                    'code_snippet': v.code_snippet
                }
                for v in violations
            ], indent=2)
        
        # Group violations by file
        by_file: Dict[str, List[Violation]] = {}
        for v in violations:
            if v.file not in by_file:
                by_file[v.file] = []
            by_file[v.file].append(v)
        
        # Count by severity
        severity_counts = {
            Severity.CRITICAL: sum(1 for v in violations if v.severity == Severity.CRITICAL),
            Severity.WARNING: sum(1 for v in violations if v.severity == Severity.WARNING),
            Severity.INFO: sum(1 for v in violations if v.severity == Severity.INFO)
        }
        
        if format == 'markdown':
            return self._generate_markdown_report(by_file, severity_counts)
        else:  # terminal
            return self._generate_terminal_report(by_file, severity_counts)
    
    def _generate_markdown_report(self, by_file: Dict[str, List[Violation]], 
                                  severity_counts: Dict[Severity, int]) -> str:
        """Generate markdown formatted report."""
        lines = [
            "# Code Review Report",
            "",
            "## Summary",
            "",
            f"- **Critical Issues**: {severity_counts[Severity.CRITICAL]}",
            f"- **Warnings**: {severity_counts[Severity.WARNING]}",
            f"- **Info**: {severity_counts[Severity.INFO]}",
            f"- **Total Violations**: {sum(severity_counts.values())}",
            f"- **Files Analyzed**: {len(by_file)}",
            "",
            "---",
            ""
        ]
        
        for filepath in sorted(by_file.keys()):
            file_violations = sorted(by_file[filepath], key=lambda v: (v.severity.value, v.line))
            lines.append(f"## {os.path.basename(filepath)}")
            lines.append(f"*{filepath}*")
            lines.append("")
            
            for v in file_violations:
                severity_emoji = {
                    Severity.CRITICAL: "🔴",
                    Severity.WARNING: "🟡",
                    Severity.INFO: "🔵"
                }
                
                lines.append(f"### {severity_emoji[v.severity]} Line {v.line}: {v.category}")
                lines.append(f"**{v.message}**")
                lines.append("")
                if v.code_snippet:
                    lines.append(f"```python")
                    lines.append(v.code_snippet)
                    lines.append(f"```")
                    lines.append("")
                lines.append(f"💡 *Suggestion*: {v.suggestion}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_terminal_report(self, by_file: Dict[str, List[Violation]], 
                                  severity_counts: Dict[Severity, int]) -> str:
        """Generate terminal formatted report with ANSI colors."""
        # ANSI color codes
        RESET = '\033[0m'
        BOLD = '\033[1m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        
        lines = [
            f"\n{BOLD}{'='*80}{RESET}",
            f"{BOLD}Code Review Report{RESET}",
            f"{BOLD}{'='*80}{RESET}\n",
            f"{BOLD}Summary:{RESET}",
            f"  {RED}Critical Issues: {severity_counts[Severity.CRITICAL]}{RESET}",
            f"  {YELLOW}Warnings: {severity_counts[Severity.WARNING]}{RESET}",
            f"  {BLUE}Info: {severity_counts[Severity.INFO]}{RESET}",
            f"  Total Violations: {sum(severity_counts.values())}",
            f"  Files Analyzed: {len(by_file)}\n"
        ]
        
        for filepath in sorted(by_file.keys()):
            file_violations = sorted(by_file[filepath], key=lambda v: (v.severity.value, v.line))
            
            lines.append(f"{BOLD}{'-'*80}{RESET}")
            lines.append(f"{BOLD}{os.path.basename(filepath)}{RESET}")
            lines.append(f"{filepath}\n")
            
            for v in file_violations:
                severity_color = {
                    Severity.CRITICAL: RED,
                    Severity.WARNING: YELLOW,
                    Severity.INFO: BLUE
                }[v.severity]
                
                lines.append(f"{severity_color}{BOLD}[{v.severity.value}]{RESET} Line {v.line} - {v.category}")
                lines.append(f"  {v.message}")
                if v.code_snippet:
                    lines.append(f"  > {v.code_snippet}")
                lines.append(f"  {GREEN}Suggestion:{RESET} {v.suggestion}\n")
        
        lines.append(f"{BOLD}{'='*80}{RESET}\n")
        
        return '\n'.join(lines)
    
    def run(self, output_format: str = 'terminal') -> str:
        """
        Run full code review analysis.
        
        Args:
            output_format: Output format ('terminal', 'markdown', 'json')
            
        Returns:
            Formatted report
        """
        print(f"Discovering Python files in {self.root_dir}...")
        files = self.discover_files()
        print(f"Found {len(files)} Python files\n")
        
        all_violations = []
        
        for filepath in files:
            print(f"Analyzing {filepath.name}...")
            violations = self.analyze_file(filepath)
            all_violations.extend(violations)
        
        print(f"\nAnalysis complete. Found {len(all_violations)} total violations.\n")
        
        return self.generate_report(all_violations, output_format)


def main():
    """Main entry point for code review agent."""
    parser = argparse.ArgumentParser(
        description='Code Review Agent for PostgreSQL Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with terminal output
  python code_review.py
  
  # Generate markdown report
  python code_review.py --format markdown --output review_report.md
  
  # Generate JSON output
  python code_review.py --format json --output review.json
        """
    )
    
    parser.add_argument(
        '--root',
        default='.',
        help='Root directory to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--format',
        choices=['terminal', 'markdown', 'json'],
        default='terminal',
        help='Output format (default: terminal)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Additional patterns to exclude from scanning'
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = CodeReviewAgent(args.root, args.exclude)
    
    # Run analysis
    report = agent.run(args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport written to {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
