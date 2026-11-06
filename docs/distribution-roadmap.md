# Future distribution

Updated 6 November 2026. [Benchside 0.4.1 is published on PyPI](https://pypi.org/project/benchside/0.4.1/)
and [GitHub Releases](https://github.com/science-works/benchside/releases/tag/v0.4.1).
Clean public-registry installations through pip (Python 3.11) and uv tool install
(Python 3.14) passed generic-agent setup, all eight role references, private
save/restore, ODT/Markdown exports and sharing-off checks. These tests sent no
submissions. Both PyPI files have the same SHA-256 checksums as the GitHub assets.

## PyPI and uv: available

Use `uv tool install benchside`, or `python -m pip install benchside` inside a
persistent virtual environment, followed by the host's `bench setup` command.
The package is `benchside`; its executable is `bench`. The same PyPI release
serves pip and uv. Updates use `uv tool upgrade benchside` or pip's `--upgrade`,
followed by rerunning setup to refresh the installed skill.

Publishing uses GitHub Trusted Publishing, restricted to the
`science-works/benchside` repository's `publish-python.yml` workflow and `pypi`
environment. That environment permits only `main`; the manual workflow requires
a release tag already merged to main. It runs the regression suite and isolated
wheel/source installation checks on Python 3.11 and 3.14 before uploading.
See the [publishing procedure](publishing.md) and
[first successful run](https://github.com/science-works/benchside/actions/runs/42250979386).
TestPyPI remains an optional rehearsal route and was not used for this release.

The Python package does not install a web-app plugin or supply a model, storage
connector or network permission. For a one-off CLI check,
`uvx --from benchside bench --help` is available; persistent setup should use a
durable tool installation or virtual environment.

References: [PyPI publishing](https://docs.pypi.org/publishing/publishing-to-pypi/),
[uv tools](https://docs.astral.sh/uv/guides/tools/),
[uv publishing](https://docs.astral.sh/uv/guides/package/).

## Plugin discovery

- Prepare public ChatGPT/Codex and Claude directory submissions with verified
  Science Works publisher ownership, listing assets and accurate host limitations.
  Complete each platform's current checks/review and test a directory install
  and update before claiming that distribution route is supported.
- Consider a Science Works Claude Code marketplace hosted on GitHub. Add its
  catalogue and verify acquisition of the runtime/dependencies, installation and
  updates; adding a marketplace manifest alone is not a working distribution.
- Publish clear privacy/support information for optional research contributions.
  Skills-only Benchside does not need an MCP server merely to gain a listing.

These are packaging/discovery improvements. They cannot grant missing runtime,
durable storage or outbound networking capabilities to a host account.
