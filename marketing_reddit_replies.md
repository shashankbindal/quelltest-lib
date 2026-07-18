# Reddit reply drafts — July 2026

Ground rules baked into every draft below:
- **Always disclose** you built Quelltest ("I build a tool in this space" / "disclosure: my project").
  Undisclosed self-promo gets nuked by mods and poisons the brand; disclosed expertise performs better anyway.
- Lead with a genuinely useful answer that stands alone even if the reader never clicks anything.
- Mention the product at most once, at the end, only where it's on-topic. Some drafts don't mention it at all — those build account credibility.
- Never post the same text twice; retype/vary. Reddit's spam filter and users both notice.
- Only reply in threads where the question is real. Don't necro old threads.

---

## Thread type 1 — r/Python or r/learnpython: "How do you test edge cases you didn't think of?"

> The uncomfortable answer: your codebase already lists most of them, you just never turned the list into tests. Docstrings that say "raises ValueError if amount <= 0", Pydantic fields with `gt=0`, `Optional` params, guard clauses — every one of those is a documented edge case, and in most codebases the majority have no test asserting them.
>
> A cheap manual version: grep your code for `raise` and for Pydantic `Field(` constraints, then check whether a test actually feeds the violating input. You'll usually find the docs promise behavior nobody verifies.
>
> The second trick that changed how I test: after writing a test, break the code on purpose (flip the comparison, delete the guard) and make sure the test goes red. A test that can't fail is decoration.
>
> Disclosure: I got obsessed enough with this that I built a tool that automates exactly that loop for Python (quelltest on PyPI) — but the grep + break-it-on-purpose combo works with zero tooling.

## Thread type 2 — r/ExperiencedDevs: "Anyone else not trusting AI-generated tests?"

> The failure mode I keep seeing isn't that AI tests are bad — it's that they're *self-consistent*. The agent writes the implementation and the test from the same (possibly wrong) understanding, so both agree, CI is green, and the review reads clean. The bug ships with a seatbelt on.
>
> What's worked for us: don't review AI tests by reading them. Review them by execution — inject the violation each test claims to catch and require a red result. It's mutation testing scoped per-test, and it filters out the `assert result is not None` genre instantly. In my own experiment (a week of letting the agent write every test), roughly 1 in 5 deliberately-broken versions of the code still passed the generated suite. The surviving tests after violation-checking were genuinely good.
>
> The research backs this up if you want ammunition for your team: Inozemtseva & Holmes (ICSE 2014) on coverage not predicting effectiveness, Just et al. (FSE 2014) on mutant detection tracking real-fault detection.
>
> (Disclosure since I'm citing my own workflow: I build a Python tool around this idea, but the practice is tool-independent.)

## Thread type 3 — r/ClaudeAI or r/ClaudeCode: "Best MCP servers for Python dev?"

> A category I'd suggest beyond the usual (filesystem, GitHub, Playwright): verification servers — tools that let the agent *prove* its own output instead of just producing more of it.
>
> The loop that's been great for me in Claude Code: agent writes a function → calls a testing MCP tool that finds what's untested → writes the tests → the tool verifies each test actually fails when the code is broken → agent reads the flagged gaps and fixes testability. All in-session, no terminal round-trips.
>
> Disclosure: the one I use is my own project (quelltest — local stdio server, ships in the pip package, `pip install "quelltest[mcp]"`, nothing leaves the machine). Whatever tool you pick, the pattern of giving the agent a verifier and not just a generator is the upgrade.

## Thread type 4 — r/Python: "Is 100% coverage worth it?" (no product mention — credibility builder)

> The research answer is clearer than the dashboard answer: coverage is a good map and a bad target. Inozemtseva & Holmes (ICSE 2014) generated ~31k test suites and found that once you control for suite size, coverage correlates only weakly with how many faults a suite catches. Their own conclusion: use it to find *untested* areas, don't use it as a quality gate.
>
> The practical version: 100% coverage with weak asserts is strictly worse than 70% coverage with tests that die when the code breaks, because the 100% number makes people stop looking.
>
> Quick self-audit that costs five minutes: pick your most-covered module, flip one boundary condition, run the suite. If it stays green, the coverage number was lying to you. What that exercise measures — fault detection — is the thing worth gating on.

## Thread type 5 — r/programming, on any "AI wrote X% of our code" news item

> The interesting number in these stories is never the generation percentage — it's that verification capacity stayed flat while generation went up 50x. Review depth per line has quietly collapsed everywhere; we've gone from reading code to skimming narratives about code.
>
> Generation being cheap means the scarce good is now *proof*: mechanical evidence that the code does what its own docs claim. Specs already exist in the code (docstrings, type constraints, guard clauses); tests can be validated by injecting the violation and requiring a failure. None of that needs AI to be less capable — it needs the gate to be un-gameable by high-throughput generators, human or otherwise.

---

## Posting cadence suggestion

- 1–2 replies/week max, spread across subs; prioritize threads < 24h old with real questions.
- Alternate: two no-mention credibility replies (types 4/5) for every one product-mention reply (types 1/2/3).
- If a mod or user pushes back on the mention, don't argue — the disclosure was upfront; just engage on substance.
