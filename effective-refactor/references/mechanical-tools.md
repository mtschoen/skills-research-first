# Mechanical refactoring tools by language

One semantic tool invocation beats N hand edits. Pick from this table before
editing call sites by hand. Verify every mechanical pass with `git diff` review
and the test suite before committing it as its own commit.

| Language | Rename | Extract | Structural rewrite | Notes |
| --- | --- | --- | --- | --- |
| C# / .NET | `roslynator rename-symbol` (solution-wide) | No CLI extract; Rider/ReSharper GUI only | `roslynator analyze` + `fix` applies analyzer code fixes; `dotnet format` for style analyzers | Roslynator CLI is the mature scriptable option |
| C / C++ | `clang-rename` (`-offset` or `-qualified-name`, needs `compile_commands.json`); clangd LSP rename | None native | `clang-tidy -fix`; mass mode via `-export-fixes` + `clang-apply-replacements` | |
| Python | `rope` library (third-party `ropecli` wraps it) | rope: extract method/variable via its API | `libcst` codemods | Bowler is archived; LibCST is its successor |
| TypeScript / JS | `ts-morph` rename (updates references and imports; small script) | ts-morph AST manipulation, no one-liner | `jscodeshift` codemods | ts-morph wraps the TypeScript compiler API |
| Go | `gopls rename -write file.go:line:col newname` | `gopls` extract code actions via LSP | `gofmt -r 'pattern -> replacement' -w` for expression rewrites | `gorename` is being removed from x/tools; use `gopls rename` |
| Rust | rust-analyzer LSP rename only - no standalone CLI subcommand | LSP code actions in-editor only | None beyond LSP | Drive via an LSP client or fall back to break-and-chase (`cargo check` is excellent) |
| Java | OpenRewrite recipes (Maven/Gradle plugin; Moderne CLI for multi-repo) | Author a recipe, or Spoon for custom AST transforms | OpenRewrite recipe YAML/Java | Recipes are deterministic, CI-safe |
| Any | - | - | `ast-grep` (tree-sitter structural search/rewrite, many languages); `comby` (template syntax, nearly any language); Semgrep rules with `fix:` | The fallback when no language-specific tool covers the target |

## Caveats and traps

- **JetBrains CLI does not rename.** ReSharper/Rider `CleanupCode` is
  formatting and style cleanup only; the semantic refactorings are GUI-only.
  Do not plan a headless pipeline around them.
- **LSP-based renames without an editor** (rust-analyzer, clangd, pyright)
  need an LSP client. If the harness exposes an LSP tool or an LSP MCP bridge
  is installed, use it; otherwise prefer a standalone CLI from the table or
  break-and-chase.
- **Structural tools are syntactic.** `ast-grep`, `comby`, and `gofmt -r`
  match shapes, not symbol bindings - they will happily rewrite a same-named
  symbol from another scope. Constrain patterns tightly and review the diff
  hunk by hunk.
- **Community MCP wrappers** around Roslyn and gopls exist in varying states
  of maturity; treat them as options to evaluate, not defaults.
