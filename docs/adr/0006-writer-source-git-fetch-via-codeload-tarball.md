# Writer source Git fetch uses an HTTP codeload tarball, not git clone

When a `Writer` supplies a public Git URL for `Source_Upload`, the backend fetches
the repository as an **HTTP archive download** (the host's "codeload" tarball
endpoint, e.g. `https://.../archive/<ref>.tar.gz`) and runs it through the same
`unpack_archive` path as a direct archive upload — rather than installing a `git`
binary and running `git clone`, or adding a Python Git library. We chose this
because the backend image is `python3.13-bookworm-slim` with no `git` installed:
the HTTP route needs no new system package, reuses the archive-unpack safety
guards (zip-slip rejection, symlink skipping, entry-count and total-size caps)
we already specify, and covers the realistic hosts for a CS/Medicine paper
(GitHub, GitLab).

## Consequences

- Only hosts that expose a codeload-style archive endpoint are supported; an
  arbitrary or unsupported Git host is rejected with the same
  "repository could not be fetched" `422` as an unreachable URL.
- Repositories requiring authentication are never fetched (the public archive
  endpoint simply fails) — consistent with the "no private repositories" boundary.
- Only the default/named ref's tracked files are stored, as text; the fetched
  tarball is discarded after unpacking (no working copy retained), per
  `docs/adr/0003`'s "store derived content, not raw artifacts" boundary.
- Swapping to `git clone` or a Git library later is possible behind the same
  `Source_Upload` seam if arbitrary-host support becomes necessary.
