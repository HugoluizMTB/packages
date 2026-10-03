-- Invented data shaped exactly like rows written by opencode 1.18.34.
-- Session ses_fixture1 runs in /Users/alice/dev/widgets; ses_fixture2 is a subagent (task tool) child.
INSERT INTO project (id, worktree, vcs, name, icon_url, icon_url_override, icon_color, time_created, time_updated, time_initialized, sandboxes, commands)
VALUES ('4b1c0e2f9d8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c', '/Users/alice/dev/widgets', 'git', NULL, NULL, NULL, NULL, 1790977880000, 1790977890000, NULL, '[]', NULL);

INSERT INTO session (id, project_id, workspace_id, parent_id, slug, directory, path, title, version, time_created, time_updated)
VALUES ('ses_f01662699ffeFixtureAAAAAA', '4b1c0e2f9d8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c', NULL, NULL, 'jolly-wolf', '/Users/alice/dev/widgets', '', 'Check PR 42 and run tests', '1.18.34', 1790977890662, 1790977901159);

INSERT INTO session (id, project_id, workspace_id, parent_id, slug, directory, path, title, version, time_created, time_updated)
VALUES ('ses_f01662000ffeFixtureCHILDD', '4b1c0e2f9d8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c', NULL, 'ses_f01662699ffeFixtureAAAAAA', 'brave-otter', '/Users/alice/dev/widgets', '', 'Review PR diff (@explore subagent)', '1.18.34', 1790977898000, 1790977899500);

-- user message + its text part
INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES
('msg_0fe99da69001FixtureUser01', 'ses_f01662699ffeFixtureAAAAAA', 1790977890921, 1790977890921,
 '{"role":"user","time":{"created":1790977890921},"agent":"build","model":{"providerID":"opencode","modelID":"big-pickle"},"summary":{"diffs":[]}}');
INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES
('prt_0fe99da6c001FixturePart01', 'msg_0fe99da69001FixtureUser01', 'ses_f01662699ffeFixtureAAAAAA', 1790977890926, 1790977890926,
 '{"type":"text","text":"Check https://github.com/acme/widgets/pull/42, write a todo list, then run gh pr view 42."}');

-- assistant message 1: text + todowrite tool
INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES
('msg_0fe99da73001FixtureAsst01', 'ses_f01662699ffeFixtureAAAAAA', 1790977890931, 1790977894503,
 '{"parentID":"msg_0fe99da69001FixtureUser01","role":"assistant","mode":"build","agent":"build","path":{"cwd":"/Users/alice/dev/widgets","root":"/Users/alice/dev/widgets"},"cost":0,"tokens":{"total":7887,"input":5859,"output":108,"reasoning":0,"cache":{"write":0,"read":1920}},"modelID":"big-pickle","providerID":"opencode","time":{"created":1790977890931,"completed":1790977894503},"finish":"tool-calls"}');
INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES
('prt_0fe99e512001FixturePart02', 'msg_0fe99da73001FixtureAsst01', 'ses_f01662699ffeFixtureAAAAAA', 1790977893650, 1790977893650,
 '{"snapshot":"4b825dc642cb6eb9a060e54bf8d69288fbee4904","type":"step-start"}'),
('prt_0fe99e517001FixturePart03', 'msg_0fe99da73001FixtureAsst01', 'ses_f01662699ffeFixtureAAAAAA', 1790977893655, 1790977893655,
 '{"type":"text","text":"Looking at https://github.com/acme/widgets/pull/42 now. I will start with the todo list.","time":{"start":1790977893655,"end":1790977894483}}'),
('prt_0fe99e5cb001FixturePart04', 'msg_0fe99da73001FixtureAsst01', 'ses_f01662699ffeFixtureAAAAAA', 1790977893835, 1790977893835,
 '{"type":"tool","tool":"todowrite","callID":"call_7fc5b98e09cb4ce6bcc9f2e1","state":{"status":"completed","input":{"todos":[{"content":"Check the PR","status":"in_progress","priority":"high"},{"content":"Run the tests","status":"pending","priority":"medium"}]},"output":"[\n  {\n    \"content\": \"Check the PR\",\n    \"status\": \"in_progress\",\n    \"priority\": \"high\"\n  },\n  {\n    \"content\": \"Run the tests\",\n    \"status\": \"pending\",\n    \"priority\": \"medium\"\n  }\n]","metadata":{"todos":[{"content":"Check the PR","status":"in_progress","priority":"high"},{"content":"Run the tests","status":"pending","priority":"medium"}],"truncated":false},"title":"2 todos","time":{"start":1790977894400,"end":1790977894402}}}'),
('prt_0fe99e861001FixturePart05', 'msg_0fe99da73001FixtureAsst01', 'ses_f01662699ffeFixtureAAAAAA', 1790977894497, 1790977894497,
 '{"reason":"tool-calls","snapshot":"4b825dc642cb6eb9a060e54bf8d69288fbee4904","type":"step-finish","tokens":{"total":7887,"input":5859,"output":108,"reasoning":0,"cache":{"write":0,"read":1920}},"cost":0}');

-- assistant message 2: bash tool + task (subagent) tool
INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES
('msg_0fe99e869001FixtureAsst02', 'ses_f01662699ffeFixtureAAAAAA', 1790977894505, 1790977899600,
 '{"parentID":"msg_0fe99da69001FixtureUser01","role":"assistant","mode":"build","agent":"build","path":{"cwd":"/Users/alice/dev/widgets","root":"/Users/alice/dev/widgets"},"cost":0,"tokens":{"total":8080,"input":149,"output":31,"reasoning":92,"cache":{"write":0,"read":7808}},"modelID":"big-pickle","providerID":"opencode","time":{"created":1790977894505,"completed":1790977899600},"finish":"tool-calls"}');
INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES
('prt_0fe99f22d001FixturePart06', 'msg_0fe99e869001FixtureAsst02', 'ses_f01662699ffeFixtureAAAAAA', 1790977897005, 1790977897005,
 '{"snapshot":"4b825dc642cb6eb9a060e54bf8d69288fbee4904","type":"step-start"}'),
('prt_0fe99f50d001FixturePart07', 'msg_0fe99e869001FixtureAsst02', 'ses_f01662699ffeFixtureAAAAAA', 1790977897741, 1790977897741,
 '{"type":"tool","tool":"bash","callID":"call_7982b44d146c44219d3bb7ab","state":{"status":"completed","input":{"command":"gh pr view 42","description":"Show PR 42"},"output":"title:\tAdd widget sorting\nstate:\tOPEN\nauthor:\talice\nurl:\thttps://github.com/acme/widgets/pull/42\n","metadata":{"output":"title:\tAdd widget sorting\nstate:\tOPEN\nauthor:\talice\nurl:\thttps://github.com/acme/widgets/pull/42\n","exit":0,"truncated":false},"title":"gh pr view 42","time":{"start":1790977897790,"end":1790977897852}}}'),
('prt_0fe99f60a001FixturePart08', 'msg_0fe99e869001FixtureAsst02', 'ses_f01662699ffeFixtureAAAAAA', 1790977898000, 1790977898000,
 '{"type":"tool","tool":"task","callID":"call_1a2b3c4d5e6f708192a3b4c5","state":{"status":"running","input":{"description":"Review PR diff","prompt":"Read the diff of PR 42 in /Users/alice/dev/widgets and list risky changes.","subagent_type":"explore"},"title":"Review PR diff","metadata":{"parentSessionId":"ses_f01662699ffeFixtureAAAAAA","sessionId":"ses_f01662000ffeFixtureCHILDD","model":{"modelID":"big-pickle","providerID":"opencode"}},"time":{"start":1790977898000}}}');

INSERT INTO todo (session_id, content, status, priority, position, time_created, time_updated) VALUES
('ses_f01662699ffeFixtureAAAAAA', 'Check the PR', 'in_progress', 'high', 0, 1790977894396, 1790977894396),
('ses_f01662699ffeFixtureAAAAAA', 'Run the tests', 'pending', 'medium', 1, 1790977894396, 1790977894396);
