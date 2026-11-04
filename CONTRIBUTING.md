# Contributing

**English** · [Русский](CONTRIBUTING.ru.md) · [Home](README.md)

Voice Studio welcomes bug reports, documentation fixes and focused pull requests.
English and Russian are both welcome.

## Choose where to start

| You want to... | Start here |
| --- | --- |
| Ask how to use a model or workflow | [Discussions](https://github.com/Evgenykravchenko/voice-studio/discussions) and the [user guide](docs/guide.md). |
| Report something broken | Search [existing issues](https://github.com/Evgenykravchenko/voice-studio/issues), then use the bug report form. |
| Suggest a feature | Describe the task, current difficulty and expected result in a feature request. |
| Work on a larger change or platform port | Discuss the approach first to agree on scope. |

## Make a change

1. Fork the repository and create a branch for one focused change.
2. Follow [setup](docs/setup.md) and the [development guide](docs/development.md).
3. Check the affected behavior. Include the commands or manual checks in your pull request.
4. Update both English and Russian guides when changing documented behavior.
5. Describe the problem, resulting behavior and any limits in the pull request.

Current installer and inference support targets macOS 14+ on Apple Silicon.
Windows and Linux work needs suitable backends and real platform checks before
being advertised as supported. See the [roadmap](docs/roadmap.md).

## Keep examples safe to publish

Use anonymous sample text and synthetic or consented test audio. Review diffs
before uploading: recordings, voice profiles, databases, model weights, local
paths, tokens and logs with private content must stay out of the repository.
Keep dependencies and caches project-local. Preserve third-party license notices.

For model changes, document supported languages, voice modes, the runtime and
model license. A successful download alone does not demonstrate working inference.
