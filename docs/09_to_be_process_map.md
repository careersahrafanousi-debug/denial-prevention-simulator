# To-Be Process Map — Denial Prevention Simulator

```mermaid
flowchart TD
    A[Service delivered] --> B[Charge entered]
    B --> C[Automated pre-submission check runs all five rules]:::ctrl
    C --> D[Preventable Denial Risk score assigned]:::ctrl
    D --> E{Risk band}
    E -- Low --> F[Submit automatically]
    E -- Medium --> G[Billing checklist, same-day review]:::ctrl
    E -- High --> H[Exception queue routed to rule owner]:::ctrl
    H --> I{Gap resolved?}
    I -- Yes --> J[Re-score]:::ctrl
    I -- No --> K[Supervisor decision: hold or submit with documented exception]:::ctrl
    J --> E
    G --> F
    K --> F
    F --> L[Payer adjudicates]
    L --> M{Denied?}
    M -- No --> N[Paid]
    M -- Yes --> O[Recovery Priority score assigned]:::ctrl
    O --> P[Worked in priority order by owning queue]:::ctrl
    P --> Q[Outcome recorded with root cause]:::ctrl
    Q --> R[Monthly rule recalibration]:::ctrl
    R --> C
    N --> S[Certified reporting: preventable and non-preventable separated]:::ctrl

    classDef ctrl fill:#e8f4ea,stroke:#1e7b34,color:#14532d;
```

## Controls introduced

| Control | Addresses | Owner |
|---|---|---|
| Automated five-rule pre-submission check | P1, P2 | Billing Manager |
| Risk-band routing instead of claim-type routing | P3, P4 | Billing Manager |
| Owner-assigned exception queues | P1, P2 | Rule owners per `prevention_rules.csv` |
| Documented submit-with-exception path | avoids new backlogs | Billing Supervisor |
| Recovery priority ordering | P5 | Denial Analyst |
| Root-cause capture at resolution | P6 | Revenue Cycle Director |
| Monthly rule recalibration | P6 | Revenue Cycle Director |
| Separated preventable reporting | P6 | Analyst |

The submit-with-documented-exception path matters. A hard hold with no release valve just
converts a denial problem into an aging problem, which is how well-intentioned edit rules get
switched off six months later.
