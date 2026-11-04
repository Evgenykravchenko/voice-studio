# Security policy

**English** · [Русский](SECURITY.ru.md) · [Contributing](CONTRIBUTING.md)

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/Evgenykravchenko/voice-studio/security/advisories/new).
Include the version or commit, affected component, impact and minimal reproduction
steps with anonymous test data. Keep credentials, private recordings and working
exploits out of public issues and discussions. Reports are reviewed manually.

## Versions

Voice Studio is a macOS Apple Silicon beta. Report issues against current `main`
or the latest published release, if one exists. Include the exact version or
commit. Supported maintenance lines will be identified in release notes;
no maintenance schedule or response-time guarantee is currently promised.

## System boundary

The application consists of a browser interface, a local Java API and Python
model processes. The API is configured for loopback access. GitHub Pages hosts
only public project documentation, not inference or user data. Internet-facing,
multi-user hosting is not a supported deployment.

Protected assets include recordings, transcripts, voice profiles, saved projects,
model caches and the integrity of source, workflows, tags and release artifacts.
Audio uploads, text, filenames, profile identifiers, downloaded model artifacts
and proposed source changes cross trust boundaries. A local-only deployment does
not make malicious web requests, parsing bugs or path escapes harmless.

## Security properties to preserve

- Keep inference and personal data local; no unexpected upload of recordings or scripts.
- Validate local request origins and hosts; do not replace loopback binding with public exposure silently.
- Constrain file access and subprocess arguments to their intended operations. Preserve existing originals when creating derived audio.
- Keep downloaded files and dependencies project-local, verify pinned model artifacts where supported and retain third-party notices.
- Keep personal files, credentials, models and databases out of Git and build artifacts. Review actual publication contents as well as ignore rules.
- Review changes through pull requests with passing checks. Untrusted contribution workflows must not receive write tokens or repository secrets.
- Publish only reviewed release sources. Protect version tags and retain release integrity controls.

These are intended properties to review, not a claim that every implementation
path has been audited. Report bypasses with realistic reachability and impact,
including unintended data disclosure, file access, command execution, unsafe
model/archive handling or a compromised contribution/release path. No finding
class is blanket-excluded by this document.

## Limits

Models, dependencies and upstream runtimes have separate licenses and security
properties. Local data backups remain the user's responsibility. Model output
quality and a passing CI run do not establish security. Repository controls do
not replace protection of the owner's GitHub account and access credentials.
