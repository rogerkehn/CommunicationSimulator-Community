# Communication Simulator Community

Share `.simulator` configurations from **Windows > Community Simulators** in Communication Simulator. Browse and download without signing in. Every published revision is retained; the application shows one entry per author/name and reveals older revisions on request.

## Immediate publication

Choose **Upload**, select a saved simulator file, give it a short name and write a posting comment. Sign in with your own GitHub personal access token (classic `public_repo` scope). The application keeps the token only for this upload dialog. No maintainer credential is shipped in the application.

Uploads create a submission issue in this repository. GitHub Actions validates it and publishes automatically without maintainer approval, normally within a minute. The issue links to the workflow outcome. Publication may take longer when GitHub queues jobs. If publication fails, the file is not listed; the maintainer can retry the issue using the workflow's Run workflow action. Do not repeatedly upload an uncertain submission.

Each GitHub account owns `simulators/<account>/<name>/`. Use the same name to post a new revision of your own file; other contributors publish under their own account. Revision numbers are submission issue numbers, and can have gaps. The latest revision is the greatest published revision number, even if jobs finish out of order. Files, checksums, dates and required comments are recorded in `catalog.json` and Git history. Published revisions are never overwritten by the uploader. Repository administrators retain moderation/removal powers.

## Sharing limits and review

Each file must be valid simulator XML, at most 1 MiB after privacy cleanup and small enough to fit a 60,000-character issue (at most 56,000 base64 characters of gzip data). The application reports oversized files before posting. Saved AI conversations and all AI preferences are removed from the shared copy; originals remain unchanged. Inspect the prepared XML: settings and scripts can still contain credentials, network details, personal data or proprietary material. Share only material you own or have permission to distribute and identify its applicable license/permissions in your comment. This repository does not assign a blanket license to contributions or the application.

Downloaded files are saved only, never automatically opened, compiled, connected or executed. Inspect scripts before opening files in the simulator. Automatic publication validates format and integrity; it is not a hardware, compatibility or security certification.

## Protocol and operations

Submissions use an issue body beginning with `SIMULATOR-SHARE/1` followed by JSON fields `name`, `comment`, `content` (gzip/base64 UTF-8 XML) and `sha256` (uncompressed bytes). Identity comes from the actual issue author, never submitted JSON. Only newly opened submissions trigger publication; edits cannot replace versions. Submit a new issue for each revision. The trusted publisher does not execute contributed scripts, check out contributor branches, download URLs from submissions, or accept arbitrary paths. A manual workflow retry supports recovery. No signing keys, application source or release credentials are held here.

Public submission issues themselves contain the encoded file. Closing an issue does not make its data private. Accidental disclosures require GitHub removal/credential rotation as appropriate; avoid uploading secrets in the first place.
