# Evaluations overview

The Evaluations resource group defines reusable evaluation configurations and run history for model outputs or agent behavior in a Foundry project. An evaluation can point to built-in evaluators, custom evaluators, and project data sources that are used when individual runs execute.

## What this resource group supports

- Create, retrieve, update, list, and delete evaluation definitions.
- Configure built-in evaluators and custom evaluators in the same evaluation.
- Start runs with inline test data or dataset references.
- Retrieve run status, aggregate summaries, and item-level scores.
- Cancel long-running evaluation runs.

## Base request format

- **Base URL:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`
- **Authentication:** `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`
- **API version:** `api-version=2025-05-01`

## Resource model

- **Evaluation:** Reusable configuration that defines evaluators, metadata, and the default data source contract.
- **Run:** Execution record for a specific evaluation against a concrete dataset or inline test payload.

## Related guides

- [Create datasets and run evaluations](../../guides/create-datasets-run-evals.md)
- [Batch evaluations](../../guides/batch-evaluations.md)
