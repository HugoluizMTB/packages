import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "files" / "devmachine-infer"
loader = SourceFileLoader("devmachine_infer", str(MODULE_PATH))
spec = importlib.util.spec_from_loader("devmachine_infer", loader)
devmachine_infer = importlib.util.module_from_spec(spec)
sys.modules["devmachine_infer"] = devmachine_infer
loader.exec_module(devmachine_infer)


def test_cwd_for_session(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return True, "/home/alice/dev/dash\n"

    import devmachine_infer as m
    monkeypatch.setattr(m, "run", fake_run)
    assert m.cwd_for_session("lin-7307") == "/home/alice/dev/dash"
    assert "display" in calls[0] and "lin-7307" in calls[0]


def test_cwd_for_session_no_tmux(monkeypatch):
    import devmachine_infer as m

    def fake_run(cmd, **kw):
        return False, ""

    monkeypatch.setattr(m, "run", fake_run)
    assert m.cwd_for_session("nope") is None


def test_latest_todos():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "TodoWrite",
             "input": {"todos": [{"content": "a", "status": "completed"}]}}]}},
        {"message": {"content": [
            {"type": "tool_use", "name": "TodoWrite",
             "input": {"todos": [
                 {"content": "a", "status": "completed"},
                 {"content": "b", "status": "in_progress"},
                 {"content": "c", "status": "pending"}]}}]}},
    ]
    todos = m.latest_todos(events)
    assert [t["state"] for t in todos] == ["done", "active", "pending"]
    assert todos[1]["text"] == "b"


def test_latest_todos_empty():
    import devmachine_infer as m
    assert m.latest_todos([]) == []
    assert m.latest_todos([{"message": {"content": "plain string"}}]) == []


def test_find_transcript_auto_includes_worktrees(monkeypatch, tmp_path):
    import devmachine_infer as m
    import os

    projects = tmp_path / "projects"
    repo = tmp_path / "dash"
    slug = str(repo.resolve()).replace("/", "-")
    (projects / slug).mkdir(parents=True)
    (projects / f"{slug}--claude-worktrees-da-x").mkdir()

    older = projects / slug / "a.jsonl"
    newer = projects / f"{slug}--claude-worktrees-da-x" / "b.jsonl"
    older.write_text("{}\n")
    newer.write_text("{}\n")
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    monkeypatch.setattr(m, "PROJECTS_DIR", projects)
    assert m.find_transcript("auto", repo) == newer


def test_find_transcript_auto_ignores_sibling_project(monkeypatch, tmp_path):
    import devmachine_infer as m

    projects = tmp_path / "projects"
    repo = tmp_path / "dash"
    slug = str(repo.resolve()).replace("/", "-")
    (projects / slug).mkdir(parents=True)
    (projects / f"{slug}board").mkdir()
    (projects / f"{slug}board" / "other.jsonl").write_text("{}\n")

    monkeypatch.setattr(m, "PROJECTS_DIR", projects)
    assert m.find_transcript("auto", repo) is None


def _created(task_id, subject):
    return {"toolUseResult": {"task": {"id": task_id, "subject": subject}}}


def _updated(task_id, to, success=True):
    return {"toolUseResult": {"success": success, "taskId": task_id,
                              "updatedFields": ["status"],
                              "statusChange": {"from": "pending", "to": to}}}


def test_latest_tasks():
    import devmachine_infer as m
    events = [
        _created("1", "first"),
        _created("2", "second"),
        _created("3", "third"),
        _updated("1", "completed"),
        _updated("2", "in_progress"),
    ]
    tasks = m.latest_tasks(events)
    assert [t["text"] for t in tasks] == ["first", "second", "third"]
    assert [t["state"] for t in tasks] == ["done", "active", "pending"]


def test_latest_tasks_ignores_rejected_create():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "TaskCreate",
             "input": {"tasks": '[{"content": "a", "status": "pending"}]'}}]},
         "toolUseResult": "InputValidationError: expected string"},
        _created("1", "real one"),
    ]
    assert m.latest_tasks(events) == [{"text": "real one", "state": "pending"}]


def test_latest_tasks_ignores_failed_update():
    import devmachine_infer as m
    events = [_created("1", "a"), _updated("1", "completed", success=False),
              _updated("9", "completed")]
    assert m.latest_tasks(events) == [{"text": "a", "state": "pending"}]


def test_latest_todos_prefers_tasks_over_todo_write():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "TodoWrite",
             "input": {"todos": [{"content": "old", "status": "pending"}]}}]}},
        _created("1", "new"),
    ]
    assert [t["text"] for t in m.latest_todos(events)] == ["new"]


def test_plan_prefers_todos():
    import devmachine_infer as m
    todos = [{"text": "x", "state": "active"}]
    plan = m.build_plan(todos=todos)
    assert plan["source"] == "todos" and plan["done"] == 0 and plan["total"] == 1


def test_plan_none_when_no_todos():
    import devmachine_infer as m
    assert m.build_plan(todos=[]) is None


def test_map_prs_and_links():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 5, "url": "https://github.com/o/r/pull/5",
               "state": "open", "isDraft": False, "title": "t",
               "ci": "pass", "review": "APPROVED"}]
    links_in = [{"url": "https://linear.app/x/issue/LIN-9"},
                {"url": "https://acme.atlassian.net/browse/PROJ-451"},
                {"url": "https://example.com/a"}]
    prs = m.map_prs(github)
    assert prs[0] == {"number": 5, "repo": "o/r", "title": "t",
                      "url": "https://github.com/o/r/pull/5",
                      "ci": "pass", "review": "approved", "state": "open"}
    links = m.map_links(links_in)
    assert {"url": "https://linear.app/x/issue/LIN-9",
            "label": "LIN-9", "kind": "linear"} in links
    assert {"url": "https://acme.atlassian.net/browse/PROJ-451",
            "label": "PROJ-451", "kind": "atlassian"} in links
    assert {"url": "https://example.com/a",
            "label": "example.com/a", "kind": "example"} in links


def test_map_prs_draft_state():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 1, "url": "u", "state": "open",
               "isDraft": True, "title": "t", "ci": "none", "review": None}]
    prs = m.map_prs(github)
    assert prs[0]["state"] == "draft"
    assert prs[0]["review"] == "none"


def test_what_github_answers_reaches_the_panel_with_the_words_it_uses():
    import devmachine_infer as m
    for decision, word in [("APPROVED", "approved"), ("CHANGES_REQUESTED", "changes"),
                           ("REVIEW_REQUIRED", "required"), (None, "none")]:
        resolved, *_ = m.parse_batch(_reply([_node(review=decision)]), [_entry(5)])
        pr = m.map_prs([{**_entry(5), **resolved["github.com|o/r#5"]}])[0]
        assert pr["review"] == word, decision


def test_map_prs_keeps_merged_state_and_threads():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 9, "url": "u", "state": "merged", "isDraft": False,
               "title": "t", "ci": "pass", "review": "APPROVED", "threads": 2}]
    prs = m.map_prs(github)
    assert prs[0]["state"] == "merged"
    assert prs[0]["threads"] == 2


def test_map_prs_drops_empty_thread_count():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 9, "url": "u", "state": "open", "isDraft": False,
               "title": "t", "ci": "none", "review": None, "threads": None}]
    assert "threads" not in m.map_prs(github)[0]


def test_build_context_linear_label_is_key(monkeypatch, tmp_path):
    import devmachine_infer as m

    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        '{"message": {"content": [{"type": "text", "text": '
        '"see LIN-9 https://linear.app/example/issue/LIN-9"}]}}\n'
    )

    monkeypatch.setattr(m, "cwd_for_session", lambda session: str(tmp_path))
    monkeypatch.setattr(m, "find_transcript", lambda session, project: transcript)
    monkeypatch.setattr(m, "default_repo_of", lambda project: None)
    monkeypatch.setattr(m, "collect_plans", lambda project, touched_md: [])

    ctx = m.build_context("sess", None, resolve=False)
    linear_links = [l for l in ctx["links"] if l["kind"] == "linear"]
    assert len(linear_links) == 1
    assert linear_links[0]["label"] == "LIN-9"


def test_build_context_without_a_session_uses_the_project(monkeypatch, tmp_path):
    import devmachine_infer as m

    def boom(session):
        raise AssertionError("tmux must not be asked when no session is given")

    monkeypatch.setattr(m, "cwd_for_session", boom)
    monkeypatch.setattr(m, "find_transcript", lambda mode, proj: None)
    ctx = m.build_context(None, str(tmp_path), resolve=False)
    assert ctx["cwd"] == str(tmp_path)
    assert ctx["isClaude"] is False


def test_build_context_no_transcript(monkeypatch, tmp_path):
    import devmachine_infer as m

    monkeypatch.setattr(m, "cwd_for_session", lambda session: str(tmp_path))
    monkeypatch.setattr(m, "find_transcript", lambda session, project: None)

    ctx = m.build_context("no-such-session", None, resolve=False)
    assert ctx["isClaude"] is False
    assert ctx["cwd"] == str(tmp_path)
    assert ctx["plan"] is None
    assert ctx["prs"] == []
    assert ctx["links"] == []
    assert ctx["agents"] == []
    assert "updatedAt" in ctx


def test_build_context_with_transcript(monkeypatch, tmp_path):
    import devmachine_infer as m

    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        '{"message": {"content": [{"type": "text", "text": '
        '"see https://github.com/o/r/pull/5 and LIN-9 https://linear.app/example/issue/LIN-9 '
        'and https://example.com/a"}]}}\n'
        '{"message": {"content": [{"type": "tool_use", "name": "TodoWrite", '
        '"input": {"todos": [{"content": "do thing", "status": "in_progress"}]}}]}}\n'
    )

    monkeypatch.setattr(m, "cwd_for_session", lambda session: str(tmp_path))
    monkeypatch.setattr(m, "find_transcript", lambda session, project: transcript)
    monkeypatch.setattr(m, "default_repo_of", lambda project: None)
    monkeypatch.setattr(m, "collect_plans", lambda project, touched_md: [])

    ctx = m.build_context("sess", None, resolve=False)
    assert ctx["isClaude"] is True
    assert ctx["plan"]["source"] == "todos"
    assert len(ctx["prs"]) == 1
    assert ctx["prs"][0]["repo"] == "o/r"
    assert any(l["kind"] == "linear" and l["label"] == "LIN-9" for l in ctx["links"])
    assert any(l["kind"] == "example" for l in ctx["links"])
    assert ctx["agents"] == []


def test_background_task_ends_with_its_notification_attachment():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Bash",
             "input": {"description": "Apply the caddy role"}}]}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
    ]
    assert [s["label"] for s in m.extract_background(events)["shells"]] == [
        "Apply the caddy role"]

    events.append({
        "type": "attachment",
        "attachment": {"type": "queued_command", "commandMode": "task-notification",
                       "prompt": "<task-notification> <task-id>bg1</task-id> done"},
    })
    assert m.extract_background(events)["shells"] == []


def test_background_task_ends_with_current_text_notification_attachment():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Bash",
             "input": {"description": "Run the checks"}}]}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
        {"type": "attachment",
         "attachment": {"type": "task_notification",
                        "text": "<task-notification> <task-id>bg1</task-id> done"}},
    ]
    assert m.extract_background(events)["shells"] == []


def test_background_task_ends_with_task_output_result():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Bash",
             "input": {"description": "Run the checks"}}]}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu2"}]},
         "toolUseResult": {"task_id": "bg1", "task_type": "local_bash",
                           "message": "Task completed"}},
    ]
    assert m.extract_background(events)["shells"] == []


def test_a_notification_for_another_task_leaves_the_shell_running():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"description": "Wait"}}]}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
        {"type": "attachment",
         "attachment": {"prompt": "<task-notification> <task-id>other</task-id>"}},
    ]
    assert len(m.extract_background(events)["shells"]) == 1


def test_a_background_task_without_notification_goes_stale():
    import devmachine_infer as m
    events = [
        {"timestamp": "2026-09-16T01:00:00.000Z",
         "message": {"content": [
             {"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"description": "Wait"}}]}},
        {"timestamp": "2026-09-16T01:00:01.000Z",
         "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
        {"timestamp": "2026-09-16T05:00:00.000Z", "message": {"content": []}},
    ]
    assert len(m.extract_background(events)["shells"]) == 1

    events.append({"timestamp": "2026-09-16T09:00:00.000Z", "message": {"content": []}})
    assert m.extract_background(events)["shells"] == []


def test_an_event_without_timestamps_is_never_stale():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"description": "Wait"}}]}},
        {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
         "toolUseResult": {"backgroundTaskId": "bg1"}},
    ]
    assert len(m.extract_background(events)["shells"]) == 1


def test_extract_agents_running():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "Task", "id": "tu_1",
             "input": {"description": "Audit ship readiness", "subagent_type": "fork",
                       "prompt": "long prompt text here"}}]}},
    ]
    agents = m.extract_background(events)["agents"]
    assert agents == [{"label": "Audit ship readiness", "status": "running"}]


def test_extract_agents_completed():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "Task", "id": "tu_1",
             "input": {"description": "Audit ship readiness"}}]}},
        {"message": {"content": [
            {"type": "tool_result", "tool_use_id": "tu_1", "content": "done"}]}},
    ]
    assert m.extract_background(events)["agents"] == []


def test_extract_agents_label_fallback():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "Agent", "id": "tu_2",
             "input": {"subagent_type": "general-purpose"}}]}},
    ]
    agents = m.extract_background(events)["agents"]
    assert agents == [{"label": "general-purpose", "status": "running"}]

def _user_event(text):
    return [{"timestamp": "2026-01-01T00:00:00Z",
             "message": {"role": "user", "content": text}}]


def test_gh_command_uses_the_repo_flag_not_the_session_repo():
    refs = devmachine_infer.extract_refs(
        _user_event("gh pr view 4242 -R acme/engineering"), "acme/dash")
    assert list(refs["github"]) == ["acme/engineering#4242"]
    assert refs["github"]["acme/engineering#4242"]["url"] == (
        "https://github.com/acme/engineering/pull/4242")


def test_gh_command_reads_the_repo_flag_before_the_number():
    refs = devmachine_infer.extract_refs(
        _user_event("gh pr view --repo acme/engineering 4242"), "acme/dash")
    assert list(refs["github"]) == ["acme/engineering#4242"]


def test_gh_command_without_a_repo_flag_falls_back_to_the_session_repo():
    refs = devmachine_infer.extract_refs(_user_event("gh pr checks 77"), "acme/dash")
    assert list(refs["github"]) == ["acme/dash#77"]


def test_gh_command_without_a_number_is_ignored():
    refs = devmachine_infer.extract_refs(_user_event("gh pr list"), "acme/dash")
    assert refs["github"] == {}


def _bash_launch(tool_use_id, bg_id, description, command="sleep 1"):
    return [
        {"message": {"content": [
            {"type": "tool_use", "id": tool_use_id, "name": "Bash",
             "input": {"command": command, "description": description,
                       "run_in_background": True}}]}},
        {"message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_use_id,
             "content": f"Command running in background with ID: {bg_id}."}]},
         "toolUseResult": {"stdout": "", "stderr": "", "backgroundTaskId": bg_id}},
    ]


def test_extract_shells_running():
    import devmachine_infer as m
    events = _bash_launch("tu_1", "b1abc", "Watch CI to completion")
    bg = m.extract_background(events)
    assert bg["shells"] == [{"label": "Watch CI to completion", "status": "running"}]
    assert bg["monitors"] == [] and bg["agents"] == []


def test_extract_shells_done_by_notification():
    import devmachine_infer as m
    events = _bash_launch("tu_1", "b1abc", "Watch CI to completion")
    events.append({"content": "<task-notification>\n<task-id>b1abc</task-id>\n"
                              "<status>completed</status>\n</task-notification>"})
    assert m.extract_background(events)["shells"] == []


def test_extract_shells_falls_back_to_command():
    import devmachine_infer as m
    events = _bash_launch("tu_1", "b2xyz", "", command="ansible-playbook site.yml\nsecond line")
    assert m.extract_background(events)["shells"] == [
        {"label": "ansible-playbook site.yml", "status": "running"}]


def test_build_context_lists_shells_with_agents(monkeypatch, tmp_path):
    import devmachine_infer as m
    import json as _json

    transcript = tmp_path / "session.jsonl"
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "Task", "id": "tu_agent",
             "input": {"description": "Audit ship readiness", "subagent_type": "fork"}}]}},
    ] + _bash_launch("tu_1", "b3run", "Deploy the thing")
    transcript.write_text("".join(_json.dumps(e) + "\n" for e in events))

    monkeypatch.setattr(m, "cwd_for_session", lambda session: str(tmp_path))
    monkeypatch.setattr(m, "find_transcript", lambda session, project: transcript)
    monkeypatch.setattr(m, "default_repo_of", lambda project: None)

    ctx = m.build_context("sess", None, resolve=False)
    assert [a["label"] for a in ctx["agents"]] == ["Audit ship readiness"]
    assert [s["label"] for s in ctx["shells"]] == ["Deploy the thing"]
    assert ctx["monitors"] == []


def test_build_context_merges_refs_across_sessions(monkeypatch, tmp_path):
    import devmachine_infer as m
    import json as _json
    import os

    projects = tmp_path / "projects"
    repo = tmp_path / "dash"
    repo.mkdir()
    slug = str(repo.resolve()).replace("/", "-")
    (projects / slug).mkdir(parents=True)
    (projects / f"{slug}--claude-worktrees-da-x").mkdir()

    with_prs = projects / slug / "old.jsonl"
    with_prs.write_text(_json.dumps({"message": {"content": [
        {"type": "text", "text": "https://github.com/o/r/pull/7 and LIN-4 "
                                 "https://linear.app/example/issue/LIN-4"}]}}) + "\n")

    with_tasks = projects / f"{slug}--claude-worktrees-da-x" / "new.jsonl"
    with_tasks.write_text(_json.dumps(_created("1", "worktree task")) + "\n")

    now = __import__("time").time()
    os.utime(with_prs, (now - 20, now - 20))
    os.utime(with_tasks, (now - 10, now - 10))

    monkeypatch.setattr(m, "PROJECTS_DIR", projects)
    monkeypatch.setattr(m, "cwd_for_session", lambda session: str(repo))
    monkeypatch.setattr(m, "default_repo_of", lambda project: None)

    ctx = m.build_context("sess", None, resolve=False)
    assert ctx["plan"]["items"] == [{"text": "worktree task", "state": "pending"}]
    assert [p["number"] for p in ctx["prs"]] == [7]
    assert any(l["label"] == "LIN-4" for l in ctx["links"])


def test_recent_transcripts_limit_and_age(monkeypatch, tmp_path):
    import devmachine_infer as m
    import os
    import time as _time

    projects = tmp_path / "projects"
    repo = tmp_path / "dash"
    slug = str(repo.resolve()).replace("/", "-")
    (projects / slug).mkdir(parents=True)

    now = _time.time()
    fresh = []
    for i in range(5):
        f = projects / slug / f"fresh{i}.jsonl"
        f.write_text("{}\n")
        os.utime(f, (now - i, now - i))
        fresh.append(f)
    stale = projects / slug / "stale.jsonl"
    stale.write_text("{}\n")
    os.utime(stale, (now - 60 * 3600, now - 60 * 3600))

    monkeypatch.setattr(m, "PROJECTS_DIR", projects)
    picked = m.recent_transcripts(repo)
    assert picked == fresh[:4]
    assert stale not in picked


def _monitor_launch(tool_use_id, task_id, description):
    return [
        {"message": {"content": [
            {"type": "tool_use", "id": tool_use_id, "name": "Monitor",
             "input": {"command": "tail -f app.log", "description": description,
                       "timeout_ms": 180000}}]}},
        {"message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_use_id,
             "content": f"Monitor started (task {task_id}, timeout 180000ms)."}]},
         "toolUseResult": {"taskId": task_id, "timeoutMs": 180000, "persistent": False}},
    ]


def test_extract_background_monitor_running_then_done():
    import devmachine_infer as m
    events = _monitor_launch("tu_m", "b9f2co", "Wait for backend suite")
    assert m.extract_background(events)["monitors"] == [
        {"label": "Wait for backend suite", "status": "running"}]

    events.append({"message": {"content": [
        {"type": "text", "text": "<task-id>b9f2co</task-id>"}]}})
    assert m.extract_background(events)["monitors"] == []


def test_extract_background_async_subagent():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "id": "tu_a", "name": "Agent",
             "input": {"description": "Map the API", "subagent_type": "Explore"}}]}},
        {"message": {"content": [
            {"type": "tool_result", "tool_use_id": "tu_a",
             "content": "Agent launched"}]},
         "toolUseResult": {"isAsync": True, "status": "async_launched",
                           "agentId": "a0a6aa74", "description": "Map the API"}},
    ]
    assert m.extract_background(events)["agents"] == [
        {"label": "Map the API", "status": "running"}]

    events.append({"content": "<task-notification>\n<task-id>a0a6aa74</task-id>"})
    assert m.extract_background(events)["agents"] == []


def test_extract_background_keeps_groups_apart():
    import devmachine_infer as m
    events = (_monitor_launch("tu_m", "bmon", "CI for PR 5241")
              + _bash_launch("tu_s", "bsh", "Deploy the thing")
              + [{"message": {"content": [
                  {"type": "tool_use", "id": "tu_t", "name": "Task",
                   "input": {"description": "Audit ship readiness"}}]}}])
    bg = m.extract_background(events)
    assert [x["label"] for x in bg["monitors"]] == ["CI for PR 5241"]
    assert [x["label"] for x in bg["shells"]] == ["Deploy the thing"]
    assert [x["label"] for x in bg["agents"]] == ["Audit ship readiness"]


def test_pr_number_takes_only_the_first_argument():
    import devmachine_infer as m
    assert m.pr_number("5240 --json state") == "5240"
    assert m.pr_number(" 5241 --json state,title") == "5241"
    assert m.pr_number("--watch --interval 15") is None
    assert m.pr_number("<pr> --watch --interval 15") is None
    assert m.pr_number("--repo acme/dash --json number,state 2>") is None


def test_extract_refs_skips_gh_subcommands_that_name_no_pr():
    import devmachine_infer as m
    events = [
        {"message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "gh pr list --repo o/r --state all --json number 2>&1"}}]}},
        {"message": {"content": [
            {"type": "text", "text": "gh pr checks <pr> --watch --interval 15"}]}},
        {"message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "gh pr checks 5241 --watch"}}]}},
    ]
    refs = m.extract_refs(events, default_repo="o/r")
    assert sorted(refs["github"]) == ["o/r#5241"]


def test_service_of_reads_the_domain():
    import devmachine_infer as m
    assert m.service_of("https://linear.app/example/issue/EX-2701") == "linear"
    assert m.service_of("https://acme.atlassian.net/browse/PROJ-451") == "atlassian"
    assert m.service_of("https://gist.github.com/user/abc") == "github"
    assert m.service_of("https://platform.openai.com/plugins/edit") == "openai"


def test_map_links_keeps_one_row_per_issue():
    import devmachine_infer as m
    links = m.map_links([
        {"url": "https://linear.app/example/issue/EX-2701"},
        {"url": "https://linear.app/example/issue/EX-2701/comment-9"},
        {"url": "https://example.com/a"},
    ])
    assert [l["label"] for l in links] == ["EX-2701", "example.com/a"]


def test_service_of_folds_usercontent_into_the_site():
    import devmachine_infer as m
    assert m.service_of("https://gist.githubusercontent.com/u/f03de5") == "github"
    assert m.service_of("https://gist.github.com/u/f03de5") == "github"



def _event_at(ts, text):
    return {"timestamp": ts, "message": {"role": "user", "content": text}}


def test_extract_refs_tracks_the_last_time_a_pr_was_mentioned():
    import devmachine_infer as m
    events = [
        _event_at("2026-01-01T00:00:00Z", "gh pr view 5 -R o/r"),
        _event_at("2026-01-02T00:00:00Z", "https://github.com/o/r/pull/5"),
        _event_at("2026-01-03T00:00:00Z", "gh pr view 9 -R o/r"),
    ]
    refs = m.extract_refs(events, default_repo="o/r")
    assert refs["github"]["o/r#5"]["first_ts"] == "2026-01-01T00:00:00Z"
    assert refs["github"]["o/r#5"]["last_ts"] == "2026-01-02T00:00:00Z"
    assert refs["github"]["o/r#9"]["last_ts"] == "2026-01-03T00:00:00Z"


def test_extract_refs_keeps_the_last_mention_when_an_event_has_no_timestamp():
    import devmachine_infer as m
    events = [
        _event_at("2026-01-01T00:00:00Z", "gh pr view 5 -R o/r"),
        {"message": {"role": "user", "content": "gh pr view 5 -R o/r"}},
    ]
    refs = m.extract_refs(events, default_repo="o/r")
    assert refs["github"]["o/r#5"]["last_ts"] == "2026-01-01T00:00:00Z"


def test_merge_refs_keeps_the_newest_mention_of_the_two_transcripts():
    import devmachine_infer as m
    dst = {"github": {"o/r#5": {"num": 5, "repo": "o/r", "count": 1,
                                "first_ts": "2026-01-01T00:00:00Z",
                                "last_ts": "2026-01-01T00:00:00Z"}},
           "links": {}}
    src = {"github": {"o/r#5": {"num": 5, "repo": "o/r", "count": 2,
                                "first_ts": "2026-01-02T00:00:00Z",
                                "last_ts": "2026-01-04T00:00:00Z"}},
           "links": {}}
    m.merge_refs(dst, src)
    assert dst["github"]["o/r#5"]["last_ts"] == "2026-01-04T00:00:00Z"
    assert dst["github"]["o/r#5"]["count"] == 3


def test_map_prs_carries_the_last_mention():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 5, "url": "u", "state": "open",
               "isDraft": False, "title": "t", "ci": "none", "review": None,
               "last_ts": "2026-01-02T00:00:00Z"}]
    assert m.map_prs(github)[0]["lastSeen"] == "2026-01-02T00:00:00Z"


def test_map_prs_omits_the_last_mention_when_there_is_none():
    import devmachine_infer as m
    github = [{"repo": "o/r", "num": 5, "url": "u", "state": "open",
               "isDraft": False, "title": "t", "ci": "none", "review": None}]
    assert "lastSeen" not in m.map_prs(github)[0]


def test_extract_refs_survives_an_event_whose_timestamp_is_null():
    import devmachine_infer as m
    events = [{"timestamp": None, "message": {"role": "user", "content": "gh pr view 5 -R o/r"}}]
    refs = m.extract_refs(events, default_repo="o/r")
    assert refs["github"]["o/r#5"]["last_ts"] == ""


def test_extract_refs_compares_mentions_as_instants_not_as_text():
    import devmachine_infer as m
    events = [
        _event_at("2026-01-02T00:00:00.500Z", "gh pr view 5 -R o/r"),
        _event_at("2026-01-02T00:00:00Z", "gh pr view 5 -R o/r"),
    ]
    refs = m.extract_refs(events, default_repo="o/r")
    assert refs["github"]["o/r#5"]["last_ts"] == "2026-01-02T00:00:00.500Z"


# ── one query, one cache ──────────────────────────────────────────────────

def _entry(num, repo="o/r", host="github.com"):
    return {"host": host, "repo": repo, "num": num, "count": 1,
            "first_ts": "", "last_ts": "",
            "url": f"https://{host}/{repo}/pull/{num}"}


def _node(state="OPEN", draft=False, review="APPROVED", rollup="SUCCESS", unresolved=0):
    threads = [{"isResolved": False} for _ in range(unresolved)] + [{"isResolved": True}]
    commit = {"statusCheckRollup": {"state": rollup} if rollup else None}
    return {"number": 1, "state": state, "isDraft": draft, "title": "t",
            "url": "https://github.com/o/r/pull/1", "reviewDecision": review,
            "reviewThreads": {"nodes": threads},
            "commits": {"nodes": [{"commit": commit}]}}


def _reply(nodes: list, errors=None):
    data = {f"a{i}": ({"pullRequest": n} if n else None) for i, n in enumerate(nodes)}
    payload = {"data": data}
    if errors:
        payload["errors"] = errors
    return json.dumps(payload)


def test_batch_query_names_every_pull_request():
    import devmachine_infer as m
    q = m.batch_query([_entry(5), _entry(9, repo="acme/dash")])
    assert 'a0: repository(owner: "o", name: "r")' in q
    assert "pullRequest(number: 5)" in q
    assert 'a1: repository(owner: "acme", name: "dash")' in q
    assert "pullRequest(number: 9)" in q


def test_parse_batch_reads_state_review_ci_and_open_threads():
    import devmachine_infer as m
    entries = [_entry(5)]
    resolved, limited, answered = m.parse_batch(_reply([_node(unresolved=2)]), entries)
    pr = resolved["github.com|o/r#5"]
    assert (pr["state"], pr["review"], pr["ci"], pr["threads"]) == ("open", "APPROVED", "pass", 2)
    assert (limited, answered) == (False, True)


def test_parse_batch_calls_a_merged_pull_request_merged_and_a_draft_draft():
    import devmachine_infer as m
    merged, *_ = m.parse_batch(_reply([_node(state="MERGED", draft=False)]), [_entry(5)])
    assert merged["github.com|o/r#5"]["state"] == "merged"
    draft, *_ = m.parse_batch(_reply([_node(state="OPEN", draft=True)]), [_entry(5)])
    assert draft["github.com|o/r#5"]["state"] == "draft"


def test_parse_batch_maps_the_check_rollup_to_the_panel_words():
    import devmachine_infer as m
    for rollup, word in [("SUCCESS", "pass"), ("FAILURE", "fail"), ("ERROR", "fail"),
                         ("PENDING", "pending"), ("EXPECTED", "pending"), (None, "none")]:
        resolved, *_ = m.parse_batch(_reply([_node(rollup=rollup)]), [_entry(5)])
        assert resolved["github.com|o/r#5"]["ci"] == word, rollup


def test_parse_batch_skips_a_pull_request_that_came_back_empty():
    import devmachine_infer as m
    resolved, *_ = m.parse_batch(_reply([None, _node()]), [_entry(5), _entry(9)])
    assert list(resolved) == ["github.com|o/r#9"]


def test_parse_batch_reports_a_rate_limit():
    import devmachine_infer as m
    reply = _reply([None], errors=[{"type": "RATE_LIMIT", "message": "API rate limit exceeded"}])
    _, limited, answered = m.parse_batch(reply, [_entry(5)])
    assert (limited, answered) == (True, False)


def test_parse_batch_reports_a_rate_limit_that_gh_printed_as_text():
    import devmachine_infer as m
    _, limited, answered = m.parse_batch("gh: API rate limit already exceeded for user ID 1",
                                         [_entry(5)])
    assert (limited, answered) == (True, False)


def _fake_gh(calls, reply):
    def fake_run(cmd, env=None, timeout=30):
        calls.append(cmd)
        return True, reply(cmd) if callable(reply) else reply
    return fake_run


def test_resolve_all_asks_github_once_for_every_pull_request(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([_node(), _node()])))
    entries = {"o/r#5": _entry(5), "o/r#9": _entry(9)}

    out = m.resolve_all(entries, cache_path=tmp_path / "prs.json", now=1000.0)

    assert len(calls) == 1
    assert [p["state"] for p in out] == ["open", "open"]


def test_resolve_all_asks_each_host_on_its_own():
    import devmachine_infer as m
    groups = m.group_by_host([_entry(5), _entry(9, host="github.example.com")])
    assert [host for host, _ in groups] == ["github.com", "github.example.com"]


def test_resolve_all_serves_a_fresh_answer_without_asking_github(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([_node()])))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    out = m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_OPEN - 1)

    assert len(calls) == 1
    assert out[0]["state"] == "open"


def test_resolve_all_asks_again_once_the_answer_is_old(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([_node()])))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_OPEN + 1)

    assert len(calls) == 2


def test_resolve_all_keeps_a_merged_pull_request_for_a_day(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([_node(state="MERGED")])))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    out = m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_OPEN * 10)

    assert len(calls) == 1
    assert out[0]["state"] == "merged"


def test_resolve_all_stops_asking_after_a_rate_limit_and_still_shows_what_it_knows(
        tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    replies = [_reply([_node()]),
               _reply([None], errors=[{"type": "RATE_LIMIT", "message": "exceeded"}])]

    def fake_run(cmd, env=None, timeout=30):
        calls.append(cmd)
        return True, replies[min(len(calls), len(replies)) - 1]

    monkeypatch.setattr(m, "run", fake_run)
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_OPEN + 1)
    out = m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_OPEN + 2)

    assert len(calls) == 2
    assert out[0]["state"] == "open"
    assert out[0]["title"] == "t"


def test_resolve_all_asks_again_once_the_rate_limit_pause_is_over(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []

    def fake_run(cmd, env=None, timeout=30):
        calls.append(cmd)
        return True, _reply([None], errors=[{"type": "RATE_LIMIT", "message": "exceeded"}])

    monkeypatch.setattr(m, "run", fake_run)
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    m.resolve_all(entries, cache_path=cache, now=1000.0 + 1)
    m.resolve_all(entries, cache_path=cache, now=1000.0 + m.RATE_LIMIT_PAUSE + 1)

    assert len(calls) == 2


def test_resolve_all_reports_a_pull_request_it_never_read_as_unknown(tmp_path, monkeypatch):
    import devmachine_infer as m
    monkeypatch.setattr(m, "run", lambda cmd, env=None, timeout=30: (False, "boom"))

    out = m.resolve_all({"o/r#5": _entry(5)}, cache_path=tmp_path / "prs.json", now=1000.0)

    assert out[0]["state"] == "unknown"
    assert out[0]["ci"] == "none"


def test_a_damaged_cache_file_is_ignored(tmp_path):
    import devmachine_infer as m
    cache = tmp_path / "prs.json"
    cache.write_text("{not json")
    assert m.cache_load(cache) == {}


def test_the_cache_forgets_a_pull_request_nobody_asked_about_for_a_week(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([_node()])))
    cache = tmp_path / "prs.json"

    m.resolve_all({"o/r#5": _entry(5)}, cache_path=cache, now=1000.0)
    m.resolve_all({"o/r#9": _entry(9)}, cache_path=cache, now=1000.0 + m.CACHE_KEEP + 1)

    assert list(m.cache_load(cache)["prs"]) == ["github.com|o/r#9"]


def test_resolve_all_remembers_that_github_shows_no_such_pull_request(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([None])))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    first = m.resolve_all(entries, cache_path=cache, now=1000.0)
    again = m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_UNKNOWN - 1)

    assert len(calls) == 1
    assert first[0]["state"] == "unknown" and again[0]["state"] == "unknown"
    assert again[0]["num"] == 5 and again[0]["url"].endswith("/pull/5")


def test_resolve_all_asks_about_an_unknown_pull_request_again_much_later(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, _reply([None])))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    m.resolve_all(entries, cache_path=cache, now=1000.0 + m.FRESH_UNKNOWN + 1)

    assert len(calls) == 2


def test_a_query_that_never_arrived_is_not_an_answer(tmp_path, monkeypatch):
    import devmachine_infer as m
    calls = []
    monkeypatch.setattr(m, "run", _fake_gh(calls, "could not resolve host"))
    cache = tmp_path / "prs.json"
    entries = {"o/r#5": _entry(5)}

    m.resolve_all(entries, cache_path=cache, now=1000.0)
    m.resolve_all(entries, cache_path=cache, now=1001.0)

    assert len(calls) == 2


# ── configured GitHub Enterprise hosts ─────────────────────────────────────

def test_without_config_file_only_github_com_is_recognized(monkeypatch, tmp_path):
    import devmachine_infer as m

    monkeypatch.setenv("DEVMACHINE_APP_CONFIG", str(tmp_path / "missing.json"))

    refs = m.extract_refs(
        _user_event("see https://github.example.com/o/r/pull/5 and https://github.com/o/r/pull/9"),
        "o/r")
    assert list(refs["github"]) == ["o/r#9"]
    assert m.gh_env("github.com") is None


def test_enterprise_host_from_config_is_recognized_in_a_pr_url(monkeypatch, tmp_path):
    import devmachine_infer as m

    config = tmp_path / "config.json"
    config.write_text(json.dumps({"github_hosts": [
        {"host": "github.example.com", "proxy": "socks5://proxy.example.com:1080"}]}))
    monkeypatch.setenv("DEVMACHINE_APP_CONFIG", str(config))

    refs = m.extract_refs(_user_event("see https://github.example.com/o/r/pull/5"), "o/r")
    assert list(refs["github"]) == ["o/r#5"]
    assert refs["github"]["o/r#5"]["host"] == "github.example.com"

    env = m.gh_env("github.example.com")
    assert env["GH_HOST"] == "github.example.com"
    assert env["HTTPS_PROXY"] == "socks5://proxy.example.com:1080"


def test_a_configured_host_with_no_proxy_gets_gh_host_and_no_proxy(monkeypatch, tmp_path):
    import devmachine_infer as m

    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"github_hosts": [{"host": "github.example.com"}]}))
    monkeypatch.setenv("DEVMACHINE_APP_CONFIG", str(config))

    env = m.gh_env("github.example.com")
    assert env["GH_HOST"] == "github.example.com"
    assert "HTTPS_PROXY" not in env
