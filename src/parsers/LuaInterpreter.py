# src/parsers/LuaInterpreter.py

import glob
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Tuple, Dict

from luaparser.ast import SyntaxException
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
    Call,
    Index,
)

from ..utils.logger import config_logger

# Personalised Logging
LOGGER = config_logger(__name__)


class LuaInterpreter:

    # Maps Lua rendering instructions to their standardized internal instruction types
    TARGET_PREFIXES = {
        "PointInstruction": "symbol",
        "LocalOffset": "text",
        "AreaFillReference": "area_fill",
        "ColorFill": "color_fill",
        "LineInstruction": "line_instruction",
    }

    # Negation prefix
    NEGATION_PREFIX = "NOT ("

    def __init__(self, path: str):
        self.files = glob.glob(path)
        self.local_var = []
        self.related = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    ###################################################################################
    #                            MAIN FUNCTION                                        #
    ###################################################################################

    def get_analyses(self, output_dir: str = "./data/rules_parsed"):
        """The main function that gets the information of each rule in the lua files and genarate a parsed JSON file based on each one

        Args:
            output_dir (str, optional): The output path for the results. Defaults to "./data/rules_parsed".
        """

        LOGGER.info(f"{'#' * 30} GETTING RULES DATA {'#' * 30}")

        for file in self.files:
            self.local_var = []

            path = Path(file)
            if not path.exists():
                LOGGER.error(f"No file found for this pattern: {path}")
                return

            tree = self._get_lua_code(path)
            if tree is None:
                LOGGER.warning(
                    f"ERROR GETTING THE LUA CODE. SKIPPING FILE [{path}] PROCESSING !"
                )
                return

            base_name = path.stem
            LOGGER.info(f"PROCESSING [{base_name}.lua]")

            root_nodes = self._build_tree(tree)
            conditions = self._map_conditions(root_nodes)

            file_output_dir = Path(output_dir) / base_name
            os.makedirs(file_output_dir, exist_ok=True)

            ################### JUST FOR TESTS AND DEBUGS########################
            # self._write_json(file_output_dir / f"{base_name}.json", root_nodes)
            #####################################################################

            conditions_path = file_output_dir / f"{base_name}-conditions.json"
            self._write_json(conditions_path, data=conditions)

            self._collect_related(conditions, base_name)

        LOGGER.info('CREATING RELATED FILE ')
        related_path = Path("data") / "related_symbols.json"
        self._write_json(related_path, data=self.related)

        LOGGER.info(
            f"{'#' * 10} THE CAPTURE OF ALL INFORMATION FROM RULES FILE WAS COMPLETED {'#' * 10}"
        )

    ###################################################################################
    #                            WRITE FILES FUNCTION                                 #
    ###################################################################################

    def _write_json(self, path: Path, data: Any) -> None:
        """Writes data to a JSON file

        Args:
            path (Path): The destination file path
            data (Any): The data structure to serialize into JSON
        """
        try:
            with open(path, "w") as fp:
                json.dump(data, fp, indent=2, default=list)

            LOGGER.info(f"File [{path}] successfully written")

        except TypeError as err:
            LOGGER.error(
                f"JSON serialization error for file [{path}]. Error description: {err}"
            )

        except Exception as err:
            LOGGER.error(f"Error writing the file [{path}]. Error description: {err}")

    ###################################################################################
    #                            READ LUA FILES FUNCTION                              #
    ###################################################################################

    def _get_lua_code(self, file: str) -> Chunk:
        """Reads a Lua file and parses its contents into an Abstract Syntax Tree (AST)

        Args:
            file (str): The file path to the Lua script to be read

        Returns:
            Chunk: The root AST node representing the parsed Lua code
        """
        try:
            with open(file, "r", encoding="utf-8") as fp:
                source = fp.read()
            return ast.parse(source)

        except FileNotFoundError as err:
            LOGGER.error(
                f"No such file or directory [{file}]. Error description: {err}"
            )
            return None

        except SyntaxException as err:
            LOGGER.error(
                f"Error parsing the Lua file [{file}]. Error description: {err}"
            )
            return None

        except Exception as err:
            LOGGER.error(
                f"Error reading the Lua file [{file}]. Error description: {err}"
            )

    ###################################################################################
    #                            RELATED DATA FUNCTIONS                               #
    ###################################################################################

    def _collect_related(self, conditions: List, rule_name: str) -> None:
        """Collects and groups related visual instructions [symbol, line_instruction, area_fill] from parsed conditions

        Args:
            conditions (List): A List of Dictionaries representing parsed rules and conditions
            rule_name (str): The name of the rule currently being processed
        """
        try:
            
            for item in conditions:
                if item.get("node_type") != "hit" or item.get("instruction_type") not in [
                    "symbol",
                    "line_instruction",
                    "area_fill",
                ]:
                    continue

                items_vals = item.get("values") or {}
                values = {
                    "symbol": items_vals.get("PointInstruction"),
                    "line_style": items_vals.get("LineInstruction"),
                    "area_fill": items_vals.get("AreaFillReference"),
                }

                for visu_name in ["symbol", "line_style", "area_fill"]:
                    if values[visu_name] is not None:
                        for visu in self._flatten_values(values[visu_name]):
                            self.related[visu_name][visu]["rule"].add(rule_name)

        except Exception as err:
            LOGGER.error(
                f"Error collecting related instructions for rule [{rule_name}]. Error description: {err}"
            )

    def _flatten_values(self, value: str | List) -> List:
        """Recursively flattens a nested List or Dictionary of visual values

        Args:
            value (str | List): The value(s) to flatten

        Returns:
            List: A flattened List of string values
        """
        if isinstance(value, str):
            return [value]

        if isinstance(value, List):
            symbols = []
            for item in value:
                if isinstance(item, Dict) and "value" in item:
                    symbols.extend(self._flatten_values(item["value"]))
                else:
                    symbols.extend(self._flatten_values(item))
            return symbols

        return []

    ###################################################################################
    #                            NODE HELPERS                                         #
    ###################################################################################

    def _get_line_code(self, node: Node) -> int | None:
        """Extracts the line number from a given AST node

        Args:
            node (Node): The AST node to inspect

        Returns:
            int | None: The line number where the node is located
        """
        token = getattr(node, "first_token", None)
        if token is not None:
            return token.line

        return getattr(node, "line", None)

    def _get_parameters(self, node: Node) -> str | int | None:
        """Extracts and formats the string or numeric representation of parameters from a Lua function

        Args:
            node (Node): The AST node representing the parameter(s)

        Returns:
            str | int | None: The extracted parameter value
        """
        if isinstance(node, String):
            return node.raw

        if isinstance(node, Name):
            return node.id

        if isinstance(node, Concat):
            return (
                f"{self._get_parameters(node.left)}{self._get_parameters(node.right)}"
            )

        if isinstance(node, Number):
            return node.n

        if isinstance(node, Index):
            return (
                f"{self._get_parameters(node.value)}.{self._get_parameters(node.idx)}"
            )

        if isinstance(node, Call):
            func = f"{node.func.id}"

            args_str = []
            for arg in node.args:
                args_str.append(self._get_parameters(arg))

            return f"{func}({','.join(args_str)})"
        return None

    ###################################################################################
    #                           AST TRAVERSAL & CONSTRUCTION                          #
    ###################################################################################

    def _build_tree(self, tree: Chunk) -> List:
        """Builds a simplified representation of the LUA AST

        Args:
            tree (Chunk): The root AST node or chunk to traverse

        Returns:
            List: A structed List of parsed Lua nodes
        """
        if tree is None:
            LOGGER.warning("LUA FILE IS EMPTY !")
            return []

        if isinstance(tree, Chunk):
            return self._build_tree(tree.body)

        if isinstance(tree, Block):
            return self._build_tree_body(tree.body)

        return self._build_node(tree)

    def _build_tree_body(self, parent_node: Node) -> List:
        """Iterates through a parent node's children and builds their representations

        Args:
            parent_node (Node): The parent AST block

        Returns:
            List: A List of parsed child nodes
        """
        if not parent_node:
            return []

        nodes = []
        for node in parent_node:
            nodes.extend(self._build_node(node))
        return nodes

    def _build_node(self, node: Node) -> List[Dict]:
        """Routes a specific AST node to its corresponding build function

        Args:
            node (Node): The AST node to process

        Returns:
            List[Dict]: A List containing the processed node Dictionary
        """
        if node is None:
            return []

        node_info = self._get_info_node(node)
        if node_info:
            return [self._build_hit_node(node, node_info)]

        if isinstance(node, If):
            return self._build_if_chain(node)

        if isinstance(node, Function):
            return [
                {
                    "node_type": "function",
                    "name": ast.to_lua_source(node.name) if node.name else "Unknown",
                    "line": self._get_line_code(node),
                    "children": self._build_tree(node.body),
                }
            ]

        if isinstance(node, Block):
            return self._build_tree_body(node.body)

        if isinstance(node, Assign):
            return [self._build_var_node(node)]

        return []

    def _build_if_chain(
        self, node: If | ElseIf | Block, branch_type: str = "if"
    ) -> List[Dict]:
        """Contructs a logical chain for if/elseif/else conditional branches

        Args:
            node (If | ElseIf | Block): The conditional AST node
            branch_type (str, optional): The string of the type of branch. Defaults to "if".

        Returns:
            List[Dict]: A List of Dictionaries representing the condition chain
        """
        branch_info = {
            "node_type": branch_type,
            "condition": ast.to_lua_source(node.test),
            "line": self._get_line_code(node),
            "children": self._build_tree(node.body),
        }
        chain = [branch_info]

        orelse = node.orelse
        if orelse is None:
            return chain

        if isinstance(orelse, ElseIf):
            chain.extend(self._build_if_chain(orelse, branch_type="elseif"))
        elif isinstance(orelse, Block):
            chain.append(
                {
                    "node_type": "else",
                    "line": self._get_line_code(orelse),
                    "children": self._build_tree_body(orelse.body),
                }
            )

        return chain

    ###################################################################################
    #                            LUA INSTRUCTION PARSERS                              #
    ###################################################################################

    def _get_info_node(self, node: Node) -> Dict | None:
        """Determines if a node is a specific target function invocation and extracts its info

        Args:
            node (Node): The AST node to check

        Returns:
            Dict | None: The parsed instruction details
        """

        if not isinstance(node, Invoke):
            return None

        func_name = node.func.id if isinstance(node.func, Name) else None

        if func_name == "AddInstructions":
            return self._info_add_instructions(node)

        if func_name == "SimpleLineStyle":
            return self._info_simple_line_style(node)

        if func_name == "AddTextInstruction":
            return self._info_text_instruction(node)

        return None

    def _build_hit_node(self, node: Node, node_info: Dict) -> Dict:
        """Builds a 'hit' node Dictionary representing a recognized drawing instruction (Symbols, Texts, Line Styles, AreaFills)

        Args:
            node (Node): The original AST node
            node_info (Dict): The extractes instruction information

        Returns:
            Dict: The complete hit node representation
        """

        node_dt = {
            "node_type": "hit",
            "line": self._get_line_code(node),
            "code": ast.to_lua_source(node),
        } | node_info

        if node_dt["instruction_type"] == "text":
            x, y = node_dt["values"]["LocalOffset"].split(",")
            node_dt["values"]["LocalOffset"] = {"x": x.strip(), "y": y.strip()}

        return node_dt

    def _build_var_node(self, node: Assign) -> Dict:
        """Builds a variable assignment node

        Args:
            node (Assign): The assignment AST node

        Returns:
            Dict: The Dictionary representation of the variable assignment

        """
        value = self._assign_value(node)
        name = self._assign_target_name(node)

        # Add the variable to the variables array to verify whether the other functions use it
        self.local_var.append({"name": name, "value": value})

        return {
            "node_type": "var",
            "name": name,
            "instruction_type": node.display_name,
            "line": self._get_line_code(node),
            "code": ast.to_lua_source(node),
            "value": value,
        }

    def _assign_target_name(self, node: Assign) -> str | None:
        """Extracts the variable name from an assignement node

        Args:
            node (Assign): The assignment AST node

        Returns:
            str | None: The name of the node
        """
        target = node.targets[0]
        return getattr(target, "id", None) or getattr(
            getattr(target, "idx", None), "id", None
        )

    def _assign_value(self, node: Assign) -> str | None:
        """Extracts the literal value assigned

        Args:
            node (Assign): The assignment AST node

        Returns:
            str | None: The literal value
        """

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

    def _info_add_instructions(self, node: Invoke) -> Dict | None:
        """Extracts the parameters from an 'AddInstructions' function call

        Args:
            node (Invoke): The AST invocation node

        Returns:
            Dict | None: The parsed instruction values of each parameter
        """
        all_params = self._get_parameters(node.args[0])
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

    def _info_simple_line_style(self, node: Invoke) -> Dict:
        """Extracts parameters from 'SimpleLineStyle' function call

        Args:
            node (Invoke): The AST invocation node

        Returns:
            Dict: The parsed instruction values of each parameter
        """

        style, thickness, color = [self._get_parameters(arg) for arg in node.args]
        has_var = any(self._references_local_var(v) for v in (style, thickness, color))

        return {
            "instruction_type": "line_style",
            "values": {"style": style, "thickness": thickness, "color": color},
            "has_var": has_var,
        }

    def _info_text_instruction(self, node: Invoke) -> Dict:
        """Extracts parameters from 'AddTextInstruction' function call

        Args:
            node (Invoke): The AST invocation node

        Returns:
            Dict: The parsed instruction values of each parameter
        """
        data = [self._get_parameters(arg) for arg in node.args]

        raw_text = data[0]
        text_vw_group = data[1]
        text_priority = data[2]
        view_group = data[3]
        priority = data[4] if len(data) > 4 else 0
        hover = data[5] if len(data) > 5 else False

        has_var = any(self._references_local_var(v) for v in data)

        return {
            "instruction_type": "text_instruction",
            "values": {
                "raw_text": raw_text,
                "text_vw_group": text_vw_group,
                "text_priority": text_priority,
                "view_group": view_group,
                "priority": priority,
                "hover": hover,
            },
            "has_var": has_var,
        }

    ###################################################################################
    #                         CONTROL FLOW & CONDITION MAPPING                        #
    ###################################################################################

    def _map_conditions(
        self, root_nodes: List[Dict], base_path: List = None, obj: List[Dict] = None
    ) -> List[Dict]:
        """Initializes and begins the conditional mapping process over the parsed nodes

        Args:
            nodes (List): The list of parsed AST nodes from self._build_tree
            base_path (List, optional): The current path of logic conditions. Defaults to None.
            obj (List, optional): The accumulated list of resolved objects. Defaults to None.

        Returns:
            List[Dict]: The fully resolved list of conditions objects
        """

        if base_path is None:
            base_path = []

        if obj is None:
            obj = []

        self._walk(root_nodes, base_path, {}, obj)

        return obj

    def _walk(self, nodes: List, base_path: List, var_state: Dict, obj: List) -> Dict:
        """Traverses the parsed nodes, tracking variables and resolving conditions

        Args:
            nodes (List): The nodes to traverse
            base_path (List): The active logical branch conditions
            var_state (Dict): The current state of declared variables
            obj (List): The output array being built

        Returns:
            Dict: The updated variable state
        """
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
                chain = [node]
                j = i + 1
                while j < n and nodes[j].get("node_type") in ("elseif", "else"):
                    chain.append(nodes[j])
                    j += 1

                var_state = self._process_if_chain(chain, base_path, var_state, obj)
                i = j
                continue

            children = node.get("children")
            if children:
                var_state = self._walk(children, base_path, var_state, obj)
            i += 1

        return var_state

    def _handle_var_node(self, node: Dict, base_path: List, var_state: Dict) -> Dict:
        """Registers a variable assignment in the current state

        Args:
            node (Dict): The variable node
            base_path (List): The active logical branch conditions
            var_state (Dict): The current state of declared varibles

        Returns:
            Dict: The update variable state with the new assignment
        """

        name = node.get("name")
        if name is None:
            return var_state
        return {**var_state, name: [(node.get("value"), list(base_path))]}

    def _process_if_chain(
        self, chain: List, base_path: List, var_state_in: Dict, obj: List
    ) -> Dict:
        """Traverses an if/elseif/else block and returns the var_state resulting from the junction of all possible branches

        Args:
            chain (List): The sequential chain of conditional branches
            base_path (List): The active logical branch conditions
            var_state_in (Dict): The incoming state of variables before the chain
            obj (List): The output array being built

        Returns:
            Dict: The merged state of variables after processing all branches
        """

        branch_results, has_else = self._collect_branch_results(
            chain, base_path, var_state_in, obj
        )

        if not has_else:
            none_path = base_path + self._all_negations(chain)
            branch_results.append((none_path, dict(var_state_in)))

        return self._merge_branch_states(chain, var_state_in, branch_results)

    def _collect_branch_results(
        self, chain: List, base_path: List, var_state_in: Dict, obj: List
    ) -> Tuple[List, bool]:
        """Gathers the resulting variable states from each conditional branch

        Args:
            chain (List): The sequential chain of conditional branches
            base_path (List): The active logical branch conditions
            var_state_in (Dict): The incoming state of variables
            obj (List): The output array being built

        Returns:
            Tuple[List, bool]: A tuple containing the list of branch results and a boolean indicating is an 'else' block exists
        """
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

    ###################################################################################
    #                      VARIABLE RESOLUTION & DEDUPLICATION                        #
    ###################################################################################

    def _references_local_var(self, value: Any) -> bool:
        """Checks if the value references a known local variable

        Args:
            value (Any): The value to check for variable references

        Returns:
            bool: True if the value references a known local variable, False otherwise
        """
        return any(var["name"] in str(value) for var in self.local_var)

    def _all_negations(self, chain: List) -> List:
        """Returs all negations for a given conditional chain

        Args:
            chain (List): The sequential chain of conditional branches

        Returns:
            List: A list of negated condition strings
        """

        return [
            self._negate(branch["condition"])
            for branch in chain
            if branch.get("node_type") != "else" and branch.get("condition") is not None
        ]

    def _negate(self, condition: str) -> str:
        """Wraps a condition string in a negation block

        Args:
            condition (str): The condition to negate

        Returns:
            str: The negated condition string
        """
        return f"{self.NEGATION_PREFIX}{condition})"

    def _merge_branch_states(
        self, chain: List, var_state_in: Dict, branch_results: List
    ) -> Dict:
        """Merges variable states derived from multiple branches back into a single dictionary

        Args:
            chain (List): The sequential chain of conditional branches
            var_state_in (Dict): The state of variables prior to the branches
            branch_results (List): The resulting states from traverasing each branch

        Returns:
            Dict: The combined dictionary of variable states
        """

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

    def _resolve_hit(self, node: Dict, var_state: Dict, base_path: List) -> Dict:
        """Resolves the variables and conditions associated with a hit node

        Args:
            node (Dict): The representation of the hit node
            var_state (Dict): The current variable state
            base_path (List): The active logical branch conditions

        Returns:
            Dict: The resolved node dictionary
        """
        resolved = {**node, "conditions": self._visible_conditions(base_path)}

        if not node.get("has_var"):
            return resolved

        values = node.get("values") or {}
        resolved["values"] = self._resolve_value(values, var_state, base_path)
        return resolved

    def _resolve_value(
        self, val: Dict | str | Any, var_state: Dict, base_path: List
    ) -> List | Dict:
        """_summary_

        Args:
            val (Dict | str | Any): The value to resolve
            var_state (Dict): The current variable state
            base_path (List): The active logical branch conditions

        Returns:
            List | Dict: The fulley resolved value or nested dictionary of values
        """

        if isinstance(val, Dict):
            return {
                k: self._resolve_value(v, var_state, base_path) for k, v in val.items()
            }

        if not isinstance(val, str):
            return val

        if val in var_state:
            return self._value_from_entries(var_state[val], base_path)

        for key, entries in var_state.items():
            if key in val:
                substituted = [(val.replace(key, str(v)), path) for v, path in entries]
                return self._value_from_entries(substituted, base_path)

        return val

    def _value_from_entries(
        self, entries: List[Tuple], base_path: List
    ) -> Any | List[Dict]:
        """Combines paths from variable entries and the base path to return resolved valeus

        Args:
            entries (List[Tuple]): A list of tuples containing variables values and paths
            base_path (List): The active logical branch conditions

        Returns:
            List[Dict]: The resolved value, or a list of conditional values if multiple branches exist
        """

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

    def _visible_conditions(self, conditions: List) -> List:
        """Removes negative conditions (NOT (...)) before exposing a condition path in the final result

        Args:
            conditions (List): The full list of branch conditions

        Returns:
            List: A filtered list of only the positive conditions
        """

        return [c for c in conditions if not str(c).startswith(self.NEGATION_PREFIX)]

    def _collect_assigned_names(self, nodes: List) -> set:
        """Collects all variable names assigned within a list of nodes

        Args:
            nodes (List): The list of nodes to traverse

        Returns:
            set: A set containing the names of all assigned variables [No repeated variable names]
        """

        names = set()
        for node in nodes:
            if node.get("node_type") == "var" and node.get("name"):
                names.add(node["name"])
            children = node.get("children")
            if children:
                names |= self._collect_assigned_names(children)
        return names

    def _dedup(self, path: List) -> List:
        """Removes duplicate string entries from a path while preserving order

        Args:
            path (List): The list of path segments

        Returns:
            List: The deduplicated path list
        """

        return list(dict.fromkeys(path))

    def _dedup_entries(self, entries: List[Tuple]) -> List:
        """Removes duplicate variable entries based on their value and condition path

        Args:
            entries (List[Tuple]): The list of entry tuples to duplicate

        Returns:
            List: The duduplicated list of entries
        """

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
