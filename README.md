# Communication Simulator Community

A public home for community-shared `.simulator` configurations for [Communication Simulator](https://github.com/rogerkehn/CommunicationSimulatorSuite).

## Planned application integration

- Browse shared configurations in a dedicated Community Simulators window.
- Show one entry per configuration, with the latest published revision selected.
- Expand version history only when requested, and download any published revision.
- Require a posting comment for each new configuration or revision.
- Keep revisions and posting comments in Git history.

The application browser and upload integration are not implemented yet. Submission moderation is awaiting the owner's choice. This repository initially contains documentation only.

## Files and contributions

Store configurations under `simulators/<contributor>/<name>.simulator`. Keep the same path when updating an existing configuration so its Git history remains together. Explain the device/protocol, simulator application version, setup requirements and changes in your posting comment. Do not commit passwords, tokens, private addresses, conversation histories, personal information or proprietary manuals. Review the complete file before sharing.

A public repository does not give every visitor permission to push to its default branch. GitHub accounts can contribute through forks and pull requests; direct publication requires separately configured permissions or an upload service. The final in-app submission flow will follow the owner's moderation choice.

## Downloading

GitHub's file history preserves earlier committed revisions. The planned application browser will provide latest and previous-version downloads without adding each revision to the main list. Downloaded configurations may contain C# scripts; inspect their contents before manually opening or executing them.

## Rights

Submit only content you have the right to share. No blanket license is assigned to third-party contributions or the simulator application by this repository. Include applicable permission and license information with contributions; public visibility alone is not a general reuse license.