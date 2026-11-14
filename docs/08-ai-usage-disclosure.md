# 08 - AI / LLM Usage Disclosure

Per the hackathon Development Rules ("AI tools are permitted for coding, debugging, research and documentation. Teams review, validate and explain AI-assisted work and disclose material AI-tool use."):

## Tools used

- **Instinct** (AI assistant platform) - implemented this module end to end during the event period: parser, IR, QSDK builder, reference simulator, tests, examples and documentation, and ran the offline test suite.
- **Claude** (Anthropic, team subscription) - available to the team for review, debugging and documentation support during the event.

## What the team did with the output

- Reviewed the generated code against the problem statement and the QSDK documentation (gate catalog, register rules, `add_gate` conventions).
- Ran the offline test suite and demo; will run the SDK integration suite in the Qniverse environment and record results in `docs/05-test-plan-and-results.md`.
- Each team member presenting this module can explain the architecture (parser -> IR -> documented QSDK builder), the supported subset, the register-renaming rule, and the statevector equivalence method.

## Data handling

No confidential information, credentials, personal data or restricted material was entered into external AI services. The Qniverse API key is never embedded in code, docs or messages; remote execution uses each member's own registered account.
