# Deployments

Deployments provision model inference capacity for a Foundry project and expose a stable deployment name that agents and applications can call at runtime.

## Deployment modes

| Deployment mode | Description |
| --- | --- |
| Azure OpenAI models | Provision dedicated or shared capacity for Azure OpenAI model families. |
| Serverless models | Route requests to supported serverless models without dedicated capacity management. |
| Managed compute | Configure project-managed compute and SKU settings for predictable throughput. |

## Operational concepts

- Deployments bind a model name and version to a project-scoped deployment name.
- `sku` settings determine capacity, throughput, and quota consumption.
- `versionUpgradeOption` controls how the deployment behaves when a newer compatible model version is available.
- Provisioning, scaling, and quota are region-specific.

## Common operations

| Operation | Description |
| --- | --- |
| [Create a deployment](./methods/create.md) | Provision a new deployment for a model and SKU combination. |
| [Retrieve a deployment](./methods/retrieve.md) | Read one deployment by name. |
| [Update a deployment](./methods/update.md) | Change capacity or version upgrade behavior. |
| [Delete a deployment](./methods/delete.md) | Remove a deployment that is no longer needed. |
| [List deployments](./methods/list.md) | Enumerate deployments available in the project. |
