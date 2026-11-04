# Releases and repository rules

**English** · [Русский](releasing.ru.md) · [Contributing](../CONTRIBUTING.md)

## The normal path

Work branch → pull request → review and passing checks → squash merge into `main`
→ version tag → GitHub Release. Only invited collaborators can create PRs;
other users can propose a change in an issue or discussion with a fork link.

`main` is the integration branch. Use `release/0.1` only when maintaining an
older release line, with the same PR and CI requirements. Do not create permanent
extra branches for ordinary features. Repository admins control release tags;
ordinary collaborators cannot create them. Version tags cannot be moved or deleted
under the active rules. Ruleset definitions are recorded under `.github/rulesets/`;
editing those JSON files does not change GitHub settings automatically.

The review exception for repository admins applies only to a separate review
ruleset, through a PR. The baseline rule still requires passing CI and a PR.
This lets a solo owner work without disabling the required checks.

The baseline also requires CodeQL results and blocks new security findings of
medium severity or higher, plus analysis errors. GitHub's default-setup merge
protection has a documented exception for Dependabot PRs; those still require
the ordinary CI gate and owner review. Review dependency and runtime updates
manually before merging.

## Version names

Use `vMAJOR.MINOR.PATCH`, for example `v0.1.0`. For beta releases use a suffix
such as `v0.1.0-beta.1` and mark the GitHub Release as a prerelease.
Increase patch for compatible fixes, minor for features and major for breaking
changes after 1.0. During 0.x, describe incompatible changes explicitly.

## Release checklist

1. Merge the release changes through a PR with a title such as `chore(release): prepare v0.1.0-beta.1`.
2. Check the chosen `main` commit's CI and security results. On an Apple Silicon Mac, verify relevant real model workflows separately; Linux unit CI does not certify macOS inference.
3. Use **Releases → Draft a new release**. Select the reviewed commit as the target and create the new version tag from that commit.
4. Review the notes: changes, setup/update steps, supported macOS and known limits. Keep model licenses separate from the app's MIT license.
5. Add any intended distribution assets while the release is still a draft. Never upload models, local environments, databases, voice samples or generated personal audio.
6. Publish after checking the draft. Release immutability locks published assets and the associated tag. Correct a published build with a new version rather than overwriting it.

The repository does not publish releases automatically from contributor branches.
No binary installer or production certification is implied by a source release.

## Checks and cost boundary

Required CI covers commit/PR conventions, tracked file boundaries, the static
site, frontend tests and build, Java tests and lightweight Python units. It uses
standard `ubuntu-24.04` GitHub-hosted runners. It does not install MLX or download
model weights. No CI cache or build artifact is uploaded; the Pages workflow
keeps only its small, validated static artifact for one day.

Branch/tag rules, private vulnerability reporting, public-repository CodeQL,
Dependabot alerts and standard public runners are currently available without
buying a GitHub plan or security add-on. GitHub's future terms are outside this
project's control. Larger runners, paid Marketplace actions, private-repository
compute, excess artifact/Packages storage and account-wide paid usage are separate.
Do not enable them as part of this workflow.

For a hard billing boundary, the account owner should check **Settings → Billing
and licensing → Budgets and alerts**, keep relevant paid-usage budgets at **$0**
and enable **Stop usage when budget limit is reached** where available. Repository
configuration cannot prove the state of an account's payment methods or shared
spending budgets. See [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
and [budget controls](https://docs.github.com/en/billing/how-tos/set-up-budgets).

See the [security policy](../SECURITY.md) for private reports. Alert status and
the actual repository rules remain visible in GitHub; a green check is not a
guarantee that arbitrary code or model output is safe.
