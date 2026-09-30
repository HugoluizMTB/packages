import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin")
RESOLVE = os.path.join(BIN, "resolve")
JOIN = os.path.join(BIN, "join")
SELF_NAME = os.path.join(BIN, "self-name")

STATUS = {
    "BackendState": "Running",
    "Self": {"HostName": "laptop", "DNSName": "laptop.tail0000.ts.net.", "TailscaleIPs": ["100.64.0.2"]},
    "Peer": {
        "nodekey:1": {
            "HostName": "main",
            "DNSName": "main.tail0000.ts.net.",
            "TailscaleIPs": ["100.64.0.5", "fd7a:115c:a1e0::5"],
        },
        "nodekey:2": {"HostName": "box", "DNSName": "box-1.tail0000.ts.net.", "TailscaleIPs": ["100.64.0.9"]},
    },
}


class FakeTailscale:
    """A `tailscale` on a PATH that holds nothing else, so the real one never runs."""

    def __init__(self, status=None, exit_code=0, stderr="", sleep=0):
        self.dir = tempfile.mkdtemp()
        self.log = os.path.join(self.dir, "calls.log")
        python_dir = os.path.join(self.dir, "python")
        os.mkdir(python_dir)
        os.symlink(sys.executable, os.path.join(python_dir, "python3"))
        self.path = os.pathsep.join([os.path.join(self.dir, "bin"), python_dir])
        if status is None and exit_code == 0 and not stderr:
            return
        os.mkdir(os.path.join(self.dir, "bin"))
        script = os.path.join(self.dir, "bin", "tailscale")
        with open(script, "w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    #!{python}
                    import json, os, sys, time
                    with open({log!r}, "a") as log:
                        log.write(json.dumps(sys.argv[1:]) + "\\n")
                        for arg in sys.argv[1:]:
                            if arg.startswith("--auth-key=file:"):
                                with open(arg[len("--auth-key=file:"):]) as key:
                                    log.write("key " + key.read() + "\\n")
                                mode = os.stat(arg[len("--auth-key=file:"):]).st_mode & 0o777
                                log.write("mode " + oct(mode) + "\\n")
                    time.sleep({sleep})
                    sys.stderr.write({stderr!r})
                    if {status!r} is not None:
                        print(json.dumps({status!r}))
                    sys.exit({exit_code})
                    """
                ).format(
                    python=sys.executable, log=self.log, sleep=sleep, stderr=stderr, status=status, exit_code=exit_code
                )
            )
        os.chmod(script, os.stat(script).st_mode | stat.S_IEXEC)

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as f:
            return f.read().splitlines()

    def run(self, script, *args, settings=None, stdin=""):
        env = {"PATH": self.path}
        if settings is not None:
            env["DEVMACHINE_SETTINGS"] = json.dumps(settings)
        return subprocess.run(
            [script] + list(args), env=env, input=stdin, capture_output=True, text=True, timeout=30
        )


class ResolveTest(unittest.TestCase):
    def test_prints_every_address_of_the_named_machine(self):
        fake = FakeTailscale(status=STATUS)
        result = fake.run(RESOLVE, "main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["100.64.0.5", "fd7a:115c:a1e0::5"])
        self.assertEqual(fake.calls(), ['["status", "--json"]'])

    def test_finds_itself_too(self):
        result = FakeTailscale(status=STATUS).run(RESOLVE, "laptop")
        self.assertEqual(result.stdout.split(), ["100.64.0.2"])

    def test_falls_back_to_the_magicdns_name(self):
        result = FakeTailscale(status=STATUS).run(RESOLVE, "box-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["100.64.0.9"])

    def test_missing_tailscale_is_not_available_here(self):
        result = FakeTailscale().run(RESOLVE, "main")
        self.assertEqual(result.returncode, 3)
        self.assertIn("tailscale is not installed", result.stderr)

    def test_a_stopped_tailscale_is_not_available_here(self):
        status = dict(STATUS, BackendState="Stopped")
        result = FakeTailscale(status=status).run(RESOLVE, "main")
        self.assertEqual(result.returncode, 3)
        self.assertIn("tailscale is not running", result.stderr)

    def test_a_status_that_fails_is_not_available_here(self):
        result = FakeTailscale(exit_code=1, stderr="failed to connect to local tailscaled").run(RESOLVE, "main")
        self.assertEqual(result.returncode, 3)
        self.assertIn("failed to connect to local tailscaled", result.stderr)

    def test_an_unknown_name_is_not_available_here(self):
        result = FakeTailscale(status=STATUS).run(RESOLVE, "elsewhere")
        self.assertEqual(result.returncode, 3)
        self.assertIn('no machine named "elsewhere"', result.stderr)

    def test_a_status_that_is_not_json_is_an_error(self):
        fake = FakeTailscale(stderr="", exit_code=0, status="not json")
        result = fake.run(RESOLVE, "main")
        self.assertNotIn(result.returncode, (0, 3))

    def test_asks_for_exactly_one_name(self):
        result = FakeTailscale(status=STATUS).run(RESOLVE)
        self.assertNotIn(result.returncode, (0, 3))


class JoinTest(unittest.TestCase):
    def test_runs_a_plain_tailscale_up_by_default(self):
        fake = FakeTailscale(status={})
        result = fake.run(JOIN, settings={"exit_node": False, "login_server": ""})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fake.calls(), ['["up"]'])

    def test_runs_without_any_settings(self):
        fake = FakeTailscale(status={})
        result = fake.run(JOIN)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fake.calls(), ['["up"]'])

    def test_advertises_the_exit_node_when_asked(self):
        fake = FakeTailscale(status={})
        fake.run(JOIN, settings={"exit_node": True})
        self.assertEqual(fake.calls(), ['["up", "--advertise-exit-node"]'])

    def test_passes_the_login_server_and_signs_in_through_a_url_without_a_key(self):
        fake = FakeTailscale(status={})
        result = fake.run(JOIN, settings={"login_server": "https://net.example.com"}, stdin="\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fake.calls(), ['["up", "--login-server=https://net.example.com"]'])

    def test_hands_a_pasted_key_over_in_a_private_file_never_an_argument(self):
        fake = FakeTailscale(status={})
        result = fake.run(JOIN, settings={"login_server": "https://net.example.com"}, stdin="tskey-example\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = fake.calls()
        self.assertTrue(calls[0].startswith('["up", "--login-server=https://net.example.com", "--auth-key=file:'))
        self.assertNotIn("tskey-example", calls[0])
        self.assertIn("key tskey-example", calls)
        self.assertIn("mode 0o600", calls)
        path = json.loads(calls[0])[2][len("--auth-key=file:"):]
        self.assertFalse(os.path.exists(path), "the key file outlived the join")

    def test_refuses_a_login_server_that_is_not_a_url(self):
        fake = FakeTailscale(status={})
        result = fake.run(JOIN, settings={"login_server": "net.example.com --reset"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("login_server", result.stderr)
        self.assertEqual(fake.calls(), [])

    def test_reports_tailscale_up_failing(self):
        fake = FakeTailscale(exit_code=1, stderr="backend error")
        result = fake.run(JOIN)
        self.assertEqual(result.returncode, 1)

    def test_says_when_tailscale_is_not_installed(self):
        result = FakeTailscale().run(JOIN)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sync", result.stderr)


class SelfNameTest(unittest.TestCase):
    def test_prints_the_machines_own_name(self):
        result = FakeTailscale(status=STATUS).run(SELF_NAME)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "laptop\n")

    def test_fails_without_a_name(self):
        result = FakeTailscale(status={"Self": {}}).run(SELF_NAME)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("did not name", result.stderr)

    def test_fails_when_tailscale_is_missing(self):
        result = FakeTailscale().run(SELF_NAME)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
