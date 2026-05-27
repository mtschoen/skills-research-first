# Restructure Over Exclude

When a test is slow or a coverage gap is hard to fill because the production code tangles things that
shouldn't be tangled — startup side effects, untestable singletons, network calls inline with business
logic — the right move is to refactor the production code, not to add coverage exclusions or weaken
assertions.
This is the same lever as deleting dead code: it improves the codebase.
Restructuring to be testable is not overkill.

## Worked example

```kotlin
// Before: Kover counts the while-false branch as uncovered
while (isActive) {
    delay(1000)
    evictExpired()
}

// After: no unreachable branch (delay() throws CancellationException on cancellation)
while (true) {
    delay(1000)
    evictExpired()
}
```

The `while (isActive)` form has a synthetic false branch the coverage tool can't reach
(the cooperative-cancellation idiom never executes the loop exit at false; cancellation is by exception).
Restructuring to `while (true)` eliminates the branch without changing behavior — cancellation still
works via the `CancellationException` thrown by `delay`.

## Python

Async cooperative cancellation: `asyncio.CancelledError` is the equivalent exception.
A `while running:` loop with a separate `running = False` cancellation signal has the same
uncovered-false-branch shape as the Kotlin example above.
Restructure to `while True:` and let `CancelledError` propagate.

## .NET

`CancellationToken.ThrowIfCancellationRequested()` inside `while (true)` is the .NET equivalent.
The same restructure applies: replace `while (!token.IsCancellationRequested)` with `while (true)`
and let the exception exit the loop.

## The legitimate exclusion case

Coverage exclusion is correct for genuinely-untestable framework bindings — Android `MediaCodec`,
`NSDManager`, XR Compose composables that require a running platform.
Exclude those *specifically*, not whole-class blanket exclusions on production logic.

If the exclusion attribute lands on a class whose name doesn't end in `Binding` or `Adapter` or a
similar platform-glue suffix, that's a code smell that wants restructuring first.
