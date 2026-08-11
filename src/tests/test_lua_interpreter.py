import json
import os
from collections import defaultdict

import pytest
from luaparser import ast as lua_ast

from src.parsers.LuaInterpreter import LuaInterpreter


# --------------------------------------------------------------------------- #
#                                  FIXTURES                                   #
# --------------------------------------------------------------------------- #


@pytest.fixture
def interpreter():
    """Retorna uma instância 'crua' de LuaInterpreter, sem tocar no filesystem.

    Usamos __new__ para não depender de glob.glob() sobre um path real,
    já que os testes normalmente montam o código Lua em memória / em
    arquivos temporários criados pelo próprio teste.
    """
    interp = LuaInterpreter.__new__(LuaInterpreter)
    interp.files = []
    interp.local_var = []
    interp.related = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    return interp


def build_conditions(interpreter, lua_code: str):
    """Helper de teste: parseia uma string Lua e retorna a lista de condições resolvidas."""
    tree = lua_ast.parse(lua_code)
    nodes = interpreter._build_tree(tree)
    return interpreter._map_conditions(nodes)


def build_nodes(interpreter, lua_code: str):
    """Helper de teste: parseia uma string Lua e retorna a árvore simplificada (_build_tree)."""
    tree = lua_ast.parse(lua_code)
    return interpreter._build_tree(tree)


def hits_by_line(conditions):
    return {c["line"]: c for c in conditions if c.get("node_type") == "hit"}


# --------------------------------------------------------------------------- #
#                    TESTES: HELPERS PUROS (SEM DEPENDER DO AST)              #
# --------------------------------------------------------------------------- #


class TestDedup:
    def test_dedup_preserves_order_and_removes_duplicates(self, interpreter):
        assert interpreter._dedup(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_dedup_empty_list(self, interpreter):
        assert interpreter._dedup([]) == []

    def test_dedup_entries_removes_duplicate_scalar_values(self, interpreter):
        entries = [("v1", ["a"]), ("v1", ["a"]), ("v2", ["a"])]
        result = interpreter._dedup_entries(entries)
        assert result == [("v1", ["a"]), ("v2", ["a"])]

    def test_dedup_entries_keeps_same_value_with_different_path(self, interpreter):
        entries = [("v1", ["a"]), ("v1", ["b"])]
        result = interpreter._dedup_entries(entries)
        assert result == [("v1", ["a"]), ("v1", ["b"])]

    def test_dedup_entries_handles_unhashable_dict_values(self, interpreter):
        entries = [({"k": 1}, ["a"]), ({"k": 1}, ["a"]), ({"k": 2}, ["a"])]
        result = interpreter._dedup_entries(entries)
        assert result == [({"k": 1}, ["a"]), ({"k": 2}, ["a"])]


class TestNegationAndVisibility:
    def test_negate_wraps_condition(self, interpreter):
        assert interpreter._negate('x == "1"') == 'NOT (x == "1")'

    def test_visible_conditions_strips_negated_entries(self, interpreter):
        conditions = ['a == "1"', 'NOT (b == "2")', 'c == "3"']
        assert interpreter._visible_conditions(conditions) == ['a == "1"', 'c == "3"']

    def test_visible_conditions_empty_when_all_negated(self, interpreter):
        conditions = ['NOT (a == "1")', 'NOT (b == "2")']
        assert interpreter._visible_conditions(conditions) == []

    def test_visible_conditions_passthrough_when_no_negation(self, interpreter):
        conditions = ['a == "1"', 'b == "2"']
        assert interpreter._visible_conditions(conditions) == conditions


class TestFlattenValues:
    def test_flatten_single_string(self, interpreter):
        assert interpreter._flatten_values("SYM1") == ["SYM1"]

    def test_flatten_list_of_strings(self, interpreter):
        assert interpreter._flatten_values(["SYM1", "SYM2"]) == ["SYM1", "SYM2"]

    def test_flatten_list_of_condition_dicts(self, interpreter):
        value = [
            {"value": "SYM1", "conditions": ["a"]},
            {"value": "SYM2", "conditions": []},
        ]
        assert interpreter._flatten_values(value) == ["SYM1", "SYM2"]

    def test_flatten_none_returns_empty_list(self, interpreter):
        assert interpreter._flatten_values(None) == []

    def test_flatten_nested_dict_value_recurses(self, interpreter):
        value = [{"value": ["SYM1", "SYM2"], "conditions": []}]
        assert interpreter._flatten_values(value) == ["SYM1", "SYM2"]


class TestReferencesLocalVar:
    def test_true_when_value_contains_var_name(self, interpreter):
        interpreter.local_var = [{"name": "color", "value": "CHBLK"}]
        assert interpreter._references_local_var("color") is True
        assert interpreter._references_local_var("prefix_color_suffix") is True

    def test_false_when_no_match(self, interpreter):
        interpreter.local_var = [{"name": "color", "value": "CHBLK"}]
        assert interpreter._references_local_var("thickness") is False

    def test_false_when_no_local_vars_registered(self, interpreter):
        interpreter.local_var = []
        assert interpreter._references_local_var("anything") is False


# --------------------------------------------------------------------------- #
#                TESTES: CONSTRUÇÃO DA ÁRVORE (_build_tree)                   #
# --------------------------------------------------------------------------- #


class TestBuildTree:
    def test_empty_tree_returns_empty_list(self, interpreter):
        assert interpreter._build_tree(None) == []

    def test_top_level_function_call_is_ignored(self, interpreter):
        """Chamadas de função "soltas" (Call, não Invoke em obj:Metodo()) não geram hit.

        Isso reflete o formato real dos arquivos de portrayal do S-101, em que as
        instruções sempre são invocadas como método do objeto (obj:AddInstructions(...)).
        """
        lua_code = 'function Rule(obj)\n  AddInstructions("PointInstruction:SYM1")\nend\n'
        nodes = build_nodes(interpreter, lua_code)
        function_node = nodes[0]
        assert function_node["node_type"] == "function"
        assert function_node["children"] == []

    def test_method_call_produces_hit_node(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("PointInstruction:SYM1")\nend\n'
        nodes = build_nodes(interpreter, lua_code)
        children = nodes[0]["children"]
        assert len(children) == 1
        assert children[0]["node_type"] == "hit"
        assert children[0]["instruction_type"] == "symbol"

    def test_if_elseif_else_chain_is_flattened(self, interpreter):
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            elseif obj:attr("cat") == "2" then
                obj:AddInstructions("PointInstruction:SYM2")
            else
                obj:AddInstructions("PointInstruction:SYM3")
            end
        end
        """
        nodes = build_nodes(interpreter, lua_code)
        chain = nodes[0]["children"]
        types = [b["node_type"] for b in chain]
        assert types == ["if", "elseif", "else"]

    def test_if_without_else_has_no_else_branch(self, interpreter):
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            end
        end
        """
        nodes = build_nodes(interpreter, lua_code)
        chain = nodes[0]["children"]
        assert [b["node_type"] for b in chain] == ["if"]

    def test_var_assignment_produces_var_node_and_registers_local_var(self, interpreter):
        lua_code = 'function Rule(obj)\n  local color = "CHBLK"\nend\n'
        nodes = build_nodes(interpreter, lua_code)
        var_node = nodes[0]["children"][0]
        assert var_node["node_type"] == "var"
        assert var_node["name"] == "color"
        assert var_node["value"] == "CHBLK"
        assert interpreter.local_var == [{"name": "color", "value": "CHBLK"}]

    def test_numeric_var_assignment(self, interpreter):
        lua_code = "function Rule(obj)\n  local priority = 5\nend\n"
        nodes = build_nodes(interpreter, lua_code)
        var_node = nodes[0]["children"][0]
        assert var_node["value"] == 5

    def test_negative_numeric_var_assignment(self, interpreter):
        lua_code = "function Rule(obj)\n  local offset = -3\nend\n"
        nodes = build_nodes(interpreter, lua_code)
        var_node = nodes[0]["children"][0]
        assert var_node["value"] == -3

    def test_table_var_assignment_yields_empty_dict(self, interpreter):
        lua_code = "function Rule(obj)\n  local t = {}\nend\n"
        nodes = build_nodes(interpreter, lua_code)
        var_node = nodes[0]["children"][0]
        assert var_node["value"] == {}


# --------------------------------------------------------------------------- #
#             TESTES: RECONHECIMENTO DE INSTRUÇÕES (hit nodes)                #
# --------------------------------------------------------------------------- #


class TestInstructionParsing:
    def test_add_instructions_symbol(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("PointInstruction:SYM1")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        assert len(conditions) == 1
        hit = conditions[0]
        assert hit["instruction_type"] == "symbol"
        assert hit["values"] == {"PointInstruction": "SYM1"}
        assert hit["has_var"] is False

    def test_add_instructions_with_local_offset_splits_x_y(self, interpreter):
        lua_code = (
            'function Rule(obj)\n'
            '  obj:AddInstructions("LocalOffset:10, 20;ColorFill:CHBLK")\n'
            'end\n'
        )
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        assert hit["instruction_type"] == "text"
        assert hit["values"]["LocalOffset"] == {"x": "10", "y": "20"}
        assert hit["values"]["ColorFill"] == "CHBLK"

    def test_add_instructions_unrecognized_first_key_is_dropped(self, interpreter):
        """Se a primeira chave não estiver em TARGET_PREFIXES, o nó não vira um hit."""
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("UnknownKey:VAL1")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        assert conditions == []

    def test_add_instructions_empty_args_returns_no_hit(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        assert conditions == []

    def test_simple_line_style(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:SimpleLineStyle("SOLD", "1", "CHBLK")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        assert hit["instruction_type"] == "line_style"
        assert hit["values"] == {"style": "SOLD", "thickness": "1", "color": "CHBLK"}
        assert hit["has_var"] is False

    def test_add_text_instruction_minimal_args(self, interpreter):
        lua_code = (
            'function Rule(obj)\n'
            '  obj:AddTextInstruction("MyText", "10,20", "1", "2")\n'
            'end\n'
        )
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        assert hit["instruction_type"] == "text_instruction"
        assert hit["values"]["raw_text"] == "MyText"
        assert hit["values"]["priority"] == 0
        assert hit["values"]["hover"] is False

    def test_add_text_instruction_with_all_args(self, interpreter):
        lua_code = (
            'function Rule(obj)\n'
            '  obj:AddTextInstruction("MyText", "10,20", "1", "2", "3", "true")\n'
            'end\n'
        )
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        assert hit["values"]["priority"] == "3"
        assert hit["values"]["hover"] == "true"

    def test_unrecognized_method_call_produces_no_hit(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:SomeOtherMethod("x")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        assert conditions == []


# --------------------------------------------------------------------------- #
#             TESTES: MAPEAMENTO DE CONDIÇÕES (if/elseif/else)                #
# --------------------------------------------------------------------------- #


class TestConditionMapping:
    def test_hit_outside_any_branch_has_no_conditions(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("PointInstruction:SYM1")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        assert conditions[0]["conditions"] == []

    def test_if_branch_condition_is_attached_to_hit(self, interpreter):
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            end
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        assert conditions[0]["conditions"] == ['obj:attr("cat") == "1"']

    def test_else_branch_condition_is_negation_of_if_and_stripped_from_output(
        self, interpreter
    ):
        """A condição do 'else' é internamente NOT (if_condition), mas não deve
        aparecer no resultado final (ela é filtrada por _visible_conditions)."""
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            else
                obj:AddInstructions("PointInstruction:SYM2")
            end
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        by_line = hits_by_line(conditions)
        if_hit = [h for h in conditions if h["values"]["PointInstruction"] == "SYM1"][0]
        else_hit = [h for h in conditions if h["values"]["PointInstruction"] == "SYM2"][0]

        assert if_hit["conditions"] == ['obj:attr("cat") == "1"']
        # A condição do else não deve conter "NOT (" nem qualquer resquício de negação
        assert else_hit["conditions"] == []
        for cond in else_hit["conditions"]:
            assert LuaInterpreter.NEGATION_PREFIX not in cond

    def test_elseif_chain_accumulates_prior_negations_internally_but_hides_them(
        self, interpreter
    ):
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            elseif obj:attr("cat") == "2" then
                obj:AddInstructions("PointInstruction:SYM2")
            end
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        sym2_hit = [h for h in conditions if h["values"]["PointInstruction"] == "SYM2"][0]
        
        # Apenas a condição positiva do próprio ramo elseif deve ficar visível
        assert sym2_hit["conditions"] == ['obj:attr("cat") == "2"']

    def test_no_negation_prefix_leaks_into_any_output_condition(self, interpreter):
        lua_code = """
        function Rule(obj)
            if obj:attr("cat") == "1" then
                obj:AddInstructions("PointInstruction:SYM1")
            elseif obj:attr("cat") == "2" then
                obj:AddInstructions("PointInstruction:SYM2")
            else
                obj:AddInstructions("PointInstruction:SYM3")
            end
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        for hit in conditions:
            for cond in hit["conditions"]:
                assert not str(cond).startswith(LuaInterpreter.NEGATION_PREFIX)


# --------------------------------------------------------------------------- #
#         TESTES: RESOLUÇÃO DE VARIÁVEIS (reaching-definitions)               #
# --------------------------------------------------------------------------- #


class TestVariableResolution:
    def test_variable_used_without_reassignment_resolves_to_scalar(self, interpreter):
        lua_code = """
        function Rule(obj)
            local color = "CHBLK"
            obj:AddInstructions("PointInstruction:SYM1;ColorFill:" .. color)
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        
        # Um único valor possível e sem condições -> deve virar escalar, não lista
        assert hit["values"]["ColorFill"] == "CHBLK"

    def test_variable_reassigned_inside_if_produces_conditional_list(self, interpreter):
        lua_code = """
        function Rule(obj)
            local color = "CHBLK"
            if obj:attr("cat") == "1" then
                color = "CHRED"
            end
            obj:AddInstructions("PointInstruction:SYM1;ColorFill:" .. color)
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        hit = conditions[0]
        values = hit["values"]["ColorFill"]

        assert isinstance(values, list)
        as_map = {entry["value"]: entry["conditions"] for entry in values}
        assert as_map["CHRED"] == ['obj:attr("cat") == "1"']
        assert as_map["CHBLK"] == []

    def test_variable_reassigned_in_every_branch_of_if_else(self, interpreter):
        lua_code = """
        function Rule(obj)
            local color = "CHBLK"
            if obj:attr("cat") == "1" then
                color = "CHRED"
            else
                color = "CHGRN"
            end
            obj:AddInstructions("PointInstruction:SYM1;ColorFill:" .. color)
        end
        """
        conditions = build_conditions(interpreter, lua_code)
        values = conditions[0]["values"]["ColorFill"]
        as_map = {entry["value"]: entry["conditions"] for entry in values}
        assert as_map['CHRED'] == ['obj:attr("cat") == "1"']
        # Condição do else é interna (NOT (...)) e não deve aparecer aqui
        assert as_map['CHGRN'] == []

    def test_hit_without_has_var_keeps_raw_values_unresolved(self, interpreter):
        lua_code = 'function Rule(obj)\n  obj:AddInstructions("PointInstruction:SYM1")\nend\n'
        conditions = build_conditions(interpreter, lua_code)
        # has_var é False, então _resolve_value nunca é chamado
        assert conditions[0]["values"] == {"PointInstruction": "SYM1"}


# --------------------------------------------------------------------------- #
#                  TESTES: COLETA DE DADOS RELACIONADOS (related.json)        #
# --------------------------------------------------------------------------- #


class TestCollectRelated:
    def test_collects_symbol_line_and_area_fill(self, interpreter):
        conditions = [
            {
                "node_type": "hit",
                "instruction_type": "symbol",
                "values": {"PointInstruction": "SYM1"},
            },
            {
                "node_type": "hit",
                "instruction_type": "line_instruction",
                "values": {"LineInstruction": "LINE1"},
            },
            {
                "node_type": "hit",
                "instruction_type": "area_fill",
                "values": {"AreaFillReference": ["AF1", "AF2"]},
            },
        ]
        interpreter._collect_related(conditions, "RuleX")

        assert "RuleX" in interpreter.related["symbol"]["SYM1"]["rule"]
        assert "RuleX" in interpreter.related["line_style"]["LINE1"]["rule"]
        assert "RuleX" in interpreter.related["area_fill"]["AF1"]["rule"]
        assert "RuleX" in interpreter.related["area_fill"]["AF2"]["rule"]

    def test_ignores_non_hit_and_non_visual_instruction_types(self, interpreter):
        conditions = [
            {"node_type": "var", "instruction_type": "symbol", "values": {}},
            {
                "node_type": "hit",
                "instruction_type": "text_instruction",
                "values": {"raw_text": "hi"},
            },
        ]
        interpreter._collect_related(conditions, "RuleX")
        assert interpreter.related == {}

    def test_multiple_rules_referencing_same_symbol_are_aggregated(self, interpreter):
        conditions = [
            {
                "node_type": "hit",
                "instruction_type": "symbol",
                "values": {"PointInstruction": "SYM1"},
            }
        ]
        interpreter._collect_related(conditions, "RuleA")
        interpreter._collect_related(conditions, "RuleB")
        assert interpreter.related["symbol"]["SYM1"]["rule"] == {"RuleA", "RuleB"}


# --------------------------------------------------------------------------- #
#                    TESTES: FLUXO PONTA-A-PONTA (get_analyses)               #
# --------------------------------------------------------------------------- #


class TestGetAnalysesEndToEnd:
    @pytest.fixture
    def lua_file(self, tmp_path):
        lua_code = """
        function Rule(obj)
            if obj:attr("categoryOfLight") == "1" then
                obj:AddInstructions("PointInstruction:LIGHTS11")
            else
                obj:AddInstructions("PointInstruction:LIGHTS12")
            end
        end
        """
        lua_path = tmp_path / "CardinalBuoy.lua"
        lua_path.write_text(lua_code)
        return lua_path

    def test_generates_conditions_json_file(self, lua_file, tmp_path, monkeypatch):
        # 'related.json' é escrito em um caminho relativo fixo ("data/related.json"),
        # então isolamos o cwd do teste em um diretório temporário com "data/" já criado.
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)

        interp = LuaInterpreter(str(lua_file))
        out_dir = tmp_path / "rules_parsed"
        interp.get_analyses(output_dir=str(out_dir))

        conditions_path = out_dir / "CardinalBuoy" / "CardinalBuoy-conditions.json"
        assert conditions_path.exists()

        data = json.loads(conditions_path.read_text())
        assert len(data) == 2
        symbols = {hit["values"]["PointInstruction"] for hit in data}
        assert symbols == {"LIGHTS11", "LIGHTS12"}

    def test_generates_related_json_file(self, lua_file, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)

        interp = LuaInterpreter(str(lua_file))
        interp.get_analyses(output_dir=str(tmp_path / "rules_parsed"))

        related_path = tmp_path / "data" / "related.json"
        assert related_path.exists()

        related = json.loads(related_path.read_text())
        assert "LIGHTS11" in related["symbol"]
        assert "LIGHTS12" in related["symbol"]
        assert "CardinalBuoy" in related["symbol"]["LIGHTS11"]["rule"]

    def test_no_matching_files_leaves_files_list_empty(self, tmp_path):
        interp = LuaInterpreter(str(tmp_path / "does_not_exist_*.lua"))
        assert interp.files == []

    def test_resets_local_var_between_files(self, tmp_path, monkeypatch):
        """local_var não deve vazar de um arquivo para o outro (bug de leakage de estado)."""
        monkeypatch.chdir(tmp_path)
        os.makedirs("data", exist_ok=True)

        file_a = tmp_path / "RuleA.lua"
        file_a.write_text(
            'function Rule(obj)\n'
            '  local color = "CHBLK"\n'
            '  obj:AddInstructions("PointInstruction:SYM1;ColorFill:" .. color)\n'
            'end\n'
        )
        file_b = tmp_path / "RuleB.lua"
        file_b.write_text(
            'function Rule(obj)\n'
            '  obj:AddInstructions("PointInstruction:SYM2;ColorFill:" .. color)\n'
            'end\n'
        )

        interp = LuaInterpreter(str(tmp_path / "Rule*.lua"))
        interp.files = sorted(interp.files)  # ordem determinística: RuleA antes de RuleB
        interp.get_analyses(output_dir=str(tmp_path / "rules_parsed"))

        rule_b_conditions = json.loads(
            (tmp_path / "rules_parsed" / "RuleB" / "RuleB-conditions.json").read_text()
        )
        # Em RuleB, "color" não foi declarado localmente: como local_var foi
        # resetado, has_var deve ser False e o valor bruto ("color") deve
        # permanecer sem substituição.
        hit = rule_b_conditions[0]
        assert hit["values"]["ColorFill"] == "color"