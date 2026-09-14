# Responses API overview

The Responses API is the project-scoped interface for generating model output directly, without creating an agent, thread, or run. It is suited to request-response workloads that need the OpenAI-style responses shape on top of a Microsoft Foundry project endpoint.

## What this resource group supports

- Text input as a simple string or as structured content parts.
- Image input alongside text input in the same request.
- Text output in buffered or streamed form.
- Tool use with code interpreter, file search, web search, and function calling.
- Retrieval, cancellation, deletion, and list operations for response resources.

## Base request format

- **Base URL:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`
- **Authentication:** `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`
- **API version:** `api-version=2025-05-01`

## Common workflow

1. Create a response with `POST /responses`.
2. Set `stream` to `true` when the client should consume server-sent events as output is generated.
3. Retrieve the response later with `GET /responses/{responseId}` if the client needs the stored result.
4. Cancel a long-running response with `POST /responses/{responseId}/cancel`.
5. Delete responses that are no longer needed.

## Related guides

- [Create and run an agent](../../guides/create-and-run-agent.md)
- [Configure agent tools](../../guides/configure-agent-tools.md)
- [Create datasets and run evaluations](../../guides/create-datasets-run-evals.md)
