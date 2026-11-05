import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrShipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pr-ship tests ")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.user_home = self.directory / "home"
        self.user_home.mkdir()
        self.mocks = self.directory / "mocks"
        self.mocks.mkdir()
        self.prefix = self.directory / "custom prefix"
        self.env = os.environ.copy()
        for key in ("PREFIX", "DESTDIR", "SUDO_USER", "BASH_ENV", "ENV", "LC_ALL"):
            self.env.pop(key, None)
        self.env.update(
            HOME=str(self.user_home),
            PATH=f"{self.mocks}:/usr/bin:/bin:/usr/sbin:/sbin",
            LANG="en_US.UTF-8",
            NO_COLOR="1",
            GH_LOG=str(self.directory / "gh.log"),
        )
        self.stub("uname", 'printf "%s\\n" "${TEST_PLATFORM:-Darwin}"\n')
        self.stub(
            "gh",
            'printf "%s\\n" "$@" >> "$GH_LOG"\n'
            'case "$2" in\n'
            '  */merge)\n'
            '    printf "%s\\n" "${GH_MERGED:-true}"\n'
            '    exit "${GH_MERGE_RC:-0}"\n'
            '    ;;\n'
            '  *)\n'
            '    printf "%s\\n" "${GH_CREATE_OUT:-42}"\n'
            '    printf "%s" "${GH_CREATE_ERR:-}" >&2\n'
            '    exit "${GH_CREATE_RC:-0}"\n'
            '    ;;\n'
            'esac\n',
        )

    def stub(self, name, body):
        path = self.mocks / name
        path.write_text("#!/bin/bash\n" + body)
        path.chmod(0o755)
        return path

    def run_command(self, *arguments, input_text="", success=True, extra_env=None):
        result = subprocess.run(
            [str(argument) for argument in arguments],
            cwd=ROOT,
            env={**self.env, **(extra_env or {})},
            input=input_text,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def install(self, input_text="", prefix=None):
        return self.run_command(
            "/bin/bash", "install.sh", input_text=input_text,
            extra_env={"PREFIX": str(prefix or self.prefix)},
        )

    def config(self, content):
        path = self.user_home / ".config/pr-ship/config"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_platform_prefix_defaults(self):
        for platform, expected in (
            ("Darwin", str(self.user_home / ".local")),
            ("Linux", "/usr"),
        ):
            with self.subTest(platform=platform):
                result = self.run_command(
                    "/bin/bash", "lib/pr-ship/install-paths.sh",
                    extra_env={"TEST_PLATFORM": platform},
                )
                self.assertEqual(result.stdout.strip(), expected)

    def test_sudo_uses_original_user_home_on_macos(self):
        original_home = self.directory / "original user"
        self.stub("getent", f'printf "user:x:501:20::%s:/bin/zsh\\n" "{original_home}"\n')
        result = self.run_command(
            "/bin/bash", "lib/pr-ship/install-paths.sh",
            extra_env={"SUDO_USER": "user"},
        )
        self.assertEqual(result.stdout.strip(), str(original_home / ".local"))

    def test_unknown_sudo_user_fails_before_installing(self):
        self.stub("getent", "exit 2\n")
        result = self.run_command(
            "/bin/bash", "install.sh", success=False,
            extra_env={"SUDO_USER": "missing-user"},
        )
        self.assertIn("Cannot determine", result.stderr)
        self.assertFalse((self.user_home / ".local").exists())

    def test_sudo_home_lookup_with_macos_directory_services(self):
        original_home = self.directory / "mac user"
        self.stub("dscl", f'printf "NFSHomeDirectory: %s\\n" "{original_home}"\n')
        (self.mocks / "sed").symlink_to("/usr/bin/sed")
        result = self.run_command(
            "/bin/bash", "lib/pr-ship/install-paths.sh",
            extra_env={"SUDO_USER": "user", "PATH": str(self.mocks)},
        )
        self.assertEqual(result.stdout.strip(), str(original_home / ".local"))

    def test_macos_install_and_uninstall_defaults(self):
        self.run_command("/bin/bash", "install.sh")
        binary = self.user_home / ".local/bin/pr-ship"
        self.assertTrue(os.access(binary, os.X_OK))
        result = self.run_command(binary, "--version")
        self.assertEqual(result.stdout.strip(), "pr-ship v1.0.3")
        self.run_command("/bin/bash", "uninstall.sh")
        self.assertFalse(binary.exists())
        self.assertFalse((self.user_home / ".local/share/pr-ship").exists())

    def test_custom_prefix_and_bundled_languages(self):
        self.install()
        binary = self.prefix / "bin/pr-ship"
        self.assertEqual(self.run_command(binary, "--version").stdout.strip(), "pr-ship v1.0.3")
        self.assertIn("Usage:", self.run_command(binary, "--help").stdout)
        self.config('PRSHIP_LANG="pt_BR"\n')
        result = self.run_command(binary, success=False)
        self.assertIn("informe o repositório", result.stderr)
        self.assertEqual(
            sorted(path.name for path in (self.prefix / "share/pr-ship/lang").glob("*.sh")),
            sorted(path.name for path in (ROOT / "lib/pr-ship/lang").glob("*.sh")),
        )

    def test_relative_symlink_loads_installed_resources(self):
        self.install()
        link_directory = self.directory / "links"
        link_directory.mkdir()
        link = link_directory / "pr-ship"
        link.symlink_to("../custom prefix/bin/pr-ship")
        self.assertIn("Usage:", self.run_command(link, "--help").stdout)

    def test_source_checkout_runs_with_system_bash(self):
        self.assertIn("Usage:", self.run_command("/bin/bash", "bin/pr-ship", "--help").stdout)

    def test_setup_with_system_bash(self):
        self.install()
        self.run_command(
            "/bin/bash", self.prefix / "bin/pr-ship", "--setup",
            input_text="\ngabsdk\n\n\n\n\n",
        )
        config = (self.user_home / ".config/pr-ship/config").read_text()
        self.assertIn('PRSHIP_OWNER="gabsdk"', config)
        self.assertIn('PRSHIP_DEFAULT_HEAD="development"', config)
        self.assertIn('PRSHIP_DEFAULT_BASE="sandbox"', config)
        self.assertIn('PRSHIP_LANG="en"', config)

    def test_reinstall_preserves_config_by_default(self):
        self.install()
        config = self.config('PRSHIP_OWNER="preserved"\n')
        self.install(input_text="y\n\n")
        self.assertEqual(config.read_text(), 'PRSHIP_OWNER="preserved"\n')

    def test_declined_reinstall_leaves_files_untouched(self):
        self.install()
        binary = self.prefix / "bin/pr-ship"
        before = binary.stat().st_mtime_ns
        self.install(input_text="n\n")
        self.assertEqual(binary.stat().st_mtime_ns, before)

    def test_uninstall_preserves_config_by_default(self):
        self.install()
        config = self.config('PRSHIP_OWNER="preserved"\n')
        self.run_command(
            "/bin/bash", "uninstall.sh", input_text="\n",
            extra_env={"PREFIX": str(self.prefix)},
        )
        self.assertFalse((self.prefix / "bin/pr-ship").exists())
        self.assertFalse((self.prefix / "share/pr-ship").exists())
        self.assertTrue(config.exists())

    def test_uninstall_purge_removes_config(self):
        self.install()
        config = self.config('PRSHIP_OWNER="preserved"\n')
        self.run_command(
            "/bin/bash", "uninstall.sh", "--purge",
            extra_env={"PREFIX": str(self.prefix)},
        )
        self.assertFalse(config.parent.exists())

    def test_relative_prefix_is_rejected(self):
        for script in ("install.sh", "uninstall.sh"):
            with self.subTest(script=script):
                result = self.run_command(
                    "/bin/bash", script, success=False, extra_env={"PREFIX": "relative"},
                )
                self.assertIn("PREFIX must be an absolute path", result.stderr)

    def test_unwritable_prefix_reports_failure(self):
        result = self.run_command(
            "/bin/bash", "install.sh", success=False,
            extra_env={"PREFIX": "/dev/null/pr-ship"},
        )
        self.assertIn("Cannot create installation directories", result.stderr)

    def test_make_uses_same_macos_default(self):
        self.run_command("make", "install")
        binary = self.user_home / ".local/bin/pr-ship"
        self.assertIn("Usage:", self.run_command(binary, "--help").stdout)
        self.run_command("make", "uninstall")
        self.assertFalse(binary.exists())

    def test_make_linux_staging_and_custom_prefix(self):
        staging = self.directory / "staging"
        self.run_command(
            "make", "install", f"DESTDIR={staging}",
            extra_env={"TEST_PLATFORM": "Linux"},
        )
        binary = staging / "usr/bin/pr-ship"
        self.assertIn("Usage:", self.run_command(binary, "--help").stdout)
        self.run_command("make", "uninstall", "PREFIX=/usr", f"DESTDIR={staging}")
        self.assertFalse(binary.exists())
        self.run_command("make", "install", f"PREFIX={self.prefix}")
        self.assertIn("Usage:", self.run_command(self.prefix / "bin/pr-ship", "--help").stdout)
        self.run_command("make", "uninstall", f"PREFIX={self.prefix}")
        self.assertFalse((self.prefix / "bin/pr-ship").exists())

    def test_create_and_merge_with_mock_github(self):
        self.install()
        self.config('PRSHIP_OWNER="example"\n')
        result = self.run_command(
            "/bin/bash", self.prefix / "bin/pr-ship", "project", "feature/test", "main",
            "--title", "Release test", "--body", "Test body",
        )
        self.assertIn("Process finished successfully", result.stdout)
        self.assertEqual(
            (self.directory / "gh.log").read_text().splitlines(),
            [
                "api", "repos/example/project/pulls",
                "-f", "title=Release test", "-f", "head=feature/test", "-f", "base=main",
                "-f", "body=Test body", "--jq", ".number",
                "api", "repos/example/project/pulls/42/merge",
                "-X", "PUT", "-f", "merge_method=merge", "--jq", ".merged",
            ],
        )

    def test_failed_create_never_merges(self):
        self.install()
        result = self.run_command(
            "/bin/bash", self.prefix / "bin/pr-ship", "example/project", success=False,
            extra_env={
                "GH_CREATE_RC": "1", "GH_CREATE_OUT": "{}",
                "GH_CREATE_ERR": "gh: Not Found (HTTP 404)\n",
            },
        )
        self.assertIn("Repository not found", result.stderr)
        self.assertNotIn("/merge", (self.directory / "gh.log").read_text())

    def test_rejected_merge_reports_open_pr(self):
        self.install()
        result = self.run_command(
            "/bin/bash", self.prefix / "bin/pr-ship", "example/project", success=False,
            extra_env={"GH_MERGED": "false"},
        )
        self.assertIn("The PR is still open: https://github.com/example/project/pull/42", result.stderr)


if __name__ == "__main__":
    unittest.main()
