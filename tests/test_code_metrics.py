"""Tests for code_metrics utility - TDD approach."""
import pytest
import tempfile
import os
from pathlib import Path


class TestCodeMetrics:
    """Test suite for code_metrics utility following TDD."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary Python project for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_count_lines_single_file(self, temp_project):
        """RED Test 1: Should count lines in a single Python file."""
        # Create a test file
        test_file = temp_project / "test_module.py"
        test_file.write_text("""# Comment line
def hello():
    print("Hello")
    return True

class MyClass:
    pass
""")
        # Import and test - this will fail initially since module doesn't exist
        from backend.utils.code_metrics import count_lines
        result = count_lines(test_file)
        assert result["total_lines"] == 7
        assert result["code_lines"] > 0
        assert result["comment_lines"] >= 1
        assert result["blank_lines"] >= 1

    def test_count_lines_recursive(self, temp_project):
        """RED Test 2: Should count lines recursively in a directory."""
        # Create multiple files
        (temp_project / "main.py").write_text("print('main')\n")
        subdir = temp_project / "subdir"
        subdir.mkdir()
        (subdir / "utils.py").write_text("def util(): pass\n")
        
        from backend.utils.code_metrics import count_lines
        result = count_lines(temp_project)
        assert result["total_lines"] >= 2
        assert len(result["files"]) == 2

    def test_count_functions(self, temp_project):
        """RED Test 3: Should count functions in a Python file."""
        test_file = temp_project / "funcs.py"
        test_file.write_text("""
def func1():
    pass

def func2():
    pass

class MyClass:
    def method1(self):
        pass
""")
        from backend.utils.code_metrics import count_functions
        result = count_functions(test_file)
        assert result["total_functions"] == 3  # func1, func2, method1
        assert "func1" in result["functions"]
        assert "func2" in result["functions"]

    def test_count_classes(self, temp_project):
        """RED Test 4: Should count classes in a Python file."""
        test_file = temp_project / "classes.py"
        test_file.write_text("""
class Class1:
    pass

class Class2:
    pass
""")
        from backend.utils.code_metrics import count_classes
        result = count_classes(test_file)
        assert result["total_classes"] == 2
        assert "Class1" in result["classes"]

    def test_parse_imports(self, temp_project):
        """RED Test 5: Should parse import statements."""
        test_file = temp_project / "imports.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from collections import defaultdict
""")
        from backend.utils.code_metrics import parse_imports
        result = parse_imports(test_file)
        assert "os" in result["modules"]
        assert "sys" in result["modules"]
        assert "pathlib" in result["modules"]
        assert "collections" in result["modules"]

    def test_detect_long_functions(self, temp_project):
        """RED Test 6: Should detect functions exceeding line threshold."""
        test_file = temp_project / "long_func.py"
        # Create a function with many lines
        lines = ["def long_function():\n"]
        for i in range(50):
            lines.append(f"    print({i})\n")
        test_file.write_text("".join(lines))
        
        from backend.utils.code_metrics import detect_long_functions
        result = detect_long_functions(test_file, max_lines=20)
        assert len(result["long_functions"]) == 1
        assert result["long_functions"][0]["name"] == "long_function"

    def test_detect_deep_nesting(self, temp_project):
        """RED Test 7: Should detect deeply nested code."""
        test_file = temp_project / "deep_nest.py"
        test_file.write_text("""
def shallow():
    if True:
        pass

def deep():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        pass
""")
        from backend.utils.code_metrics import detect_deep_nesting
        result = detect_deep_nesting(test_file, max_depth=3)
        assert len(result["deep_nesting"]) >= 1

    def test_detect_too_many_parameters(self, temp_project):
        """RED Test 8: Should detect functions with too many parameters."""
        test_file = temp_project / "many_params.py"
        test_file.write_text("""
def good_func(a, b, c):
    pass

def bad_func(a, b, c, d, e, f, g, h, i, j):
    pass
""")
        from backend.utils.code_metrics import detect_too_many_parameters
        result = detect_too_many_parameters(test_file, max_params=5)
        assert len(result["too_many_params"]) == 1
        assert result["too_many_params"][0]["name"] == "bad_func"

    def test_calculate_complexity_score(self, temp_project):
        """RED Test 9: Should calculate overall complexity score."""
        test_file = temp_project / "complex.py"
        test_file.write_text("""
def simple():
    return 1

def complex_func():
    if True:
        for i in range(10):
            if i > 5:
                print(i)
""")
        from backend.utils.code_metrics import calculate_complexity_score
        result = calculate_complexity_score(test_file)
        assert "score" in result
        assert "metrics" in result

    def test_analyze_project_comprehensive(self, temp_project):
        """RED Test 10: Should provide comprehensive project analysis."""
        # Create a realistic mini-project
        (temp_project / "main.py").write_text("""
import os
from utils import helper

def main():
    helper()

if __name__ == "__main__":
    main()
""")
        subdir = temp_project / "utils"
        subdir.mkdir()
        (subdir / "__init__.py").write_text("")
        (subdir / "helper.py").write_text("""
def helper():
    if True:
        for i in range(10):
            pass
""")
        
        from backend.utils.code_metrics import analyze_project
        result = analyze_project(temp_project)
        assert "summary" in result
        assert "files" in result
        assert "smells" in result
        assert "dependencies" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
