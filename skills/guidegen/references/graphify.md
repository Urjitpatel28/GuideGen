# Optional input: graphify

Use this only if `graphify-out/graph.json` or `graphify-out/GRAPH_REPORT.md` exists **and** config `graphify.use` is
`"auto"` or `true`. GuideGen never installs or runs graphify.

- **Chapters**: `GRAPH_REPORT.md` communities (clusters of related files) name the product areas. Put screens
  whose `source` files fall in the same community into the same `group` (for example `group: Billing`). The
  Screen Reference renders one sub-chapter per group. Use user words for group names, not package names.
- **Task candidates**: "god nodes" and central paths between UI files and services often mark core workflows
  (for example a checkout flow that touches cart, pricing and order modules). Add them as task candidates with
  `evidence: {type: graphify, ref: "<community or node>"}`, then verify them live like any other task.
- Without graphify the manual must still be complete. It only improves grouping and ranking.
