import glob
import json
import os
from collections import defaultdict
from pathlib import Path

from luaparser import ast
from luaparser.astnodes import (
    Assign,
    Block,
    Chunk,
    Concat,
    ElseIf,
    Function,
    If,
    Invoke,
    Name,
    Node,
    Number,
    String,
)

from ..utils.logger import config_logger

LOGGER = config_logger(__name__)


class LuaInterpreter:

    # Nome do 1o parâmetro de AddInstructions -> tipo de instrução gerado
    TARGET_PREFIXES = {
        "PointInstruction": "symbol",
        "LocalOffset": "text",
        "AreaFillReference": "area_fill",
        "ColorFill": "color_fill",
        "LineInstruction": "line_instruction",
    }

    # Prefixo usado internamente para marcar condições negadas
    # (ramo "NOT (...)" de um if/elseif não satisfeito). Essas condições
    # nunca aparecem no resultado final, servem só para resolver o valor
    # correto de variáveis.
    NEGATION_PREFIX = "NOT ("

    def __init__(self, path: str):
        self.files = glob.glob(path)
        self.local_var = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_json_analyses(self, output_dir: str = "./data/rules_parsed"):
        LOGGER.info(f"{'#' * 30} GETTING RULES DATA {'#' * 30}")
        symbol_rules = defaultdict(set)

        for file in self.files:
            base_name, root_nodes, conditions = self._process_file(file)
            LOGGER.info(f"PROCESSING {base_name}.lua")

            file_output_dir = Path(output_dir) / base_name
            os.makedirs(file_output_dir, exist_ok=True)

            self._write_json(file_output_dir / f"{base_name}.json", root_nodes)
            self._write_json(
                file_output_dir / f"{base_name}-conditions.json", conditions
            )

            self._collect_symbol_rules(conditions, base_name, symbol_rules)

        self._write_symbol_rules_map(symbol_rules)

        LOGGER.info(
            f"{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM RULES FILE "
            f"WAS COMPLETED {'*' * 10}"
        )

    def get_symbol_rules_map(self) -> dict:
        """Processa todos os arquivos e retorna {simbolo: [rule, ...]},
        sem gravar nada em disco."""
        symbol_rules = defaultdict(set)

        for file in self.files:
            base_name, _, conditions = self._process_file(file)
            self._collect_symbol_rules(conditions, base_name, symbol_rules)

        return self._sorted_symbol_rules(symbol_rules)

    # ------------------------------------------------------------------
    # Processamento de arquivo (compartilhado pelos dois métodos acima)
    # ------------------------------------------------------------------

    def _process_file(self, file: str):
        """Faz o parsing de um arquivo .lua e devolve
        (nome_base, arvore_json, conditions).

        IMPORTANTE: reseta `self.local_var` a cada arquivo. Sem isso,
        variáveis de um arquivo continuariam "visíveis" ao processar o
        próximo arquivo da lista.
        """
        self.local_var = []

        path = Path(file)
        tree = self.get_lua_code(path)
        root_nodes = self.build_tree(tree)
        conditions = self.map_conditions(root_nodes)

        return path.stem, root_nodes, conditions

    def _write_json(self, path, data) -> None:
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)

    # ------------------------------------------------------------------
    # Mapa {simbolo: [regras]}
    # ------------------------------------------------------------------

    def _collect_symbol_rules(
        self, conditions: list, rule_name: str, symbol_rules: dict
    ) -> None:
        for item in conditions:
            if (
                item.get("node_type") != "hit"
                or item.get("instruction_type") != "symbol"
            ):
                continue

            values = item.get("values") or {}
            symbol_value = values.get("PointInstruction")

            for symbol in self._flatten_symbol_values(symbol_value):
                symbol_rules[symbol].add(rule_name)

    def _flatten_symbol_values(self, value) -> list:
        """Normaliza o valor (já resolvido) de um símbolo numa lista
        simples de nomes, cobrindo os 3 formatos possíveis: valor fixo
        (str), lista de possibilidades ({'value':..., 'conditions':...})
        ou algo inesperado (ignorado)."""
        if isinstance(value, str):
            return [value]

        if isinstance(value, list):
            symbols = []
            for item in value:
                if isinstance(item, dict) and "value" in item:
                    symbols.extend(self._flatten_symbol_values(item["value"]))
                else:
                    symbols.extend(self._flatten_symbol_values(item))
            return symbols

        return []

    def _sorted_symbol_rules(self, symbol_rules: dict) -> dict:
        return {
            symbol: {"rules": sorted(rules)}
            for symbol, rules in sorted(symbol_rules.items())
        }

    def _write_symbol_rules_map(self, symbol_rules: dict) -> None:
        self._write_json(
            Path("data") / "symbol_related.json",
            self._sorted_symbol_rules(symbol_rules),
        )

    # ==================================================================
    # PARTE 1 — Parsing: AST do luaparser -> árvore de dicts (JSON)
    # ==================================================================

    def get_lua_code(self, file: str) -> Chunk:
        with open(file, "r", encoding="utf-8") as fp:
            source = fp.read()
        return ast.parse(source)

    def get_line_code(self, node: Node):
        token = getattr(node, "first_token", None)
        if token is not None:
            return token.line
        return getattr(node, "line", None)

    def get_parameters(self, node: Node) -> str | int | None:
        if isinstance(node, String):
            return node.raw

        if isinstance(node, Name):
            return node.id

        if isinstance(node, Concat):
            return f"{self.get_parameters(node.left)}{self.get_parameters(node.right)}"

        if isinstance(node, Number):
            return node.n

        return None

    def build_tree(self, tree: Chunk) -> list:
        if tree is None:
            return []

        if isinstance(tree, Chunk):
            return self.build_tree(tree.body)

        if isinstance(tree, Block):
            return self.build_tree_body(tree.body)

        return self.build_node(tree)

    def build_tree_body(self, parent_node: Node) -> list:
        if not parent_node:
            return []

        nodes = []
        for node in parent_node:
            nodes.extend(self.build_node(node))
        return nodes

    def build_node(self, node: Node) -> list:
        if node is None:
            return []

        node_info = self.get_info_node(node)
        if node_info:
            return [self._build_hit_node(node, node_info)]

        if isinstance(node, If):
            return self.build_if_chain(node)

        if isinstance(node, Function):
            return [
                {
                    "node_type": "function",
                    "name": ast.to_lua_source(node.name) if node.name else "Unknown",
                    "line": self.get_line_code(node),
                    "children": self.build_tree(node.body),
                }
            ]

        if isinstance(node, Block):
            return self.build_tree_body(node.body)

        if isinstance(node, Assign):
            return [self._build_var_node(node)]

        return []

    def _build_hit_node(self, node: Node, node_info: dict) -> dict:
        node_dt = {
            "node_type": "hit",
            "line": self.get_line_code(node),
            "code": ast.to_lua_source(node),
        } | node_info

        # LocalOffset chega como "x,y" numa única string; separamos em
        # dois campos para facilitar o consumo depois.
        if node_dt["instruction_type"] == "text":
            x, y = node_dt["values"]["LocalOffset"].split(",")
            node_dt["values"]["LocalOffset"] = {"x": x.strip(), "y": y.strip()}

        return node_dt

    def _build_var_node(self, node: Assign) -> dict:
        value = self._assign_value(node)
        name = self._assign_target_name(node)

        self.local_var.append({"name": name, "value": value})

        return {
            "node_type": "var",
            "name": name,
            "instruction_type": node.display_name,
            "line": self.get_line_code(node),
            "code": ast.to_lua_source(node),
            "value": value,
        }

    def _assign_target_name(self, node: Assign):
        """O alvo de um Assign é normalmente um Name (node.targets[0].id),
        mas pode ser um acesso indexado (ex.: tabela), onde o nome fica em
        node.targets[0].idx.id."""
        target = node.targets[0]
        return getattr(target, "id", None) or getattr(
            getattr(target, "idx", None), "id", None
        )

    def _assign_value(self, node: Assign):
        """Extrai o valor literal atribuído (número, string ou tabela).
        Para qualquer outra coisa (ex.: chamada de função, variável),
        mantém o valor padrão 1 (ou -1 se precedido de unário '-')."""
        value = 1
        var_val = node.values[0] if node.values else None
        if var_val is None:
            return value

        if var_val.display_name == "UMinusOp":
            var_val = var_val.operand
            value *= -1

        if var_val.display_name == "Number":
            value *= var_val.n
        elif var_val.display_name == "String":
            value = var_val.raw
        elif var_val.display_name == "Table":
            value = {}

        return value

    def get_info_node(self, node: Node):
        if not isinstance(node, Invoke):
            return None

        func_name = node.func.id if isinstance(node.func, Name) else None

        if func_name == "AddInstructions":
            return self._info_add_instructions(node)

        if func_name == "SimpleLineStyle":
            return self._info_simple_line_style(node)

        return None

    def _info_add_instructions(self, node: Invoke):
        all_params = self.get_parameters(node.args[0])
        if not all_params:
            return None

        params = {}
        has_var = False
        for param in all_params.split(";"):
            if ":" not in param:
                continue

            key, value = (p.strip() for p in param.split(":", 1))
            params[key] = value
            has_var = has_var or self._references_local_var(value)

        first_param = next(iter(params), None)
        if first_param not in self.TARGET_PREFIXES:
            return None

        return {
            "instruction_type": self.TARGET_PREFIXES[first_param],
            "values": params,
            "has_var": has_var,
        }

    def _info_simple_line_style(self, node: Invoke):
        style, thickness, color = (self.get_parameters(arg) for arg in node.args)
        has_var = any(self._references_local_var(v) for v in (style, thickness, color))

        return {
            "instruction_type": "line_style",
            "values": {"style": style, "thickness": thickness, "color": color},
            "has_var": has_var,
        }

    def _references_local_var(self, value) -> bool:
        return any(var["name"] in str(value) for var in self.local_var)

    def build_if_chain(self, node: If | ElseIf | Block, branch_type: str = "if"):
        branch_info = {
            "node_type": branch_type,
            "condition": ast.to_lua_source(node.test),
            "line": self.get_line_code(node),
            "children": self.build_tree(node.body),
        }
        chain = [branch_info]

        orelse = node.orelse
        if orelse is None:
            return chain

        if isinstance(orelse, ElseIf):
            chain.extend(self.build_if_chain(orelse, branch_type="elseif"))
        elif isinstance(orelse, Block):
            chain.append(
                {
                    "node_type": "else",
                    "line": self.get_line_code(orelse),
                    "children": self.build_tree_body(orelse.body),
                }
            )

        return chain

    # ==================================================================
    # PARTE 2 — Resolução de condições e variáveis (reaching definitions)
    # ==================================================================
    #
    # Ideia geral: percorremos a árvore em ordem de execução mantendo um
    # `var_state` = {nome_var: [(valor, condicoes), ...]}, isto é, todos
    # os valores possíveis de cada variável até este ponto e sob quais
    # condições cada um se aplica. Ao entrar num ramo if/elseif/else,
    # acumulamos a condição do ramo (ou a negação dos ramos anteriores)
    # no caminho. Ao sair do bloco, juntamos (merge) o var_state de todos
    # os ramos possíveis. Cada "hit" é então resolvido usando o
    # var_state vigente no ponto em que ele aparece.

    def map_conditions(self, nodes: list, base_path: list = None, obj: list = None):
        if base_path is None:
            base_path = []
        if obj is None:
            obj = []

        self._walk(nodes, base_path, {}, obj)
        return obj

    def _walk(self, nodes: list, base_path: list, var_state: dict, obj: list) -> dict:
        i, n = 0, len(nodes)

        while i < n:
            node = nodes[i]
            node_type = node.get("node_type")

            if node_type == "var":
                var_state = self._handle_var_node(node, base_path, var_state)
                i += 1
                continue

            if node_type == "hit":
                obj.append(self._resolve_hit(node, var_state, base_path))
                i += 1
                continue

            if node_type == "if":
                # agrupa a cadeia if/elseif*/else? (irmãos consecutivos)
                chain = [node]
                j = i + 1
                while j < n and nodes[j].get("node_type") in ("elseif", "else"):
                    chain.append(nodes[j])
                    j += 1

                var_state = self._process_if_chain(chain, base_path, var_state, obj)
                i = j
                continue

            # nós sem tratamento explícito (ex.: 'function') -> desce nos
            # filhos mantendo o mesmo caminho de condições
            children = node.get("children")
            if children:
                var_state = self._walk(children, base_path, var_state, obj)
            i += 1

        return var_state

    def _handle_var_node(self, node: dict, base_path: list, var_state: dict) -> dict:
        """Registra uma atribuição de variável no estado corrente."""
        name = node.get("name")
        if name is None:
            return var_state
        return {**var_state, name: [(node.get("value"), list(base_path))]}

    def _process_if_chain(
        self, chain: list, base_path: list, var_state_in: dict, obj: list
    ) -> dict:
        """Percorre um bloco if/elseif*/else e devolve o var_state
        resultante da junção de todos os ramos possíveis."""
        branch_results, has_else = self._collect_branch_results(
            chain, base_path, var_state_in, obj
        )

        if not has_else:
            # nenhuma das condições do bloco foi satisfeita
            none_path = base_path + self._all_negations(chain)
            branch_results.append((none_path, dict(var_state_in)))

        return self._merge_branch_states(chain, var_state_in, branch_results)

    def _collect_branch_results(
        self, chain: list, base_path: list, var_state_in: dict, obj: list
    ):
        """Percorre cada ramo da cadeia if/elseif/else, acumulando a
        negação dos ramos anteriores no caminho de condições de cada um."""
        branch_results = []
        prior_negations = []
        has_else = False

        for branch in chain:
            b_type = branch.get("node_type")
            condition = branch.get("condition")
            children = branch.get("children") or []

            if b_type == "else":
                has_else = True
                branch_path = base_path + prior_negations
            else:
                branch_path = base_path + prior_negations + [condition]

            branch_state = self._walk(children, branch_path, dict(var_state_in), obj)
            branch_results.append((branch_path, branch_state))

            if b_type != "else" and condition is not None:
                prior_negations = prior_negations + [self._negate(condition)]

        return branch_results, has_else

    def _all_negations(self, chain: list) -> list:
        """Reconstrói a lista de negações de todas as condições if/elseif
        da cadeia (usada para o caminho 'nenhum ramo satisfeito')."""
        return [
            self._negate(branch["condition"])
            for branch in chain
            if branch.get("node_type") != "else" and branch.get("condition") is not None
        ]

    def _negate(self, condition: str) -> str:
        return f"{self.NEGATION_PREFIX}{condition})"

    def _merge_branch_states(
        self, chain: list, var_state_in: dict, branch_results: list
    ) -> dict:
        """Junta o var_state de cada ramo possível: para cada variável
        alterada em algum ramo, mantém todas as suas possibilidades de
        valor com o caminho de condições combinado."""
        changed_vars = set()
        for branch in chain:
            changed_vars |= self._collect_assigned_names(branch.get("children") or [])

        merged = dict(var_state_in)
        for name in changed_vars:
            entries = [
                (value, self._dedup(branch_path + path))
                for branch_path, state in branch_results
                for value, path in state.get(name, [])
            ]
            merged[name] = self._dedup_entries(entries)

        return merged

    def _resolve_hit(self, node: dict, var_state: dict, base_path: list) -> dict:
        resolved = {**node, "conditions": self._visible_conditions(base_path)}

        if not node.get("has_var"):
            return resolved

        values = node.get("values") or {}
        resolved["values"] = self._resolve_value(values, var_state, base_path)
        return resolved

    def _resolve_value(self, val, var_state: dict, base_path: list):
        if isinstance(val, dict):
            return {
                k: self._resolve_value(v, var_state, base_path) for k, v in val.items()
            }

        if not isinstance(val, str):
            return val

        # val É o nome de uma variável conhecida
        if val in var_state:
            return self._value_from_entries(var_state[val], base_path)

        # val CONTÉM o nome de uma variável conhecida (ex.: interpolação)
        for key, entries in var_state.items():
            if key in val:
                substituted = [(val.replace(key, str(v)), path) for v, path in entries]
                return self._value_from_entries(substituted, base_path)

        return val

    def _value_from_entries(self, entries, base_path: list):
        """Combina `base_path` com o caminho de cada entrada (valor,
        condições), remove as condições negativas e des-duplica. Se
        sobrar só um valor possível e sem condição alguma, retorna o
        valor puro; senão, a lista de possibilidades {value, conditions}."""
        combined = [
            (value, self._dedup(list(base_path) + list(path)))
            for value, path in entries
        ]
        visible = self._dedup_entries(
            (value, self._visible_conditions(path)) for value, path in combined
        )

        if len(visible) == 1 and not visible[0][1]:
            return visible[0][0]

        return [{"value": v, "conditions": c} for v, c in visible]

    def _visible_conditions(self, conditions: list) -> list:
        """Remove as condições negativas (ramos 'NOT (...)') antes de
        expor um caminho de condições no resultado final."""
        return [c for c in conditions if not str(c).startswith(self.NEGATION_PREFIX)]

    def _collect_assigned_names(self, nodes: list) -> set:
        names = set()
        for node in nodes:
            if node.get("node_type") == "var" and node.get("name"):
                names.add(node["name"])
            children = node.get("children")
            if children:
                names |= self._collect_assigned_names(children)
        return names

    def _dedup(self, path: list) -> list:
        return list(dict.fromkeys(path))

    def _dedup_entries(self, entries) -> list:
        seen = set()
        result = []
        for value, path in entries:
            key_value = (
                value
                if isinstance(value, (str, int, float, bool, type(None)))
                else json.dumps(value, sort_keys=True)
            )
            key = (key_value, tuple(path))
            if key not in seen:
                seen.add(key)
                result.append((value, path))
        return result
