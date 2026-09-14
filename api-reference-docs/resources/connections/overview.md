# Connections

Connections link a Foundry project to external services so agents, evaluations, and other project features can access external data and capabilities through named resources instead of inline secrets.

## Supported connection types

| Type | Typical target | Common use |
| --- | --- | --- |
| `AzureOpenAI` | Azure OpenAI endpoint | Route agent or application traffic to model deployments. |
| `AzureAISearch` | Azure AI Search service endpoint | Enable retrieval and grounding against indexed content. |
| `AzureBlobStorage` | Azure Blob Storage account or container endpoint | Read or write project artifacts and evaluation datasets. |
| `CustomKeys` | Custom service endpoint | Store multiple named secrets for custom integrations. |
| `APIKey` | Custom API endpoint | Call external REST services with a single API key. |

## How connections are used

- Agents use connections to reach tools such as Azure OpenAI, search indexes, storage, and custom APIs.
- Evaluations use connections to reference datasets, judge models, and external data sources.
- Project automation can reuse the same connection names across environments while rotating credentials independently.

## Common operations

| Operation | Description |
| --- | --- |
| [Create a connection](./methods/create.md) | Create a named connection to an external service. |
| [Retrieve a connection](./methods/retrieve.md) | Read one connection by name. |
| [Update a connection](./methods/update.md) | Change the target, credentials, or metadata for an existing connection. |
| [Delete a connection](./methods/delete.md) | Remove a connection that is no longer used. |
| [List connections](./methods/list.md) | Enumerate connections available in the project. |

## Resource shape

A connection object typically includes a project-scoped `name`, a `type`, a `target` endpoint, a `credentials` descriptor, and optional `metadata`. Secret values are write-only and are redacted in read responses.
