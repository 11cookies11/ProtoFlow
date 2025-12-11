from __future__ import annotations

from pathlib import Path
from typing import List

from dsl.ast_nodes import ChartSpec, ScriptAST, UIConfig
from dsl.parser import parse_script


def charts_from_ast(ast: ScriptAST) -> List[ChartSpec]:
    ui_cfg: UIConfig = ast.ui if ast.ui else UIConfig()
    return list(ui_cfg.charts)


def charts_from_yaml(path: str | Path) -> List[ChartSpec]:
    ast = parse_script(str(path))
    return charts_from_ast(ast)
