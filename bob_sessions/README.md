# bob_sessions/

This directory stores Bob session evidence for Z-FORGE hackathon demonstrations.

Each file here represents a recorded Bob interaction that invoked the Z-FORGE change-engineering
workflow via the `zforge_change_workflow` MCP tool.

## Demo Request

When Bob receives the following request (in **Z-FORGE Engineer** mode):

> "Expand CUSTOMER-ID from 8 bytes to 12 bytes. Analyze the impact, propose the changes,
>  validate them, identify remaining risks, remediate them, and return the evidence."

Bob calls:

```
zforge_change_workflow({"field": "CUSTOMER-ID", "new_length": 12})
```

Bob then presents the structured result with clearly labelled sections for each workflow stage.

## Evidence Files

Place exported Bob session transcripts here as:

```
bob_sessions/session-YYYYMMDD-HHMMSS.json
bob_sessions/session-YYYYMMDD-HHMMSS.txt
```
