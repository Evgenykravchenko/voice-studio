# CodeQL review for 0.1.0

**English** · [Русский](security-review.ru.md) · [Release status](status.md)

## Scope and result

All 138 existing CodeQL alerts were individually traced from their SARIF source
to the reported sink at `d9989cf43da31aa9316bb1bcc6735a3c2598a59f`, with an
independent boundary review. No supported exploitable path was established.
These alerts are false positives for the reviewed source and deployment; they
are not 138 repaired vulnerabilities. No runtime behavior was changed solely
to silence the scanner. Focused regression tests exercise the existing controls.

| Alerts | Report | Evidence that defeats the claim |
| --- | --- | --- |
| 6-126 | Python paths (121) | Explicit local CLI root/output paths, guarded internal job IDs, or bounded vendored example paths. HTTP cannot set the project root or manifest destination. |
| 127-130 | Python commands (4) | Fixed runtime specifications, interpreter/probe/lock recipes and argument arrays. The project root is a local operator choice. |
| 131 | Java command (1) | Exact catalog membership before a fixed interpreter/module/action; no shell. |
| 132-138 | Java paths (7) | Registered task lookup, generated UUIDs, slash-free profile IDs and fixed comparison sides before file access. |
| 3-5 | Regex complexity (3) | Speech is capped at 3000 characters, normal chunks at 400, voice descriptions at 1000 before the named expressions. |
| 2 | SSML entities (1) | Parsing requires a `<speak`-prefixed document. A DTD must precede the root and cannot pass that guard; malformed XML fails before inference. |
| 1 | Sitemap entities (1) | The parser reads the locally generated sitemap in the source/build boundary, not an uploaded or network document. |

The four vendored path reports (6, 102-104) originate in the upstream OpenVoice
Gradio demo. Its directory component is a basename plus fixed version/hash;
the demo fixes its output directory. The supported studio uses the conversion
API without a speaker-embedding save path and never launches that demo.

## Verification and limits

Tests cover traversal and absolute identifiers, restored invalid import metadata,
option-like/unknown model IDs, generation size limits, malformed SSML/entities,
valid speech markup and valid model selection. Existing archive, containment,
relocation, persistence and audio tests remain part of CI. No model weights or
personal recordings are needed for these regression tests.

This review concerns these specific findings and the local, single-user loopback
deployment in [SECURITY.md](../SECURITY.md). It is not an exhaustive new audit or a
guarantee of zero vulnerabilities. A new unbounded caller, altered validator,
network exposure, parser or file-loading path requires a fresh assessment.
CodeQL remains enabled; no rule or path was globally excluded.
