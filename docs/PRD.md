# Product Requirements

The product is a standalone Thief peer that completes six-subgame Police-and-Thief series
over P2P FastMCP while preserving partial observability and producing independently
verifiable evidence.

Primary users are the student operator, an independently implemented Police peer, and the
course evaluator. Success requires legal autonomous play, bounded network behavior, valid
commit-reveal audit, matching result artifacts, a local-truth GUI, verified replay, and
separate report delivery.

Constraints include Python 3.12, separate processes/repositories, no central judge, fixed
Appendix F values, no committed secrets, source files no longer than 150 lines, and at
least 85 percent statement/branch coverage.

