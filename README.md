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

Benchside is built by **Science Works, a nonprofit research and policy studio** studying how researchers use AI and what tools would make their work easier.

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

## Where does my notebook live?

You choose during setup. **Science Works does not receive your notebook.** Your decisions, findings and open questions stay in the project record you control.

- **On your computer:** choose a folder and read the journal as an ODT document, Markdown or both.
- **In your AI app:** use a private Claude Doc or ChatGPT Page if your account can save and reopen it.
- **In a connected service:** use a document store such as Google Docs if your agent has a connector that can safely update it. Benchside checks this before relying on it.

To continue in another app, point it at the same folder or notebook. Both apps need access; their accounts don’t sync automatically. Saving locally doesn’t change how your AI provider processes the chat. [More about your records →](docs/readable-records.md)

## Help other researchers

A useful community contribution can be as simple as: *“Our image exporter drops channel labels. We save a separate label table and reattach it after export.”* That tells us what broke and what helped, without revealing what the images show.

**Sharing is optional and off by default.** If you choose to contribute a workflow problem, you see the exact report and can edit it, skip it or send it to Science Works. Reports use a random contributor ID so we can connect contributions from the same notebook or folder. Your raw chats and scientific findings aren’t part of the report.

With permission, we use these reports to study recurring problems in scientific workflows and decide what software to build. You can separately opt into usage counts, feedback, surveys or analysis of selected conversations to help us understand **how researchers use language models**. You can change your choices later. [How participation works →](docs/getting-started.md#optional-sharing)

Our [community goal](docs/community.md) is for the next researcher who hits the same problem to find a workaround someone else has tried. You can contribute a workaround today; a searchable collection is planned. Sending a research report doesn’t publish it.

## Get involved

Have an idea for a scientific role? [Propose it or open a PR](CONTRIBUTING.md). If you use Benchside in published work, please cite [the release you used](https://github.com/science-works/benchside/releases).

[Live demo guide](docs/demo-start-here.md) · [How Benchside works](ARCHITECTURE.md) · [Developer guide](docs/getting-started.md#developer-packaging) · [Apache 2.0 licence](LICENSE)

<details>
<summary>Setting up Benchside on someone’s behalf? Instructions for agents</summary>

### Agent setup essentials

Follow [SETUP.md](SETUP.md). If you can only read this page:

- Reuse a working installation. On a local agent, install the [Python package](https://pypi.org/project/benchside/) with `uv tool install benchside` or pip in a persistent virtual environment. Run `bench setup --agent claude` for Claude Code, `bench setup --agent codex` for Codex, or `bench setup --agent generic --skills-dir <actual host skill directory>` for another agent.
- In ChatGPT, discover **Plugin Creator** and use the unchanged `benchside-plugin-<version>.zip` from the [latest release](https://github.com/science-works/benchside/releases/latest). For Claude’s plugin installer, use `benchside-claude-plugin-<version>.zip`. If only manual upload is available, guide that step. No MCP server is needed.
- Run the installed skill’s version check. After the researcher chooses durable storage, save and read back an isolated synthetic record; check recall in a new chat if possible. Explain any missing capability. Do not send data during setup.

</details>
