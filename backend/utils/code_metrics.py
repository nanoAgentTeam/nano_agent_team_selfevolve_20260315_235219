"""Code metrics utility for analyzing Python code quality.

Provides functions to analyze code complexity, detect code smells,
and generate comprehensive project health reports.
"""
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


def count_lines(file_path: Path) -> Dict[str, Any]:
    """Count lines in a Python file or directory.
    
    Args:
        file_path: Path to a Python file or directory
        
    Returns:
        Dictionary with total_lines, code_lines, comment_lines, blank_lines,
        and files list (if directory)
    """
    result = {
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "files": []
    }
    
    if file_path.is_dir():
        for py_file in file_path.rglob("*.py"):
            file_result = count_lines(py_file)
            result["total_lines"] += file_result["total_lines"]
            result["code_lines"] += file_result["code_lines"]
            result["comment_lines"] += file_result["comment_lines"]
            result["blank_lines"] += file_result["blank_lines"]
            result["files"].append({
                "path": str(py_file),
                "total_lines": file_result["total_lines"]
            })
        return result
    
    if not file_path.exists():
        return result
    
    content = file_path.read_text()
    lines = content.splitlines()
    
    for line in lines:
        result["total_lines"] += 1
        stripped = line.strip()
        if not stripped:
            result["blank_lines"] += 1
        elif stripped.startswith("#"):
            result["comment_lines"] += 1
        else:
            result["code_lines"] += 1
    
    return result


def count_functions(file_path: Path) -> Dict[str, Any]:
    """Count functions in a Python file.
    
    Args:
        file_path: Path to a Python file
        
    Returns:
        Dictionary with total_functions and list of function names
    """
    result = {
        "total_functions": 0,
        "functions": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result["total_functions"] += 1
                result["functions"].append(node.name)
    except SyntaxError:
        pass
    
    return result


def count_classes(file_path: Path) -> Dict[str, Any]:
    """Count classes in a Python file.
    
    Args:
        file_path: Path to a Python file
        
    Returns:
        Dictionary with total_classes and list of class names
    """
    result = {
        "total_classes": 0,
        "classes": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                result["total_classes"] += 1
                result["classes"].append(node.name)
    except SyntaxError:
        pass
    
    return result


def parse_imports(file_path: Path) -> Dict[str, Any]:
    """Parse import statements in a Python file.
    
    Args:
        file_path: Path to a Python file
        
    Returns:
        Dictionary with modules list
    """
    result = {
        "modules": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["modules"].append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result["modules"].append(node.module.split(".")[0])
    except SyntaxError:
        pass
    
    return result


def detect_long_functions(file_path: Path, max_lines: int = 20) -> Dict[str, Any]:
    """Detect functions that exceed the maximum line threshold.
    
    Args:
        file_path: Path to a Python file
        max_lines: Maximum allowed lines per function
        
    Returns:
        Dictionary with long_functions list containing name and line_count
    """
    result = {
        "long_functions": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length
                if hasattr(node, 'end_lineno'):
                    func_lines = node.end_lineno - node.lineno + 1
                else:
                    # Fallback for older Python versions
                    func_lines = len(ast.unparse(node).splitlines())
                
                if func_lines > max_lines:
                    result["long_functions"].append({
                        "name": node.name,
                        "line_count": func_lines,
                        "start_line": node.lineno
                    })
    except SyntaxError:
        pass
    
    return result


def detect_deep_nesting(file_path: Path, max_depth: int = 3) -> Dict[str, Any]:
    """Detect code with nesting depth exceeding threshold.
    
    Args:
        file_path: Path to a Python file
        max_depth: Maximum allowed nesting depth
        
    Returns:
        Dictionary with deep_nesting list
    """
    result = {
        "deep_nesting": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        def get_max_depth(node, current_depth=0) -> int:
            max_depth_found = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_max_depth(child, current_depth + 1)
                    max_depth_found = max(max_depth_found, child_depth)
                else:
                    child_depth = get_max_depth(child, current_depth)
                    max_depth_found = max(max_depth_found, child_depth)
            return max_depth_found
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                depth = get_max_depth(node)
                if depth > max_depth:
                    result["deep_nesting"].append({
                        "function": node.name,
                        "depth": depth,
                        "line": node.lineno
                    })
    except SyntaxError:
        pass
    
    return result


def detect_too_many_parameters(file_path: Path, max_params: int = 5) -> Dict[str, Any]:
    """Detect functions with too many parameters.
    
    Args:
        file_path: Path to a Python file
        max_params: Maximum allowed parameters
        
    Returns:
        Dictionary with too_many_params list
    """
    result = {
        "too_many_params": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count parameters (excluding self)
                params = [arg.arg for arg in node.args.args if arg.arg != "self"]
                param_count = len(params)
                
                if param_count > max_params:
                    result["too_many_params"].append({
                        "name": node.name,
                        "param_count": param_count,
                        "line": node.lineno
                    })
    except SyntaxError:
        pass
    
    return result


def calculate_complexity_score(file_path: Path) -> Dict[str, Any]:
    """Calculate overall complexity score for a file.
    
    Args:
        file_path: Path to a Python file
        
    Returns:
        Dictionary with score and detailed metrics
    """
    result = {
        "score": 0,
        "metrics": {}
    }
    
    if not file_path.exists():
        return result
    
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        # Count various complexity indicators
        functions = 0
        classes = 0
        ifs = 0
        loops = 0
        returns = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions += 1
            elif isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, ast.If):
                ifs += 1
            elif isinstance(node, (ast.For, ast.While)):
                loops += 1
            elif isinstance(node, ast.Return):
                returns += 1
        
        # Calculate complexity score (lower is better)
        # Simple formula: weighted sum of complexity indicators
        score = (
            functions * 1 +
            classes * 2 +
            ifs * 3 +
            loops * 3 +
            returns * 1
        )
        
        result["score"] = score
        result["metrics"] = {
            "functions": functions,
            "classes": classes,
            "if_statements": ifs,
            "loops": loops,
            "return_statements": returns
        }
    except SyntaxError:
        pass
    
    return result


def analyze_project(project_path: Path) -> Dict[str, Any]:
    """Perform comprehensive analysis of a Python project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary with summary, files analysis, smells, and dependencies
    """
    result = {
        "summary": {},
        "files": [],
        "smells": {
            "long_functions": [],
            "deep_nesting": [],
            "too_many_params": []
        },
        "dependencies": set()
    }
    
    if not project_path.exists():
        result["dependencies"] = list(result["dependencies"])
        return result
    
    all_functions = 0
    all_classes = 0
    total_lines = 0
    code_lines = 0
    
    for py_file in project_path.rglob("*.py"):
        # Skip test files and __pycache__
        if "test_" in py_file.name or "__pycache__" in str(py_file):
            continue
        
        file_analysis = {
            "path": str(py_file),
            "lines": count_lines(py_file),
            "functions": count_functions(py_file),
            "classes": count_classes(py_file),
            "imports": parse_imports(py_file),
            "complexity": calculate_complexity_score(py_file)
        }
        
        result["files"].append(file_analysis)
        
        # Aggregate metrics
        total_lines += file_analysis["lines"]["total_lines"]
        code_lines += file_analysis["lines"]["code_lines"]
        all_functions += file_analysis["functions"]["total_functions"]
        all_classes += file_analysis["classes"]["total_classes"]
        
        # Collect dependencies
        result["dependencies"].update(file_analysis["imports"]["modules"])
        
        # Detect code smells
        long_funcs = detect_long_functions(py_file)
        result["smells"]["long_functions"].extend([
            {**f, "file": str(py_file)} for f in long_funcs["long_functions"]
        ])
        
        deep_nest = detect_deep_nesting(py_file)
        result["smells"]["deep_nesting"].extend([
            {**d, "file": str(py_file)} for d in deep_nest["deep_nesting"]
        ])
        
        too_many = detect_too_many_parameters(py_file)
        result["smells"]["too_many_params"].extend([
            {**t, "file": str(py_file)} for t in too_many["too_many_params"]
        ])
    
    result["summary"] = {
        "total_files": len(result["files"]),
        "total_lines": total_lines,
        "code_lines": code_lines,
        "total_functions": all_functions,
        "total_classes": all_classes,
        "code_health_score": max(0, 100 - len(result["smells"]["long_functions"]) * 5 
                                      - len(result["smells"]["deep_nesting"]) * 5
                                      - len(result["smells"]["too_many_params"]) * 3)
    }
    
    result["dependencies"] = sorted(list(result["dependencies"]))
    
    return result
