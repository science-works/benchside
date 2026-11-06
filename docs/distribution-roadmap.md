# Future distribution

Recorded 6 November 2026. These routes are planned, not published or enabled.
GitHub releases remain the current download route.

## PyPI and uv

- Confirm the package name and Science Works maintainers; create the publisher
  account with verified email and two-factor authentication.
- Complete Python package metadata (licence, source/docs/support links and
  maintainer attribution), retaining existing author credit.
- Add a GitHub Actions release workflow and configure PyPI Trusted Publishing
  for that specific repository/workflow. Keep publishing separate from ordinary
  pushes and require the release to be approved.
- Exercise TestPyPI and clean Python 3.11/3.14 installations: bundled role
  content, generic-agent setup, private save/restore and a mocked submission.
- Once published, recommend `uv tool install benchside` for local CLI/agent
  use, `uv tool upgrade benchside` for updates, and
  `uvx --from benchside bench --help` for a one-off invocation.
  The package is `benchside`; its executable is `bench`.
- The same PyPI release also supports `pip install benchside`; no separate uv
  registry publication is required. `uv build`/`uv publish` can build and upload.
- Update README/SETUP only when the installation route is actually live. Do not
  imply this installs a web-app plugin or supplies a model, storage connector
  or network permission.

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
