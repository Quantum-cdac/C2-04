# 08 - AI / LLM Usage Disclosure

Per the hackathon Development Rules ("AI tools are permitted for coding, debugging, research and documentation. Teams review, validate and explain AI-assisted work and disclose material AI-tool use."):

## Tools used

- **Instinct** (AI assistant platform) - implemented this module end to end during the event period: parser, IR, QSDK builder, reference simulator, tests, examples and documentation, and ran the offline test suite.
- **Claude** (Anthropic, team subscription) - available to the team for review, debugging and documentation support during the event.

## What the team did with the output

- Ran the SDK integration suite in the venue Qniverse notebook against the preinstalled SDK (4 passed, recorded with the manual Bell conversion figures in `docs/05-test-plan-and-results.md`).
- Review of the generated code against the problem statement and the QSDK documentation, and the ability to explain the architecture (parser -> IR -> documented QSDK builder), the supported subset, the register-renaming rule and the equivalence method, remain the team's responsibility under the rules; the team members presenting this module are expected to complete that review before submission.

## Data handling

No account credentials or API keys were entered into any AI service, code, documentation or chat message in this workflow. The Qniverse API key is never embedded in code, docs or messages; remote execution uses each member's own registered account.
