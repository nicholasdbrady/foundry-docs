# Models

Models describe the catalog entries that are available for deployment in a Foundry project, including version information, capabilities, lifecycle status, and planned retirement dates.

## What model records include

- Stable model identifiers used for retrieval and deployment selection.
- Capability metadata such as chat, reasoning, embeddings, image generation, or audio.
- Lifecycle information, including preview, generally available, deprecated, and retired states.
- Deprecation dates that help plan migration before a model version is removed.

## Common operations

| Operation | Description |
| --- | --- |
| [Retrieve a model](./methods/retrieve.md) | Read one model record by identifier. |
| [List models](./methods/list.md) | Enumerate models and filter by capability or lifecycle status. |
