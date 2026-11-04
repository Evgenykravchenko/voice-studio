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

Pull request creation is restricted to invited collaborators. Other users can
open an issue or discussion with a proposal and a link to their fork. A maintainer
can bring a patch into a review branch without granting repository write access.

1. If you are an invited collaborator, create a branch for one focused change.
2. Follow [setup](docs/setup.md) and the [development guide](docs/development.md).
3. Check the affected behavior. Include the commands or manual checks in your pull request.
4. Update both English and Russian guides when changing documented behavior.
5. Describe the problem, resulting behavior and any limits in the pull request.

Changes to `main` and `release/*` go through a pull request and required checks.
Direct pushes, force pushes and branch deletion are blocked. Only squash merge is
enabled; the resulting commit uses the pull request title. Keep the branch up to
date by rebasing when needed. Resolve review conversations before merging.

The owner is the code owner. Other collaborators need the owner's approval.
The owner can merge their own pull request without a second reviewer, but cannot
bypass the separate required CI rule. Passing checks do not replace human review.

## Commit messages and PR titles

Use **`type(scope): description`** for every proposed commit and the PR title.
The scope is one lowercase word using letters and optional digits, for example
`audio`, `voices`, `models`, `api`, `web`, `site`, `deps`, `ci`, `repo` or `release`.
Write a short, concrete description; English is preferred for the public history.

```text
feat(voices): add voice preview
fix(audio): correct playback volume
docs(setup): explain the first launch
chore(deps): update dependencies
```

| Type | Use for |
| --- | --- |
| `feat`, `fix` | A feature or bug fix. |
| `docs`, `style` | Documentation or formatting without behavior changes. |
| `refactor`, `perf` | Internal restructuring or performance. |
| `test`, `build`, `ci` | Tests, build tooling or CI. |
| `chore`, `revert` | Maintenance or a deliberate reversal. |

A breaking change can use `!`, for example `feat(api)!: change the export format`,
with an explanation in the body. CI checks every commit added by the PR and its
title. Existing published history is retained. Reword local commits before
opening a PR if they do not follow the convention. See [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## Releases and security

See [Releases and repository rules](docs/releasing.md) for version tags,
maintenance branches and the release checklist. The [security policy](SECURITY.md)
explains private vulnerability reporting. Model weights and personal recordings
are never release assets.

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
