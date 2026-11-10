<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <img src="docs/assets/logo-light.svg" alt="" width="84">
  </picture>
  <h1>Benchside</h1>
  <p><strong>A research partner and a private project notebook for your AI assistant.</strong></p>
  <p><a href="docs/getting-started.md">Getting started</a> · <a href="https://github.com/science-works/benchside/releases/latest">Latest release</a> · <a href="CONTRIBUTING.md">Contribute a role</a></p>
</div>

Bring a half-formed question, a puzzling result or a paper you want to discuss. Benchside gives your assistant eight scientific roles and keeps a record of what **you** decided, what evidence you used and what’s still open. In a new chat, you can pick up the same project.

## Try it

Paste this into your agent:

> Set up Benchside for me in this app: https://github.com/science-works/benchside

For a first try, use **Claude Code** with a local folder or **Claude web** with a private notebook. ChatGPT, Codex and other agents such as OpenCode have [setup routes](docs/host-support.md) too, including for locally hosted models.

Your agent follows [the setup guide](SETUP.md), helps you choose where to save your work and checks it can reopen a test record. Benchside needs no separate account or API key. A web app may ask you to upload the plugin.

**A first session might sound like this:**

> **You:** Be my research supervisor. I have several images from each of six donors. What counts as an independent observation here?
>
> **Later:** Record my decision to check the donor labels before analysis. Leave open how to handle the repeated images.
>
> **Next chat:** Reopen my imaging project. What did I decide, and what was still open?

## Which role would help?

Ask in your own words. You don’t need to know a command or have a hypothesis to start.

| When you’re asking… | Try the… |
| --- | --- |
| What’s the next useful step for this project? | Research supervisor (PI) |
| What result would challenge my hypothesis? | Hypothesis reviewer |
| Which comparison or control am I missing? | Study-design consultant |
| Why did the same protocol give different results? | Methods troubleshooter |
| How far does this result support my claim? | Results discussant |
| Could another lab reproduce this analysis? | Reproducibility auditor |
| Does this paper’s evidence support its conclusion? | Journal-club discussant |
| What would a reviewer ask me to revise? | Scientific peer reviewer |

## What stays private?

Your project journal lives in the notebook or folder you choose, outside Git. Local projects have a [readable record](docs/readable-records.md) in ODT, Markdown or both. **Science Works does not receive your notebook.**

Sharing is off by default. If you want to help Science Works study what slows researchers down, you can review and send a workflow problem, such as a tool dropping labels on export, without sharing your scientific findings. Contributions use a random contributor ID. Feedback, usage counts, surveys and analysis of selected conversations are separate choices. [How participation works →](docs/getting-started.md#optional-sharing)

## Get involved

Have an idea for a scientific role? [Propose it or open a PR](CONTRIBUTING.md). Our [community plans](docs/community.md) include helping researchers find tools and workarounds others have tried. If you use Benchside in published work, please cite [the release you used](https://github.com/science-works/benchside/releases).

[Live demo guide](docs/demo-start-here.md) · [How Benchside works](ARCHITECTURE.md) · [Developer guide](docs/getting-started.md#developer-packaging) · [Apache 2.0 licence](LICENSE)

<details>
<summary>Setting up Benchside on someone’s behalf? Instructions for agents</summary>

### Agent setup essentials

Follow [SETUP.md](SETUP.md). If you can only read this page:

- Reuse a working installation. On a local agent, install the [Python package](https://pypi.org/project/benchside/) with `uv tool install benchside` or pip in a persistent virtual environment. Run `bench setup --agent claude` for Claude Code, `bench setup --agent codex` for Codex, or `bench setup --agent generic --skills-dir <actual host skill directory>` for another agent.
- In ChatGPT, discover **Plugin Creator** and use the unchanged `benchside-plugin-<version>.zip` from the [latest release](https://github.com/science-works/benchside/releases/latest). For Claude’s plugin installer, use `benchside-claude-plugin-<version>.zip`. If only manual upload is available, guide that step. No MCP server is needed.
- Run the installed skill’s version check. After the researcher chooses durable storage, save and read back an isolated synthetic record; check recall in a new chat if possible. Explain any missing capability. Do not send data during setup.

</details>
