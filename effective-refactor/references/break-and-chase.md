# Break and chase: error surfaces and the Mikado escalation

Break the definition, then let a checker enumerate every affected site as a
to-do list with file and line attached. The technique is practitioner lore
best articulated as "leaning on the compiler" (Ayende Rahien,
<https://ayende.com/blog/179842>, and the Working Effectively with Legacy Code
tradition); this file maps it onto each language's error surface.

## Error surfaces by language

| Language | Primary surface | Command | Notes |
| --- | --- | --- | --- |
| C# | Compiler | `dotnet build` | Solution-wide, precise; the canonical case |
| C / C++ | Compiler | project build, ideally one TU or target | Keep the loop narrow; full builds kill the iteration speed |
| Go | Compiler | `go build ./...` (`go vet` for extras) | Fast enough to run on every fix |
| Rust | Compiler | `cargo check` | Faster than `cargo build`; type-driven refactoring is idiomatic here |
| Java | Compiler | Maven/Gradle compile of the touched module | |
| TypeScript | Type checker | `tsc --noEmit` | `strict` plus `noUnusedLocals`/`noUnusedParameters` also catches half-finished remnants |
| Python | Type checker | `pyright` or `mypy --strict` | pyright checks unannotated code by default; mypy skips unannotated functions unless configured - pick the surface that actually covers the target |
| Anything else | Test suite | full or targeted run | Coarsest surface: coverage gaps are invisible, so pair with a final grep |

The surface's completeness bounds the technique's safety. A compiler sees
every reference; a type checker sees what is typed; a test suite sees what is
covered. Whatever the surface, finish with a grep for the old name expecting
zero hits - strings, comments, docs, reflection targets, and serialized keys
are invisible to all of them.

## Working the list

- Fix sites in checker order, not repo order; re-run after each few fixes.
  The list re-derives itself, so it never goes stale the way a grepped list
  does.
- Sometimes the right fix at a call site is to push the change one layer up
  (the caller's caller takes the new parameter). That is normal; the next run
  extends the list to the new layer.
- Keep the loop fast. If a check costs minutes, scope it down (one package,
  one target) before starting, or the iteration count makes the technique
  worse than a mechanical tool.

## Dynamic-language footnote

In Python and JavaScript without strict typing, the "compiler" is whatever you
make it: turn on `pyright` strict for the touched package, or lean on import
errors (delete the module, run the entry points) plus the test suite. If none
of those surfaces cover the call sites, treat the refactor as higher-risk and
prefer a semantic tool or add types to the seam first.

## Mikado: when the wave is too big

If the first break produces more errors than one sitting can clear, or fixing
a site reveals a prerequisite refactor, do not push through a red tree:

1. Write the goal down. Attempt it naively.
2. Every resulting error class becomes a prerequisite node under the goal.
3. **Revert to green.** The graph, not the diff, was the deliverable.
4. Pick a leaf prerequisite (no prerequisites of its own), do it as a small
   break-and-chase, commit on green.
5. Repeat until the original goal is itself a leaf, then do it.

Reference: the Mikado Method (Ellnestam and Brolund, Manning). The revert step
is the part agents skip and must not: exploratory breakage is for learning the
graph, and carrying it forward as WIP turns a survey into an unattributable
mess.

## The read-only probe

"What would break if we removed X?" is answerable empirically in minutes: on a
scratch branch, delete X, run the error surface, save the error list, revert.
The harvested list feeds a plan (or a Mikado graph) with real data instead of
speculation. Never let the probe's breakage leak into the working branch.
