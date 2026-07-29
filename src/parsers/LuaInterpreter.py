import json
import os
from collections import defaultdict

from pathlib import Path
from luaparser import ast
from luaparser.astnodes import (
    Node,
    Chunk,
    Block,
    Invoke,
    Name,
    String,
    Concat,
    If,
    ElseIf,
    Function,
    Assign,
    Number,
)
import glob

from ..utils.logger import config_logger

LOGGER = config_logger(__name__)


class LuaInterpreter:

    TARGET_PREFIXES = {
        "PointInstruction": "symbol",
        "LocalOffset": "text",
        "AreaFillReference": "area_fill",
        "ColorFill": "color_fill",
        "LineInstruction": "line_instruction",
    }

    def __init__(self, path: str):
        self.files = glob.glob(path)
        self.local_var = []

    def get_json_analyses(self, output_dir: str = "./data/rules_parsed"):
        LOGGER.info(f'{'#' * 30} GETTING RULES DATA {'#' * 30}')
        symbol_rules = defaultdict(set)

        for file in self.files:
            
            file = Path(file)
            
            tree = self.get_lua_code(file)
            root_nodes = self.build_tree(tree)

            base_name = file.stem
            file_output_dir = Path(f'{output_dir}/{base_name}')
            os.makedirs(file_output_dir, exist_ok=True)

            LOGGER.info(f'PROCESSING {file.name}')
            

            json_file = os.path.join(file_output_dir, f"{base_name}.json")
            conditions_file = os.path.join(
                file_output_dir, f"{base_name}-conditions.json"
            )

            conditions = self.map_conditions(root_nodes)

            with open(json_file, "w") as fp:
                json.dump(root_nodes, fp, indent=2)

            with open(conditions_file, "w") as fp:
                json.dump(conditions, fp, indent=2)

            self._collect_symbol_rules(conditions, base_name, symbol_rules)

        self._write_symbol_rules_map(symbol_rules, output_dir)
        
        LOGGER.info(f'{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM RULES FILE WAS COMPLETED {'*' * 10}')

    NEGATION_PREFIX = "NOT ("

    def map_conditions(self, nodes: list, base_path: list = None, obj: list = None):
        """
        Percorre a árvore em ordem de execução, mantendo o estado de cada
        variável (valores possíveis + condições cumulativas, já com a
        negação dos ramos não tomados). Para cada 'hit' com has_var=True,
        resolve os valores possíveis em 'resolved_values'.

        As condições negativas (ramos "NOT (...)") existem apenas
        internamente para resolver o valor correto das variáveis; elas
        não aparecem nas 'conditions' do resultado final.
        """
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
                var_state = self._handle_var_node(node, base_path, var_state, obj)
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

    def _handle_var_node(
        self, node: dict, base_path: list, var_state: dict, obj: list
    ) -> dict:
        """Registra uma atribuição de variável no estado corrente e no
        output (com as condições já filtradas para exibição)."""
        name = node.get("name")
        if name is not None:
            var_state = {**var_state, name: [(node.get("value"), list(base_path))]}

        # obj.append({**node, 'conditions': self._visible_conditions(base_path)})
        return var_state

    def _process_if_chain(
        self, chain: list, base_path: list, var_state_in: dict, obj: list
    ) -> dict:
        """Percorre um bloco if/elseif*/else, retornando o var_state
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
        """Percorre cada ramo da cadeia if/elseif/else, acumulando as
        negações dos ramos anteriores no caminho de condições de cada um."""
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
        negations = []
        for branch in chain:
            condition = branch.get("condition")
            if branch.get("node_type") != "else" and condition is not None:
                negations.append(self._negate(condition))
        return negations

    def _negate(self, condition: str) -> str:
        return f"{self.NEGATION_PREFIX}{condition})"

    def _merge_branch_states(
        self, chain: list, var_state_in: dict, branch_results: list
    ) -> dict:
        """Junta o var_state de cada ramo possível, mantendo, para cada
        variável alterada em algum ramo, todas as suas possibilidades de
        valor com o caminho de condições combinado."""
        changed_vars = set()
        for branch in chain:
            changed_vars |= self._collect_assigned_names(branch.get("children") or [])

        merged = dict(var_state_in)

        for name in changed_vars:
            merged_entries = []
            for branch_path, state in branch_results:
                for value, path in state.get(name, []):
                    merged_entries.append((value, self._dedup(branch_path + path)))
            merged[name] = self._dedup_entries(merged_entries)

        return merged

    def _resolve_hit(self, node: dict, var_state: dict, base_path: list) -> dict:
        resolved = {**node, "conditions": self._visible_conditions(base_path)}

        if not node.get("has_var"):
            return resolved

        values = node.get("values") or {}
        resolved["values"] = self._resolve_value(values, var_state, base_path)
        return resolved

    def _resolve_value(self, val, var_state: dict, base_path: list):
        # string que é o nome de uma variável conhecida -> vira a lista de
        # possibilidades {value, conditions}
        if isinstance(val, str):
            if val in var_state:
                resolved = [
                    (v, self._dedup(list(base_path) + list(path)))
                    for v, path in var_state[val]
                ]
                # remove as negações antes de expor e des-duplica, já que
                # dois caminhos podem ter diferido só por condições NOT
                visible = self._dedup_entries(
                    (v, self._visible_conditions(c)) for v, c in resolved
                )

                # só uma possibilidade e sem nenhuma condição combinada ->
                # não precisa de lista, o valor é sempre esse mesmo aqui
                if len(visible) == 1 and not visible[0][1]:
                    return visible[0][0]
                return [{"value": v, "conditions": c} for v, c in visible]

            for key in var_state:
                if key in val:

                    resolved = [
                        (val.replace(key, v), self._dedup(list(base_path) + list(path)))
                        for v, path in var_state[key]
                    ]

                    visible = self._dedup_entries(
                        (v, self._visible_conditions(c)) for v, c in resolved
                    )

                    if len(visible) == 1 and not visible[0][1]:
                        return visible[0][0]

                    return [{"value": v, "conditions": c} for v, c in visible]
            return val

        # dict aninhado (ex.: LocalOffset -> {'x': 'textOffsetX', 'y': 'textOffsetY'})
        # -> resolve cada valor recursivamente
        if isinstance(val, dict):
            return {
                k: self._resolve_value(v, var_state, base_path) for k, v in val.items()
            }

        return val

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

    def get_symbol_rules_map(self) -> dict:
        """Processa todas as rules do path informado no construtor e
        retorna um dict {simbolo: [rule, rule, ...]}, sem gravar nada em
        disco. Útil para reutilizar a lógica fora de `get_json_analyses`."""
        symbol_rules = defaultdict(set)

        for file in self.files:
            tree = self.get_lua_code(file)
            root_nodes = self.build_tree(tree)
            base_name = os.path.splitext(os.path.basename(file))[0]

            conditions = self.map_conditions(root_nodes)
            self._collect_symbol_rules(conditions, base_name, symbol_rules)

        return self._sorted_symbol_rules(symbol_rules)

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
        """Normaliza o valor de um símbolo (já resolvido por
        `_resolve_value`) numa lista simples de nomes de símbolo,
        cobrindo os três formatos possíveis: valor fixo (str), lista de
        possibilidades ({'value': ..., 'conditions': [...]}), ou algo
        inesperado (ignorado)."""
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
        return {symbol: sorted(rules) for symbol, rules in sorted(symbol_rules.items())}

    def _write_symbol_rules_map(self, symbol_rules: dict, output_dir: str) -> None:
        output_file = os.path.join(output_dir, "symbol_rules.json")
        with open(output_file, "w") as fp:
            json.dump(self._sorted_symbol_rules(symbol_rules), fp, indent=2)

    # ------------------------------------------------------------------------

    def get_lua_code(self, file: str) -> Chunk:
        with open(file, "r", encoding="utf-8") as fp:
            source = fp.read()

        return ast.parse(source)

    def get_line_code(self, node: Node):
        try:
            return node.first_token.line

        except AttributeError:
            try:
                return node.line

            except AttributeError:
                return None

    def get_parameters(self, node: Node) -> dict[str, str | int]:
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

    def build_tree_body(self, parent_node: Node):
        nodes_childrens = []

        if not parent_node:
            return nodes_childrens

        for node in parent_node:
            nodes_childrens.extend(self.build_node(node))

        return nodes_childrens

    def build_node(self, node: Node):
        if node is None:
            return []

        node_info = self.get_info_node(node)
        if node_info:

            node_dt = {
                "node_type": "hit",
                "line": self.get_line_code(node),
                "code": ast.to_lua_source(node),
            } | node_info

            if node_dt["instruction_type"] == "text":
                node_dt["values"]["LocalOffset"] = {
                    "x": node_dt["values"]["LocalOffset"].split(",")[0],
                    "y": node_dt["values"]["LocalOffset"].split(",")[1],
                }

            return [node_dt]

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
            var_val = node.values[0] if len(node.values) > 0 else None
            value = 1

            if var_val is not None:
                if var_val.display_name == "UMinusOp":
                    var_val = var_val.operand
                    value *= -1

                if var_val.display_name == "Number":
                    value *= var_val.n

                if var_val.display_name == "String":
                    value = var_val.raw

                if var_val.display_name == "Table":
                    value = {}

            try:
                self.local_var.append({"name": node.targets[0].id, "value": value})
                return [
                    {
                        "node_type": "var",
                        "name": node.targets[0].id,
                        "instruction_type": node.display_name,
                        "line": self.get_line_code(node),
                        "code": ast.to_lua_source(node),
                        "value": value,
                    }
                ]

            except:
                self.local_var.append({"name": node.targets[0].idx.id, "value": value})
                return [
                    {
                        "node_type": "var",
                        "name": node.targets[0].idx.id,
                        "instruction_type": node.display_name,
                        "line": self.get_line_code(node),
                        "code": ast.to_lua_source(node),
                        "value": value,
                    }
                ]
        return []

    # ------------------------------------------------------------------------

    def get_info_node(self, node: Node):
        if isinstance(node, Invoke):
            func_name = node.func.id if isinstance(node.func, Name) else None
            has_var = False

            if func_name == "AddInstructions":
                all_params = self.get_parameters(node.args[0])
                if all_params:

                    params = {}

                    for param in all_params.split(";"):
                        if ":" in param:
                            key = param.split(":")[0].strip()
                            value = param.split(":")[1].strip()

                            for var in self.local_var:
                                if var["name"] in value:
                                    has_var = True
                                    break

                            params = params | {key: value}

                    first_param = list(params.keys())[0] if len(params) > 0 else None

                    if first_param in list(self.TARGET_PREFIXES.keys()):
                        return {
                            "instruction_type": self.TARGET_PREFIXES[first_param],
                            "values": {**params},
                            "has_var": has_var,
                        }

            elif func_name == "SimpleLineStyle":
                all_params = [self.get_parameters(param) for param in node.args]

                values = {
                    "style": all_params[0],
                    "thickness": all_params[1],
                    "color": all_params[2],
                }

                for var in self.local_var:
                    if var["name"] in values.values():
                        has_var = True
                        break

                return {
                    "instruction_type": "line_style",
                    "values": {
                        "style": all_params[0],
                        "thickness": all_params[1],
                        "color": all_params[2],
                    },
                    "has_var": has_var,
                }

            return None
        return None

    def build_if_chain(self, node: If | ElseIf | Block, branch_type: str = "if"):
        condition = ast.to_lua_source(node.test)

        branch_info = {
            "node_type": branch_type,
            "condition": condition,
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
