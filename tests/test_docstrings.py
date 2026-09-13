"""Structural checks for the documented broker API surface."""

import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[1] / "src" / "scm_broker_mcp"
RELEVANT_MODULES = ("auth.py", "errors.py", "models.py", "providers.py", "service.py", "main.py")
IMPORTANT_PRIVATE_HELPERS = {"_url", "_headers", "_run"}


def _documented_nodes(path: Path) -> list[ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return module, class, and function nodes in a source file."""
    tree = ast.parse(path.read_text())
    nodes: list[ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef] = [tree]
    nodes.extend(node for node in ast.walk(tree) if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)))
    return nodes


def _has_shape_detail(docstring: str) -> bool:
    """Identify input/output shape language in a docstring example."""
    example = docstring[docstring.index("Examples:") :]
    return "Input:" in example and "Output:" in example


def test_relevant_modules_have_google_style_module_docstrings():
    """Require module-level documentation and representative examples."""
    for module_name in RELEVANT_MODULES:
        module_doc = ast.get_docstring(ast.parse((SOURCE_ROOT / module_name).read_text()))
        assert module_doc, module_name
        assert "Examples:" in module_doc, module_name


def test_public_api_and_important_helpers_have_google_docstrings():
    """Require Args/Returns and shape-bearing Examples on API nodes."""
    missing: list[str] = []
    for module_name in RELEVANT_MODULES:
        for node in _documented_nodes(SOURCE_ROOT / module_name)[1:]:
            name = getattr(node, "name", "")
            if name.startswith("_") and name not in IMPORTANT_PRIVATE_HELPERS:
                continue
            docstring = ast.get_docstring(node)
            if not docstring or "Examples:" not in docstring or not _has_shape_detail(docstring):
                missing.append(f"{module_name}:{name}")
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and name not in {"__repr__", "__init__"}:
                has_arguments = any(arg.arg != "self" for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)) or node.args.vararg or node.args.kwarg
                if "Returns:" not in docstring or (has_arguments and "Args:" not in docstring):
                    missing.append(f"{module_name}:{name} (Args/Returns)")
    assert not missing, "Missing Google-style docstrings: " + ", ".join(missing)
