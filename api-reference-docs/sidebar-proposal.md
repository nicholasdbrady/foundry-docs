# Sidebar proposal

This proposal moves task-first guides to the top of the API reference, then groups operation references by resource.

## Top Tasks

- Create and run an agent
- Update and version an agent
- Stream session logs
- Create datasets and run evaluations
- Manage deployments
- Configure agent tools
- Manage connections
- Run batch evaluations

## Naming rules

- Use verb-first labels.
- Prefer short labels such as `Create agent`, `Get version`, `List files`.
- Keep one action per label.
- Use `Get` for a single resource and `List` for collections.
- Use `Create version` and `Delete version` instead of mixed nouns like `Agent versions`.

## Example tree

```text
API Reference
├── Top Tasks
│   ├── Create and run an agent
│   ├── Update and version an agent
│   ├── Stream session logs
│   ├── Create datasets and run evaluations
│   ├── Manage deployments
│   ├── Configure agent tools
│   ├── Manage connections
│   └── Run batch evaluations
├── Agents
│   ├── Create agent
│   ├── List agents
│   ├── Get agent
│   ├── Update agent
│   ├── Delete agent
│   ├── Create version
│   ├── List versions
│   ├── Get version
│   └── Delete version
├── Threads
│   ├── Create thread
│   ├── Get thread
│   ├── Update thread
│   └── Delete thread
├── Runs
│   ├── Create run
│   ├── Create thread and run
│   ├── List runs
│   ├── Get run
│   ├── Cancel run
│   ├── List run steps
│   ├── Get run step
│   └── Submit tool outputs
├── Messages
│   ├── Create message
│   ├── List messages
│   ├── Get message
│   ├── Update message
│   └── Delete message
├── Files
│   ├── Create file
│   ├── List files
│   ├── Get file
│   ├── Download file
│   └── Delete file
├── Connections
│   ├── List connections
│   ├── Get connection
│   └── Get connection credentials
├── Deployments
│   ├── Create deployment
│   ├── List deployments
│   ├── Get deployment
│   └── Update deployment
├── Evaluations
│   ├── Create evaluation
│   ├── List evaluations
│   ├── Get evaluation
│   ├── Update evaluation
│   ├── Delete evaluation
│   ├── Create evaluation run
│   ├── List evaluation runs
│   ├── Get evaluation run
│   ├── Cancel evaluation run
│   ├── List output items
│   └── Get output item
└── Models
    ├── List models
    └── Get model
```

## Additional recommendation

Add a small note under `Agents` and `Runs` that points readers to `Conversations` when the hosted-agent Responses protocol is the preferred execution path. This keeps the sidebar aligned with existing developer expectations while still surfacing the newer hosted runtime flow.
