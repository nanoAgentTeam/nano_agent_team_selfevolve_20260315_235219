"""Code Health Analyzer Tool for analyzing Python project health.

This tool provides comprehensive code analysis including metrics,
code smell detection, and dependency analysis.
"""
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from backend.tools.base import BaseTool
from backend.utils.code_metrics import analyze_project


class CodeHealthAnalyzerTool(BaseTool):
    """Tool for analyzing Python project code health and quality."""

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "code_health_analyzer"

    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Analyze Python project code health, metrics, and detect code smells.
        
This tool provides comprehensive analysis including:
- Line counts (total, code, comments, blanks)
- Function and class counts
- Import/dependency analysis
- Code smell detection (long functions, deep nesting, too many parameters)
- Overall complexity scoring
- Health score calculation (0-100)

Use this when you need to understand code quality, identify refactoring opportunities,
or get an overview of a Python project's structure.
"""

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the Python project directory to analyze"
                },
                "max_function_lines": {
                    "type": "integer",
                    "description": "Maximum allowed lines per function (default: 20)",
                    "default": 20
                },
                "max_nesting_depth": {
                    "type": "integer",
                    "description": "Maximum allowed nesting depth (default: 3)",
                    "default": 3
                },
                "max_parameters": {
                    "type": "integer",
                    "description": "Maximum allowed function parameters (default: 5)",
                    "default": 5
                }
            },
            "required": ["project_path"]
        }

    async def execute(
        self,
        session: Any,
        project_path: str,
        max_function_lines: int = 20,
        max_nesting_depth: int = 3,
        max_parameters: int = 5
    ) -> Dict[str, Any]:
        """Execute the code health analysis.
        
        Args:
            session: Agent session object
            project_path: Path to the project directory
            max_function_lines: Threshold for long function detection
            max_nesting_depth: Threshold for deep nesting detection
            max_parameters: Threshold for too many parameters detection
            
        Returns:
            Dictionary with analysis results including:
            - success: bool indicating if analysis succeeded
            - analysis: dict with comprehensive analysis data
            - markdown_output: human-readable markdown report
            - error: error message if success is False
        """
        try:
            path = Path(project_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {project_path}"
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {project_path}"
                }
            
            # Perform analysis
            analysis = analyze_project(path)
            
            # Generate markdown report
            markdown_output = self._generate_markdown_report(analysis)
            
            return {
                "success": True,
                "analysis": analysis,
                "markdown_output": markdown_output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }

    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a markdown-formatted report from analysis results.
        
        Args:
            analysis: Analysis dictionary from analyze_project()
            
        Returns:
            Markdown-formatted string report
        """
        summary = analysis.get("summary", {})
        smells = analysis.get("smells", {})
        
        report = ["# Code Health Analysis Report\n"]
        
        # Summary section
        report.append("## Summary\n")
        report.append(f"- **Total Files**: {summary.get('total_files', 0)}")
        report.append(f"- **Total Lines**: {summary.get('total_lines', 0)}")
        report.append(f"- **Code Lines**: {summary.get('code_lines', 0)}")
        report.append(f"- **Total Functions**: {summary.get('total_functions', 0)}")
        report.append(f"- **Total Classes**: {summary.get('total_classes', 0)}")
        report.append(f"- **Health Score**: {summary.get('code_health_score', 0)}/100\n")
        
        # Dependencies section
        deps = analysis.get("dependencies", [])
        if deps:
            report.append("## Dependencies\n")
            for dep in deps:
                report.append(f"- `{dep}`")
            report.append("")
        
        # Code Smells section
        report.append("## Code Smells\n")
        
        long_funcs = smells.get("long_functions", [])
        if long_funcs:
            report.append("### Long Functions\n")
            for func in long_funcs[:10]:  # Limit to top 10
                report.append(f"- `{func['file']}:{func['start_line']}` - "
                            f"`{func['name']}` ({func['line_count']} lines)")
            if len(long_funcs) > 10:
                report.append(f"- ... and {len(long_funcs) - 10} more")
            report.append("")
        
        deep_nesting = smells.get("deep_nesting", [])
        if deep_nesting:
            report.append("### Deep Nesting\n")
            for nest in deep_nesting[:10]:
                report.append(f"- `{nest['file']}:{nest['line']}` - "
                            f"`{nest['function']}` (depth: {nest['depth']})")
            if len(deep_nesting) > 10:
                report.append(f"- ... and {len(deep_nesting) - 10} more")
            report.append("")
        
        too_many_params = smells.get("too_many_params", [])
        if too_many_params:
            report.append("### Too Many Parameters\n")
            for param in too_many_params[:10]:
                report.append(f"- `{param['file']}:{param['line']}` - "
                            f"`{param['name']}` ({param['param_count']} params)")
            if len(too_many_params) > 10:
                report.append(f"- ... and {len(too_many_params) - 10} more")
            report.append("")
        
        if not long_funcs and not deep_nesting and not too_many_params:
            report.append("No code smells detected! 🎉\n")
        
        # File details section
        files = analysis.get("files", [])
        if files:
            report.append("## File Details\n")
            for file_info in files[:20]:  # Limit to first 20 files
                path = file_info.get("path", "unknown")
                lines = file_info.get("lines", {})
                complexity = file_info.get("complexity", {})
                report.append(f"### `{path}`")
                report.append(f"- Lines: {lines.get('total_lines', 0)} "
                            f"(code: {lines.get('code_lines', 0)})")
                report.append(f"- Functions: {file_info.get('functions', {}).get('total_functions', 0)}")
                report.append(f"- Classes: {file_info.get('classes', {}).get('total_classes', 0)}")
                report.append(f"- Complexity Score: {complexity.get('score', 0)}\n")
            
            if len(files) > 20:
                report.append(f"... and {len(files) - 20} more files\n")
        
        return "\n".join(report)
