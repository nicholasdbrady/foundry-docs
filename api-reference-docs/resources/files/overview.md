# Files

Files store uploaded content that agents and evaluations can reuse for file search, code interpreter workloads, and evaluation datasets.

## Supported purposes

| Purpose | Typical use |
| --- | --- |
| `assistants` | Make documents available to agents for file search and code interpreter workflows. |
| `fine-tune` | Upload training and validation data for fine-tuning jobs. |
| `evaluations` | Upload datasets, prompts, or reference outputs for evaluation runs. |

## Limits and formats

- Individual file uploads can be up to 512 MB.
- Supported formats commonly include `.jsonl`, `.json`, `.csv`, `.txt`, `.md`, `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.py`, `.js`, and `.ipynb`.
- Password-protected or encrypted files are rejected.

## Common operations

| Operation | Description |
| --- | --- |
| [Upload a file](./methods/create.md) | Upload a new file using multipart form data. |
| [Retrieve file metadata](./methods/retrieve.md) | Read file metadata by file identifier. |
| [Delete a file](./methods/delete.md) | Remove a file that is no longer needed. |
| [List files](./methods/list.md) | Enumerate uploaded files and filter by purpose. |
| [Retrieve file content](./methods/content.md) | Download the raw bytes for an uploaded file. |
