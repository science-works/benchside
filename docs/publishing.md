# Publishing the Python package

The package name is `benchside`; its executable is `bench`. PyPI serves both pip
and uv. Publishing this package does not install a ChatGPT/Claude web plugin or
deploy the Science Works receiver.

## One-time publisher setup

Use a verified PyPI account with two-factor authentication. Under
[account publishing](https://pypi.org/manage/account/publishing/), add this pending
GitHub publisher for the first release:

| Field | Value |
| --- | --- |
| PyPI project name | `benchside` |
| Owner | `science-works` |
| Repository | `benchside` |
| Workflow filename | `publish-python.yml` |
| Environment | `pypi` |

Create the matching GitHub environment and restrict its deployment branches to
`main`. No long-lived PyPI API token is needed. The first successful upload creates
the project under the PyPI account that registered the pending publisher. Keep
Science Works repository attribution and add any other maintainers through
PyPI's collaborator controls when their accounts and access are agreed.

TestPyPI is optional and separate: it needs its own account/pending publisher
with the same values except environment `testpypi`. Its packages are not available
to normal `pip install` users. A pending publisher does not reserve a name.

## Release procedure

1. Review and merge the version, metadata, documentation and package changes
   through a PR. Check that CI passed, including source and wheel installations.
2. Create the corresponding release tag on `main`, for example `v0.4.1`. Keep
   `pyproject.toml` and `benchside.__version__` consistent with the tag. Rebuild
   plugin archives from that same release if distributing web-app packages.
3. Manually run **Publish Python package** from `main`, with the exact tag and
   target `pypi` (or `testpypi` for a rehearsal). Ordinary pushes and PRs never
   publish. The workflow refuses a non-release tag, a tag not merged to main,
   or a mismatch between the tag and package/runtime versions.
4. The workflow runs the tests, builds a wheel and source archive, validates PyPI
   metadata, and tests fresh installs on Python 3.11 and 3.14. The generic skill,
   private save/restore, ODT/Markdown reading copies and sharing-off defaults are
   checked outside the source checkout with all collection endpoints disabled.
5. Only after both builds pass does a separate job obtain a short-lived publishing
   credential through GitHub OIDC and upload the tested Python 3.11 build. The
   publishing job has no source checkout; the build jobs have no publishing token.
6. Verify the public PyPI version and distribution hashes, then test a fresh
   `pip install benchside==<version>` and `uv tool install benchside==<version>`
   from PyPI. Update README/SETUP to advertise that route only after it works.

Released files cannot be replaced with different bytes under the same version.
Fixes after publication need a new version. Retrying a partially uploaded release
needs investigation of which exact files were accepted; do not silently skip
existing files and assume the two builds match.

References: [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[publishing with OIDC](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
[uv publishing](https://docs.astral.sh/uv/guides/package/).
