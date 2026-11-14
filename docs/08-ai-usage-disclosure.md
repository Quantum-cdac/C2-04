# 08 - AI / LLM Usage Disclosure

Per the hackathon Development Rules ("AI tools are permitted for coding, debugging, research and documentation. Teams review, validate and explain AI-assisted work and disclose material AI-tool use."):

## Tools used

- **Instinct** (AI assistant platform) - implemented this module end to end during the event period: parser, IR, QSDK builder, decomposition fallback, reference simulator, tests, examples and documentation, and ran the offline test suite.

## What the team did with the output

- Ran the SDK integration suite in the venue Qniverse notebook against the preinstalled SDK (4 passed, recorded with the manual Bell conversion figures in `docs/05-test-plan-and-results.md`).
- Review of the generated code against the problem statement and the QSDK documentation, and the ability to explain the architecture (parser -> IR -> documented QSDK builder), the supported subset, the register-renaming rule and the equivalence method, remain the team's responsibility under the rules; the team members presenting this module are expected to complete that review before submission.

## Data handling

The Qniverse API key is never embedded in code, docs or messages; remote execution uses each member's own registered account, with the key entered locally in the notebook only.
