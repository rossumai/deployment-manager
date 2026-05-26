"""Tests for deploy/subcommands/template/helpers.py — pure helpers only."""

from copy import deepcopy

import pytest
from anyio import Path

from deployment_manager.commands.deploy.subcommands.template.helpers import (
    DEFAULT_TARGETS,
    AttributeOverride,
    add_multi_targets_to_object,
    add_override_to_deploy_file_object,
    add_override_to_deploy_file_objects,
    add_targets_for_objects,
    add_targets_from_mapping,
    check_input_integer,
    collect_rule_dependency_ids,
    create_deploy_file_template,
    find_all_email_template_paths_for_dir,
    find_creatable_email_template_paths,
    find_email_template_paths_for_queue,
    find_engine_field_paths_for_engine,
    find_engine_paths_for_dir,
    find_hooks_for_queues,
    find_label_paths_for_dir,
    find_queue_paths_for_workspaces,
    find_rule_paths_for_dir,
    find_rules_for_queues,
    find_ws_paths_for_dir,
    get_email_templates_from_user,
    get_labels_from_user,
    get_rule_dependency_objects,
    prepare_choices,
    prepare_deploy_file_objects,
    prepare_email_template_deploy_file_objects,
    prepare_engine_fields_for_deploy,
    prepare_subqueue_deploy_file_object,
)
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings


class TestCreateDeployFileTemplate:
    def test_contains_required_keys(self):
        template = create_deploy_file_template()
        for key in (
            settings.DEPLOY_KEY_TARGET_URL,
            settings.DEPLOY_KEY_SOURCE_DIR,
            settings.DEPLOY_KEY_TARGET_DIR,
            settings.DEPLOY_KEY_TOKEN_OWNER,
            settings.DEPLOY_KEY_PATCH_TARGET_ORG,
        ):
            assert f"{key}:" in template

    def test_has_section_headers(self):
        template = create_deploy_file_template()
        for section in (
            "workspaces:",
            "queues:",
            "hooks:",
            "engines:",
            "rules:",
            "labels:",
            "email_templates:",
        ):
            assert section in template

    def test_optional_list_sections_parse_to_none(self):
        # Bare `labels:` / `email_templates:` in the template parse to None, NOT []. Callers
        # must guard with `or []` before iterating (regression: create flow crashed on None).
        from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml

        data = DeployYaml(create_deploy_file_template()).data
        assert data.get(settings.DEPLOY_KEY_LABELS) is None
        assert data.get(settings.DEPLOY_KEY_EMAIL_TEMPLATES) is None
        assert (data.get(settings.DEPLOY_KEY_LABELS) or []) == []


class TestCheckInputInteger:
    def test_valid_integer(self):
        assert check_input_integer("42") is True

    def test_zero(self):
        # falsy int → returns None (not True)
        assert check_input_integer("0") is None

    def test_invalid_string(self):
        assert check_input_integer("abc") == "Invalid integer"

    def test_empty(self):
        assert check_input_integer("") == "Invalid integer"


class TestPrepareDeployFileObjects:
    def test_basic_shape(self):
        objects = [
            {"id": 1, "name": "Q1", "path": Path("src/primary/workspaces/W_[5]/queues/Q_[1]/queue.json")},
        ]
        result = prepare_deploy_file_objects(objects=objects, include_path=True)
        assert len(result) == 1
        entry = result[0]
        assert entry["id"] == 1
        assert entry["name"] == "Q1"
        # base_path is parent.parent.parent of the queue.json (= workspace dir)
        assert entry[settings.DEPLOY_KEY_BASE_PATH] == "src/primary/workspaces/W_[5]"
        assert entry[settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS

    def test_without_path(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        result = prepare_deploy_file_objects(objects=objects, include_path=False)
        assert settings.DEPLOY_KEY_BASE_PATH not in result[0]

    def test_preserves_previous_targets(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        previous = [
            {"id": 1, "targets": [{"id": 99, "attribute_override": {"name": "kept"}}]}
        ]
        result = prepare_deploy_file_objects(
            objects=objects,
            include_path=False,
            objects_in_previous_file=previous,
        )
        # Previous targets preserved
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 99, "attribute_override": {"name": "kept"}}]

    def test_extra_attributes(self):
        objects = [{"id": 1, "name": "Q1", "path": Path("a/b/c/d.json")}]
        result = prepare_deploy_file_objects(
            objects=objects,
            include_path=False,
            extra_attributes={"ignore_deploy_warnings": False},
        )
        assert result[0]["ignore_deploy_warnings"] is False


class TestPrepareSubqueueDeployFileObject:
    def test_basic(self):
        obj = {"id": 42, "name": "subobject"}
        result = prepare_subqueue_deploy_file_object(obj)
        assert result == {"id": 42, "targets": DEFAULT_TARGETS}

    def test_with_name_flag(self):
        obj = {"id": 42, "name": "subobject"}
        result = prepare_subqueue_deploy_file_object(obj, include_name=True)
        assert result["name"] == "subobject"

    def test_preserves_previous_targets(self):
        obj = {"id": 42, "name": "x"}
        previous = {"targets": [{"id": 99}]}
        result = prepare_subqueue_deploy_file_object(obj, previous_object=previous)
        assert result["targets"] == [{"id": 99}]


@pytest.mark.asyncio
class TestFindPaths:
    async def test_find_ws_paths_for_dir(self, tmp_path):
        base = tmp_path / "src"
        await (base / "workspaces" / "WS_[1]").mkdir(parents=True)
        await (base / "workspaces" / "WS_[2]").mkdir(parents=True)
        result = await find_ws_paths_for_dir(base)
        assert len(result) == 2

    async def test_find_queue_paths_for_workspaces(self, tmp_path):
        ws_path = tmp_path / "workspaces" / "WS_[1]"
        await (ws_path / "queues" / "Q_[10]").mkdir(parents=True)
        await (ws_path / "queues" / "Q_[10]" / "queue.json").write_text("{}")
        result = await find_queue_paths_for_workspaces([ws_path])
        assert len(result) == 1
        assert result[0].name == "queue.json"

    async def test_find_rule_paths_for_dir(self, tmp_path):
        rules_dir = tmp_path / settings.RULES_DIR_NAME
        await rules_dir.mkdir(parents=True)
        await (rules_dir / "rule_[1].json").write_text("{}")
        await (rules_dir / "notrule.txt").write_text("x")
        result = await find_rule_paths_for_dir(tmp_path)
        assert len(result) == 1

    async def test_find_rule_paths_for_dir_missing(self, tmp_path):
        assert await find_rule_paths_for_dir(tmp_path) == []

    async def test_find_engine_paths_for_dir(self, tmp_path):
        engine_dir = tmp_path / "engines"
        await (engine_dir / "engine_[1]").mkdir(parents=True)
        await (engine_dir / "engine_[1]" / "engine.json").write_text("{}")
        # Also a top-level engine json (older layout)
        await (engine_dir / "flat_engine_[2].json").write_text("{}")
        result = await find_engine_paths_for_dir(tmp_path)
        assert len(result) == 2

    async def test_find_engine_field_paths_for_engine(self, tmp_path):
        engine_file = tmp_path / "engines" / "eng_[1]" / "engine.json"
        await engine_file.parent.mkdir(parents=True)
        await engine_file.write_text("{}")
        fields_dir = engine_file.parent / "engine_fields"
        await fields_dir.mkdir()
        await (fields_dir / "f_[99].json").write_text("{}")
        result = await find_engine_field_paths_for_engine(engine_file)
        assert len(result) == 1

    async def test_find_hooks_for_queues_matches_by_id(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        await hooks_dir.mkdir(parents=True)

        h1 = {
            "id": 100,
            "name": "H1",
            "url": "https://api/hooks/100",
            "type": "function",
            "events": [],
            "active": True,
            "queues": [],
            "run_after": [],
            "config": {},
            "extension_source": "custom",
            "secrets": {},
            "sideload": [],
        }
        h2 = {**h1, "id": 200, "name": "H2"}
        await write_object_to_json(hooks_dir / "H1_[100].json", h1)
        await write_object_to_json(hooks_dir / "H2_[200].json", h2)

        # Queue only references H1
        queues = [{"hooks": ["https://api/v1/hooks/100"]}]
        result = await find_hooks_for_queues(tmp_path, queues)
        assert len(result) == 1
        assert result[0]["id"] == 100

    async def test_find_hooks_for_queues_dedupes_across_queues(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        await hooks_dir.mkdir(parents=True)
        h = {"id": 7, "name": "H", "queues": [], "run_after": []}
        await write_object_to_json(hooks_dir / "H_[7].json", h)

        # Two queues reference the same hook → only returned once
        queues = [
            {"hooks": ["https://api/v1/hooks/7"]},
            {"hooks": ["https://api/v1/hooks/7"]},
        ]
        result = await find_hooks_for_queues(tmp_path, queues)
        assert len(result) == 1

    async def test_find_rules_for_queues_skips_schema_rules(self, tmp_path):
        rules_dir = tmp_path / settings.RULES_DIR_NAME
        await rules_dir.mkdir(parents=True)

        # Rule referenced by selected queue
        await write_object_to_json(
            rules_dir / "r1.json",
            {"id": 1, "name": "R1", "queues": ["https://api/v1/queues/100"]},
        )
        # Schema-based rule (deprecated) referencing the same queue → skipped
        await write_object_to_json(
            rules_dir / "r2.json",
            {"id": 2, "name": "R2", "schema": "x", "queues": ["https://api/v1/queues/100"]},
        )
        # Rule referencing an unrelated queue
        await write_object_to_json(
            rules_dir / "r3.json",
            {"id": 3, "name": "R3", "queues": ["https://api/v1/queues/999"]},
        )

        result = await find_rules_for_queues(tmp_path, [{"id": 100}])
        assert result == {1}

    async def test_find_label_paths_for_dir(self, tmp_path):
        labels_dir = tmp_path / settings.LABELS_DIR_NAME
        await labels_dir.mkdir(parents=True)
        await (labels_dir / "Done_[1].json").write_text("{}")
        await (labels_dir / "Todo_[2].json").write_text("{}")
        await (labels_dir / "notlabel.txt").write_text("x")
        result = await find_label_paths_for_dir(tmp_path)
        assert len(result) == 2

    async def test_find_label_paths_for_dir_missing(self, tmp_path):
        assert await find_label_paths_for_dir(tmp_path) == []

    async def test_find_email_template_paths_for_queue(self, tmp_path):
        queue_path = tmp_path / "workspaces" / "WS_[1]" / "queues" / "Q_[10]" / "queue.json"
        et_dir = queue_path.parent / settings.EMAIL_TEMPLATES_DIR_NAME
        await et_dir.mkdir(parents=True)
        await (et_dir / "Welcome_[100].json").write_text("{}")
        await (et_dir / "Bye_[101].json").write_text("{}")
        result = await find_email_template_paths_for_queue(queue_path)
        assert len(result) == 2

    async def test_find_email_template_paths_for_queue_missing(self, tmp_path):
        queue_path = tmp_path / "queues" / "Q_[10]" / "queue.json"
        await queue_path.parent.mkdir(parents=True)
        assert await find_email_template_paths_for_queue(queue_path) == []

    async def test_find_creatable_email_template_paths_filters_non_creatable(self, tmp_path):
        queue_path = tmp_path / "workspaces" / "WS_[1]" / "queues" / "Q_[10]" / "queue.json"
        et_dir = queue_path.parent / settings.EMAIL_TEMPLATES_DIR_NAME
        await et_dir.mkdir(parents=True)
        await write_object_to_json(et_dir / "Custom_[1].json", {"id": 1, "name": "Custom", "type": "custom"})
        await write_object_to_json(et_dir / "Rejection_[2].json", {"id": 2, "name": "Rejection", "type": "rejection"})
        await write_object_to_json(
            et_dir / "Default_[3].json", {"id": 3, "name": "Default", "type": "rejection_default"}
        )
        await write_object_to_json(
            et_dir / "NoAtt_[4].json",
            {"id": 4, "name": "NoAtt", "type": "email_with_no_processable_attachments"},
        )
        result = await find_creatable_email_template_paths([{"id": 10, "path": queue_path}])
        # custom + rejection are creatable; the two auto-created types are excluded
        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"Custom_[1].json", "Rejection_[2].json"}

    async def test_find_creatable_email_template_paths_only_selected_queues(self, tmp_path):
        # Two queues each with a creatable template; only one queue is "selected"
        for qid in (10, 20):
            et_dir = (
                tmp_path / "workspaces" / "WS_[1]" / "queues" / f"Q_[{qid}]" / settings.EMAIL_TEMPLATES_DIR_NAME
            )
            await et_dir.mkdir(parents=True)
            await write_object_to_json(
                et_dir / f"T_[{qid}].json", {"id": qid, "name": "T", "type": "custom"}
            )
        selected_queue_path = tmp_path / "workspaces" / "WS_[1]" / "queues" / "Q_[10]" / "queue.json"
        result = await find_creatable_email_template_paths([{"id": 10, "path": selected_queue_path}])
        assert len(result) == 1
        assert result[0].name == "T_[10].json"

    async def test_find_all_email_template_paths_for_dir(self, tmp_path):
        for qid in (10, 20):
            queue_dir = tmp_path / "workspaces" / "WS_[1]" / "queues" / f"Q_[{qid}]"
            et_dir = queue_dir / settings.EMAIL_TEMPLATES_DIR_NAME
            await et_dir.mkdir(parents=True)
            await (queue_dir / "queue.json").write_text("{}")
            await (et_dir / f"T_[{qid}].json").write_text("{}")
        result = await find_all_email_template_paths_for_dir(tmp_path)
        assert len(result) == 2

    async def test_find_all_email_template_paths_for_dir_missing(self, tmp_path):
        assert await find_all_email_template_paths_for_dir(tmp_path) == []


class TestPrepareEmailTemplateDeployFileObjects:
    def test_base_path_is_email_templates_dir(self):
        objects = [
            {
                "id": 100,
                "name": "Welcome",
                "path": Path("src/primary/workspaces/W_[5]/queues/Q_[1]/email_templates/Welcome_[100].json"),
            }
        ]
        result = prepare_email_template_deploy_file_objects(objects=objects)
        assert len(result) == 1
        entry = result[0]
        assert entry["id"] == 100
        assert entry["name"] == "Welcome"
        # base_path points directly at the email_templates/ dir (= path.parent)
        assert entry[settings.DEPLOY_KEY_BASE_PATH] == "src/primary/workspaces/W_[5]/queues/Q_[1]/email_templates"
        assert entry[settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS

    def test_preserves_previous_targets(self):
        objects = [
            {"id": 100, "name": "Welcome", "path": Path("a/b/c/email_templates/Welcome_[100].json")}
        ]
        previous = [{"id": 100, "targets": [{"id": 555, "attribute_override": {"subject": "kept"}}]}]
        result = prepare_email_template_deploy_file_objects(
            objects=objects, objects_in_previous_file=previous
        )
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [
            {"id": 555, "attribute_override": {"subject": "kept"}}
        ]


@pytest.mark.asyncio
class TestGetRuleDependencyObjects:
    """Labels/email templates referenced by selected rules are surfaced in the deploy file,
    tagged with `included_by_rules`, derived fresh from the rule selection."""

    async def _write_label(self, base: Path, id_: int, name: str):
        await write_object_to_json(
            base / settings.LABELS_DIR_NAME / f"{name}_[{id_}].json",
            {"id": id_, "name": name, "color": "#fff"},
        )

    async def _write_email_template(self, base: Path, id_: int, name: str, type_: str = "custom"):
        queue_dir = base / "workspaces" / "WS_[1]" / "queues" / "Q_[10]"
        await queue_dir.mkdir(parents=True, exist_ok=True)
        await (queue_dir / "queue.json").write_text("{}")
        await write_object_to_json(
            queue_dir / settings.EMAIL_TEMPLATES_DIR_NAME / f"{name}_[{id_}].json",
            {"id": id_, "name": name, "type": type_, "queue": "https://api/v1/queues/10"},
        )

    def _rule(self, id_: int, label_ids=(), email_template_ids=()):
        actions = []
        for lid in label_ids:
            actions.append({"type": "add_label", "payload": {"labels": [f"https://api/v1/labels/{lid}"]}})
        for eid in email_template_ids:
            actions.append(
                {"type": "send_email", "payload": {"email_template": f"https://api/v1/email_templates/{eid}"}}
            )
        return {"id": id_, "name": f"rule-{id_}", "actions": actions}

    async def test_derives_label_and_email_template_entries(self, tmp_path):
        await self._write_label(tmp_path, 100, "Done")
        await self._write_email_template(tmp_path, 500, "Welcome")
        rule = self._rule(7000, label_ids=[100], email_template_ids=[500])

        labels, ets = await get_rule_dependency_objects(selected_rules=[rule], source_path=tmp_path)

        assert [entry["id"] for entry in labels] == [100]
        assert labels[0]["included_by_rules"] == [7000]
        assert labels[0]["name"] == "Done"
        assert [entry["id"] for entry in ets] == [500]
        assert ets[0]["included_by_rules"] == [7000]
        assert ets[0][settings.DEPLOY_KEY_BASE_PATH].endswith("Q_[10]/email_templates")

    async def test_non_creatable_email_template_excluded(self, tmp_path):
        await self._write_email_template(tmp_path, 501, "Reject", type_="rejection_default")
        rule = self._rule(7000, email_template_ids=[501])

        _, ets = await get_rule_dependency_objects(selected_rules=[rule], source_path=tmp_path)
        assert ets == []

    async def test_manual_pick_excluded(self, tmp_path):
        await self._write_label(tmp_path, 100, "Done")
        rule = self._rule(7000, label_ids=[100])

        labels, _ = await get_rule_dependency_objects(
            selected_rules=[rule], source_path=tmp_path, exclude_label_ids={100}
        )
        assert labels == []

    async def test_multiple_rules_listed_in_tag(self, tmp_path):
        await self._write_label(tmp_path, 100, "Done")
        rules = [self._rule(7000, label_ids=[100]), self._rule(8000, label_ids=[100])]

        labels, _ = await get_rule_dependency_objects(selected_rules=rules, source_path=tmp_path)
        assert labels[0]["included_by_rules"] == [7000, 8000]

    async def test_schema_rule_skipped(self, tmp_path):
        await self._write_label(tmp_path, 100, "Done")
        rule = {**self._rule(7000, label_ids=[100]), "schema": "https://api/v1/schemas/1"}

        labels, _ = await get_rule_dependency_objects(selected_rules=[rule], source_path=tmp_path)
        assert labels == []

    async def test_missing_local_file_is_skipped(self, tmp_path):
        # Rule references label 999 that has no local file → not listed (auto-loads at deploy)
        rule = self._rule(7000, label_ids=[999])
        labels, _ = await get_rule_dependency_objects(selected_rules=[rule], source_path=tmp_path)
        assert labels == []

    async def test_preserves_previous_targets(self, tmp_path):
        await self._write_label(tmp_path, 100, "Done")
        rule = self._rule(7000, label_ids=[100])
        previous = [{"id": 100, "included_by_rules": [7000], "targets": [{"id": 777}]}]

        labels, _ = await get_rule_dependency_objects(
            selected_rules=[rule], source_path=tmp_path, previous_deploy_file_labels=previous
        )
        assert labels[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 777}]


class TestCollectRuleDependencyIds:
    def _rule(self, id_, label_ids=(), email_template_ids=()):
        actions = [
            {"type": "add_label", "payload": {"labels": [f"https://api/v1/labels/{lid}" for lid in label_ids]}}
        ]
        for eid in email_template_ids:
            actions.append(
                {"type": "send_email", "payload": {"email_template": f"https://api/v1/email_templates/{eid}"}}
            )
        return {"id": id_, "actions": actions}

    def test_maps_labels_and_email_templates_to_rules(self):
        rules = [self._rule(55, label_ids=[100], email_template_ids=[500]), self._rule(60, label_ids=[100])]
        label_ids, et_ids = collect_rule_dependency_ids(rules)
        assert label_ids == {100: {55, 60}}
        assert et_ids == {500: {55}}

    def test_schema_rule_ignored(self):
        rule = {**self._rule(55, label_ids=[100]), "schema": "https://api/v1/schemas/1"}
        label_ids, et_ids = collect_rule_dependency_ids([rule])
        assert label_ids == {}
        assert et_ids == {}


@pytest.mark.asyncio
class TestGetLabelsFromUser:
    """The selection menu surfaces rule-required labels as mandatory and tags them."""

    async def _write_label(self, base: Path, id_: int, name: str):
        await write_object_to_json(
            base / settings.LABELS_DIR_NAME / f"{name}_[{id_}].json",
            {"id": id_, "name": name, "color": "#fff"},
        )

    async def test_rule_required_label_is_tagged_even_when_also_manually_selected(self, tmp_path):
        # Label 100 was manually picked previously AND is referenced by rule 55.
        # Non-interactive update (manual selection present) skips the prompt.
        await self._write_label(tmp_path, 100, "Export Completed")
        previous = [{"id": 100, "name": "Export Completed", "targets": [{"id": 14993}]}]

        result = await get_labels_from_user(
            source_path=tmp_path,
            interactive=False,
            previous_deploy_file_labels=previous,
            rule_required_ids={100: {55}},
        )

        assert len(result) == 1
        assert result[0]["id"] == 100
        assert result[0]["included_by_rules"] == [55]
        # Existing target is preserved
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 14993}]
        # included_by_rules is ordered before targets for readability
        keys = list(result[0].keys())
        assert keys.index("included_by_rules") < keys.index(settings.DEPLOY_KEY_TARGETS)

    async def test_manual_label_not_required_by_rule_has_no_tag(self, tmp_path):
        await self._write_label(tmp_path, 100, "Manual")
        previous = [{"id": 100, "name": "Manual", "targets": [{"id": 1}]}]

        result = await get_labels_from_user(
            source_path=tmp_path,
            interactive=False,
            previous_deploy_file_labels=previous,
            rule_required_ids={},
        )
        assert "included_by_rules" not in result[0]

    async def test_stale_tag_is_cleared_when_rule_removed(self, tmp_path):
        # Label was rule-required before but the rule is no longer selected.
        await self._write_label(tmp_path, 100, "WasRuleBound")
        previous = [{"id": 100, "name": "WasRuleBound", "included_by_rules": [55], "targets": [{"id": 1}]}]

        # Not rule-required now, and not a manual pick → not preselected → drops out.
        result = await get_labels_from_user(
            source_path=tmp_path,
            interactive=False,
            previous_deploy_file_labels=previous,
            rule_required_ids={},
        )
        # The previously rule-bound label is no longer preselected (manual_label_ids is empty),
        # so the non-interactive path returns nothing for it.
        assert result == []


@pytest.mark.asyncio
class TestGetEmailTemplatesFromUser:
    """Email templates share the same rule-dependency selection logic as labels."""

    async def _write_email_template(self, base: Path, id_: int, name: str, type_: str = "custom"):
        queue_dir = base / "workspaces" / "WS_[1]" / "queues" / "Q_[10]"
        await queue_dir.mkdir(parents=True, exist_ok=True)
        await (queue_dir / "queue.json").write_text("{}")
        await write_object_to_json(
            queue_dir / settings.EMAIL_TEMPLATES_DIR_NAME / f"{name}_[{id_}].json",
            {"id": id_, "name": name, "type": type_, "queue": "https://api/v1/queues/10"},
        )
        return queue_dir / "queue.json"

    async def test_rule_required_email_template_is_tagged_even_when_manually_selected(self, tmp_path):
        queue_json = await self._write_email_template(tmp_path, 500, "Welcome")
        selected_queues = [{"id": 10, "path": queue_json}]
        previous = [{"id": 500, "name": "Welcome", "targets": [{"id": 999}]}]

        result = await get_email_templates_from_user(
            selected_queues=selected_queues,
            interactive=False,
            previous_deploy_file_email_templates=previous,
            rule_required_ids={500: {55}},
        )

        assert len(result) == 1
        assert result[0]["id"] == 500
        assert result[0]["included_by_rules"] == [55]
        # Existing target preserved and base_path points at the queue's email_templates dir
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 999}]
        assert result[0][settings.DEPLOY_KEY_BASE_PATH].endswith("Q_[10]/email_templates")
        keys = list(result[0].keys())
        assert keys.index("included_by_rules") < keys.index(settings.DEPLOY_KEY_TARGETS)

    async def test_manual_email_template_not_required_by_rule_has_no_tag(self, tmp_path):
        queue_json = await self._write_email_template(tmp_path, 500, "Welcome")
        selected_queues = [{"id": 10, "path": queue_json}]
        previous = [{"id": 500, "name": "Welcome", "targets": [{"id": 1}]}]

        result = await get_email_templates_from_user(
            selected_queues=selected_queues,
            interactive=False,
            previous_deploy_file_email_templates=previous,
            rule_required_ids={},
        )
        assert "included_by_rules" not in result[0]


@pytest.mark.asyncio
class TestPrepareChoices:
    async def test_returns_choices_sorted_by_id(self, tmp_path):
        await write_object_to_json(tmp_path / "a.json", {"id": 5, "name": "Alpha"})
        await write_object_to_json(tmp_path / "b.json", {"id": 1, "name": "Beta"})
        await write_object_to_json(tmp_path / "c.json", {"id": 3, "name": "Gamma"})
        result = await prepare_choices([tmp_path / "a.json", tmp_path / "b.json", tmp_path / "c.json"])
        ids = [c.value["id"] for c in result]
        assert ids == [1, 3, 5]

    async def test_skips_objects_without_id(self, tmp_path):
        await write_object_to_json(tmp_path / "a.json", {"id": 1, "name": "Has-ID"})
        await write_object_to_json(tmp_path / "b.json", {"name": "No-ID"})
        result = await prepare_choices([tmp_path / "a.json", tmp_path / "b.json"])
        assert len(result) == 1

    async def test_preselect_specific_ids(self, tmp_path):
        await write_object_to_json(tmp_path / "a.json", {"id": 1, "name": "A"})
        await write_object_to_json(tmp_path / "b.json", {"id": 2, "name": "B"})
        result = await prepare_choices(
            [tmp_path / "a.json", tmp_path / "b.json"], preselected_ids=[1]
        )
        # Sorted by id, so index 0 is the preselected one
        assert result[0].checked is True
        assert result[1].checked is False

    async def test_preselect_all(self, tmp_path):
        await write_object_to_json(tmp_path / "a.json", {"id": 1, "name": "A"})
        await write_object_to_json(tmp_path / "b.json", {"id": 2, "name": "B"})
        result = await prepare_choices(
            [tmp_path / "a.json", tmp_path / "b.json"], preselect_all=True
        )
        assert all(c.checked for c in result)

    async def test_disabled_reasons_force_checked_and_disabled(self, tmp_path):
        await write_object_to_json(tmp_path / "a.json", {"id": 1, "name": "A"})
        await write_object_to_json(tmp_path / "b.json", {"id": 2, "name": "B"})
        result = await prepare_choices(
            [tmp_path / "a.json", tmp_path / "b.json"],
            disabled_reasons={2: "required by rule(s) 55"},
        )
        by_id = {c.value["id"]: c for c in result}
        # The rule-required one is forced checked and disabled (can't be unchecked)
        assert by_id[2].checked is True
        assert by_id[2].disabled == "required by rule(s) 55"
        # The other one is untouched
        assert by_id[1].checked is False
        assert by_id[1].disabled is None


class TestAddMultiTargetsToObject:
    def test_appends_default_targets(self):
        obj = {"id": 1}
        add_multi_targets_to_object(obj, target_count="2")
        assert len(obj[settings.DEPLOY_KEY_TARGETS]) == 2
        assert obj[settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS * 2

    def test_preserves_previous_targets(self):
        obj = {settings.DEPLOY_KEY_TARGETS: [{"id": 7}]}
        add_multi_targets_to_object(obj, target_count="1")
        # Previous + 1 new default
        assert len(obj[settings.DEPLOY_KEY_TARGETS]) == 2
        assert obj[settings.DEPLOY_KEY_TARGETS][0] == {"id": 7}

    def test_zero_count_leaves_targets_unchanged(self):
        obj = {settings.DEPLOY_KEY_TARGETS: [{"id": 5}]}
        add_multi_targets_to_object(obj, target_count="0")
        assert obj[settings.DEPLOY_KEY_TARGETS] == [{"id": 5}]


class TestAddOverrideToDeployFileObject:
    def test_writes_override_into_each_target(self):
        obj = {settings.DEPLOY_KEY_TARGETS: [{"id": 1}, {"id": 2}]}
        override = AttributeOverride(object_types=["queues"], attribute="name", value="PROD")
        add_override_to_deploy_file_object(override, obj)
        for target in obj[settings.DEPLOY_KEY_TARGETS]:
            assert target[settings.DEPLOY_KEY_OVERRIDES]["name"] == "PROD"

    def test_merges_with_existing_overrides(self):
        obj = {
            settings.DEPLOY_KEY_TARGETS: [
                {"id": 1, settings.DEPLOY_KEY_OVERRIDES: {"existing": "X"}}
            ]
        }
        override = AttributeOverride(object_types=["queues"], attribute="name", value="PROD")
        add_override_to_deploy_file_object(override, obj)
        target = obj[settings.DEPLOY_KEY_TARGETS][0]
        assert target[settings.DEPLOY_KEY_OVERRIDES] == {"existing": "X", "name": "PROD"}


class TestAddOverrideToDeployFileObjects:
    def test_applies_to_each_object_in_each_type(self):
        deploy_file = {
            "queues": [
                {settings.DEPLOY_KEY_TARGETS: [{"id": 1}]},
                {settings.DEPLOY_KEY_TARGETS: [{"id": 2}]},
            ],
            "hooks": [{settings.DEPLOY_KEY_TARGETS: [{"id": 3}]}],
        }
        override = AttributeOverride(object_types=["queues", "hooks"], attribute="name", value="PROD")
        add_override_to_deploy_file_objects(override, deploy_file)
        for queue in deploy_file["queues"]:
            assert queue[settings.DEPLOY_KEY_TARGETS][0][settings.DEPLOY_KEY_OVERRIDES]["name"] == "PROD"
        assert deploy_file["hooks"][0][settings.DEPLOY_KEY_TARGETS][0][settings.DEPLOY_KEY_OVERRIDES]["name"] == "PROD"

    def test_skips_unknown_object_type(self):
        deploy_file = {"queues": [{settings.DEPLOY_KEY_TARGETS: [{"id": 1}]}]}
        override = AttributeOverride(object_types=["nonexistent"], attribute="name", value="PROD")
        # Must not raise; just warns
        add_override_to_deploy_file_objects(override, deploy_file)
        assert deploy_file == {"queues": [{settings.DEPLOY_KEY_TARGETS: [{"id": 1}]}]}


class TestAddTargetsForObjects:
    def test_copies_target_ids_from_mapping(self):
        deploy_objects = [{"id": 1, settings.DEPLOY_KEY_TARGETS: [{"id": None}]}]
        mapping_objects = [{"id": 1, "targets": [{"target_id": 999}]}]
        add_targets_for_objects(mapping_objects, deploy_objects, "queues")
        assert deploy_objects[0][settings.DEPLOY_KEY_TARGETS][0]["id"] == 999

    def test_preserves_existing_deploy_target_id(self):
        # Already has a deploy target id → keep it
        deploy_objects = [{"id": 1, settings.DEPLOY_KEY_TARGETS: [{"id": 42}]}]
        mapping_objects = [{"id": 1, "targets": [{"target_id": 999}]}]
        add_targets_for_objects(mapping_objects, deploy_objects, "queues")
        assert deploy_objects[0][settings.DEPLOY_KEY_TARGETS][0]["id"] == 42

    def test_merges_attribute_overrides(self):
        deploy_objects = [
            {
                "id": 1,
                settings.DEPLOY_KEY_TARGETS: [{"id": None, "attribute_override": {"keep": "yes"}}],
            }
        ]
        mapping_objects = [
            {"id": 1, "targets": [{"target_id": 999, "attribute_override": {"from_mapping": "x"}}]}
        ]
        add_targets_for_objects(mapping_objects, deploy_objects, "queues")
        assert deploy_objects[0][settings.DEPLOY_KEY_TARGETS][0]["attribute_override"] == {
            "from_mapping": "x",
            "keep": "yes",
        }

    def test_skips_objects_without_mapping(self):
        deploy_objects = [{"id": 1, settings.DEPLOY_KEY_TARGETS: [{"id": 42}]}]
        mapping_objects = [{"id": 999, "targets": []}]
        # Original should be untouched (function continues for unknown ids)
        before = deepcopy(deploy_objects)
        add_targets_for_objects(mapping_objects, deploy_objects, "queues")
        assert deploy_objects == before


class TestAddTargetsFromMapping:
    def test_propagates_org_target_id(self):
        mapping = {
            "organization": {
                "targets": [{"target_id": 12345}],
                "workspaces": [],
                "hooks": [],
                "schemas": [],
            }
        }
        deploy_file = {
            settings.DEPLOY_KEY_WORKSPACES: [],
            settings.DEPLOY_KEY_QUEUES: [],
            settings.DEPLOY_KEY_HOOKS: [],
        }
        add_targets_from_mapping(mapping, deploy_file)
        assert deploy_file[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] == 12345

    def test_full_propagation(self):
        mapping = {
            "organization": {
                "targets": [{"target_id": 1}],
                "workspaces": [
                    {
                        "id": 10,
                        "targets": [{"target_id": 100}],
                        "queues": [
                            {
                                "id": 20,
                                "targets": [{"target_id": 200}],
                                "inbox": {"id": 30, "targets": [{"target_id": 300}]},
                            }
                        ],
                    }
                ],
                "hooks": [{"id": 40, "targets": [{"target_id": 400}]}],
                "schemas": [{"id": 50, "targets": [{"target_id": 500}]}],
            }
        }
        deploy_file = {
            settings.DEPLOY_KEY_WORKSPACES: [{"id": 10, settings.DEPLOY_KEY_TARGETS: [{"id": None}]}],
            settings.DEPLOY_KEY_QUEUES: [
                {
                    "id": 20,
                    settings.DEPLOY_KEY_TARGETS: [{"id": None}],
                    settings.DEPLOY_KEY_INBOX: {"id": 30, settings.DEPLOY_KEY_TARGETS: [{"id": None}]},
                    settings.DEPLOY_KEY_SCHEMA: {"id": 50, settings.DEPLOY_KEY_TARGETS: [{"id": None}]},
                }
            ],
            settings.DEPLOY_KEY_HOOKS: [{"id": 40, settings.DEPLOY_KEY_TARGETS: [{"id": None}]}],
        }
        add_targets_from_mapping(mapping, deploy_file)
        assert deploy_file[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] == 1
        assert deploy_file[settings.DEPLOY_KEY_WORKSPACES][0][settings.DEPLOY_KEY_TARGETS][0]["id"] == 100
        queue = deploy_file[settings.DEPLOY_KEY_QUEUES][0]
        assert queue[settings.DEPLOY_KEY_TARGETS][0]["id"] == 200
        assert queue[settings.DEPLOY_KEY_INBOX][settings.DEPLOY_KEY_TARGETS][0]["id"] == 300
        assert queue[settings.DEPLOY_KEY_SCHEMA][settings.DEPLOY_KEY_TARGETS][0]["id"] == 500
        assert deploy_file[settings.DEPLOY_KEY_HOOKS][0][settings.DEPLOY_KEY_TARGETS][0]["id"] == 400


class TestPrepareEngineFieldsForDeploy:
    def test_basic_shape(self):
        fields = [{"id": 1, "name": "F1"}, {"id": 2, "name": "F2"}]
        result = prepare_engine_fields_for_deploy(fields)
        assert len(result) == 2
        for f in result:
            assert settings.DEPLOY_KEY_TARGETS in f
            assert f[settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS

    def test_preserves_previous_targets(self):
        fields = [{"id": 1, "name": "F1"}]
        previous = [{"id": 1, settings.DEPLOY_KEY_TARGETS: [{"id": 99}]}]
        result = prepare_engine_fields_for_deploy(fields, previous_engine_fields=previous)
        assert result[0][settings.DEPLOY_KEY_TARGETS] == [{"id": 99}]

    def test_unknown_previous_id_falls_back_to_default(self):
        fields = [{"id": 5, "name": "F"}]
        previous = [{"id": 999, settings.DEPLOY_KEY_TARGETS: [{"id": 1}]}]
        result = prepare_engine_fields_for_deploy(fields, previous_engine_fields=previous)
        assert result[0][settings.DEPLOY_KEY_TARGETS] == DEFAULT_TARGETS
