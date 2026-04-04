---
title: "Harness Design Is Becoming the Real Moat in AI Agents"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/harness-design-long-running-ai-agents"
published_date: "2026-03-26"
license: "CC BY 4.0"
---
# Harness Design Is Becoming the Real Moat in AI Agents

## Anthropic’s new long-running agent research shows why the orchestration layer now matters as much as the model

On March 24, 2026, Anthropic published one of the most important agent engineering pieces of the year: **“Harness design for long-running application development.”** The headline examples were flashy enough to get attention. A six-hour autonomous run produced a retro game maker. A later four-hour run produced a browser-based DAW. But the real value of the post is not the demos. It is the admission that **the harness around the model is often the real system**. [read](https://www.anthropic.com/engineering)

That matters far beyond coding.

If you are building specialized agents for compliance audits, risk analysis, policy reviews, research pipelines, content operations, or impact assessments, the same principle applies. The model is not the product. The **orchestration layer** is the product. Anthropic’s own definitions support that generalization: in its agent evals guidance, the company defines an **agent harness** as the system that enables a model to act as an agent by processing inputs, orchestrating tool calls, and returning results. Anthropic also positions the Agent SDK as a broader platform for real agents beyond code, including example agents such as an email assistant and a research agent. [read](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## Most teams are still optimizing the wrong thing

A lot of teams are still behaving as if the main question is model choice.

That is too shallow now.

Anthropic’s own progression across its engineering posts points to a more useful reality. In December 2024, the company argued that the most successful agent implementations usually rely on **simple, composable patterns** rather than unnecessary complexity. In September 2025, it reframed the problem as **context engineering**, arguing that the central challenge is not just prompt wording but the broader configuration of context, tools, history, and state available to the model at any given moment. In January 2026, it expanded that logic into evals, showing that agents need structured grading, trace review, and reliable environments because agent behavior compounds over time. The March 2026 harness post is the next step in that arc: if you want long-running performance, you need to design the system around the model’s real behavior. [read](https://www.anthropic.com/engineering/building-effective-agents)

That is the strategic insight leaders should take from this.

The market likes to talk about raw intelligence. Production teams should care more about **durability**. Can the agent hold a goal over time? Can it work across state changes? Can it hand off context cleanly? Can it be judged by something more skeptical than itself? That is where the harness starts to matter more than the benchmark. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

## What Is Harness Design for AI Agents?

The simplest way to explain a harness is this: it is the software and structure that turns a model into a working system.

That includes prompts, tools, memory, state handling, review loops, stop conditions, evaluation logic, permissions, and the way context is curated or reset between runs. Anthropic’s eval guidance makes the distinction cleanly: the **agent harness** is the system that lets the model act, while the **evaluation harness** is the infrastructure that runs tests end to end, grades results, and aggregates performance. When teams say “the agent did this,” they are usually describing the behavior of the model and the harness together. [read](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

That distinction is critical for consulting work.

It means the right question is rarely “Which model should we buy?” The better question is “What harness do we need for this workflow to become reliable?” In my view, this is exactly where AI consulting is moving. Not toward generic tool recommendations, but toward **harness design as an operating discipline**, a core practice in our AI Strategy Consulting. That inference follows directly from Anthropic’s own framing: the company explicitly says harness design had a substantial impact on long-running performance, and that the interesting work now lies in finding the next novel combination of harness components as models improve. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

## Anthropic identified two failure modes that matter everywhere

The most useful part of the new post is how candid it is about failure.

Anthropic says two problems kept appearing in long-running autonomous work. The first was **context anxiety**. As the context window filled, some models began wrapping up early, losing coherence, or trying to finish before the task was truly done. Anthropic says this showed up strongly enough in Sonnet 4.5 that **context resets** became essential in its earlier harness design, because compaction alone still preserved enough continuity for the model to remain anxious about the limit. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

The second was **self-evaluation**. Anthropic says agents tend to praise work they have produced even when the output is obviously mediocre to a human reviewer. That mattered most in design, where “good” is subjective, but Anthropic is explicit that the problem also appears in tasks with verifiable outcomes. The fix was not magical self-awareness. It was **role separation**: one agent generates, another evaluates. Anthropic says tuning a standalone evaluator to be skeptical turned out to be much more tractable than trying to make the generator judge itself honestly. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

These are not coding-only lessons.

A compliance review agent can also rush toward closure when the evidence trail gets large. A content pipeline agent can also overpraise weak output if it is asked to judge its own work. A risk analysis agent can also stop short if the system has no meaningful definition of “done.” The pattern generalizes because the failure modes are structural, not domain-specific. That is my inference, but it is grounded in Anthropic’s definitions of harnesses, multi-turn evals, and context engineering across agent types. [read](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## The evaluator is the story

Anthropic’s frontend experiment is where the post becomes especially interesting.

Instead of asking a model vague questions like “Is this beautiful?”, Anthropic built grading criteria that made subjective quality more **gradable**: design quality, originality, craft, and functionality. It weighted design quality and originality more heavily because the model already performed reasonably on craft and functionality, but tended to produce bland, generic outputs on the more subjective dimensions. Anthropic then gave the evaluator **Playwright MCP**, so it could navigate the page directly, inspect the implementation, and produce detailed critiques over repeated iterations. In one example, that loop eventually pushed a Dutch art museum website into a radically more distinctive design direction than a single-pass generation produced. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

The consulting lesson here is massive.

If you want better agents in subjective domains, stop asking them vague, elegant-sounding questions. Start translating taste into **criteria**. That does not make the work fully objective, but it makes quality more operational. The same move applies to legal writing, audit narratives, board memos, content quality, vendor risk summaries, and policy assessments, all areas where expert AI Governance & Risk Advisory is crucial. You do not ask, “Is this good?” You ask, “Does this meet our principles for completeness, specificity, originality, evidence, tone, usability, and decision-value?” Anthropic’s work is a strong signal that **gradable criteria are the bridge between subjective judgment and usable iteration**. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

## The Planner-Generator-Evaluator Loop in Harness Design for AI Agents

The full-stack section of Anthropic’s post is where the article becomes operationally important.

For the retro game maker, Anthropic moved to a three-agent system: **planner, generator, evaluator**. The planner took a short prompt and expanded it into a broader spec. The generator built the app in sprints. The evaluator used Playwright to exercise the application like a user, checked sprint criteria, and failed any sprint that fell below threshold. Anthropic reports that the solo run took 20 minutes and cost $9, but produced a broken result. The full harness took six hours and cost $200, but the resulting app was materially richer and actually playable. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

That tradeoff is exactly what business leaders need to understand.

The cheapest run is often the most expensive system if it produces weak, unverifiable, or incomplete work. Anthropic’s own logs show why the evaluator mattered: it caught concrete issues like broken rectangle fill behavior, faulty entity deletion logic, and API route ordering bugs. Anthropic also admits that getting the evaluator to this level was not plug-and-play. Out of the box, Claude was a poor QA agent, initially identifying real issues and then talking itself into approving them anyway. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

That admission should reset expectations across the industry.

A production evaluator is not a nice extra. It is its own product problem.

## Better models change the harness, not the need for one

One of the strongest sections in the post is the simplification story.

Anthropic did not treat the original harness as sacred. It removed components one by one and tested which ones were still load-bearing. With Opus 4.6, Anthropic says it was able to remove the sprint structure and stop relying on context resets because the model could sustain longer autonomous work with compaction alone. It kept the planner and evaluator because they were still adding obvious value. Then it used the simplified harness to build a browser-based digital audio workstation from a one-line prompt. That run took about **3 hours 50 minutes** and **$124.70**, with the evaluator still catching missing core interactions such as clip drag behavior, instrument panels, visual effect editors, audio recording, clip split, and graphical EQ views. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

That is the lesson most teams will miss.

The takeaway is not “context resets are dead” or “evaluators are always required.” Anthropic’s actual lesson is subtler and more valuable: **every harness component encodes an assumption about what the model cannot yet do**, and those assumptions must be re-tested as models improve. Anthropic says the practical implication is to re-examine a harness whenever a new model lands, stripping away pieces that are no longer load-bearing and adding new ones that unlock capabilities the older model could not support. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

That is why I think harness design is becoming a serious consulting layer. It is not a one-time architecture diagram. It is a living operating system.

## What this means outside coding

Here is where I think this becomes commercially important for First AI Movers and for AI consulting more broadly.

The case studies in Anthropic’s post are coding-heavy. But Anthropic’s own materials make clear that the platform is broader than coding. The Agent SDK is presented as a way to build production AI agents generally, and Anthropic points to example agents such as an email assistant and a research agent. Its broader solution pages also place AI agents across domains including customer support, financial services, government, and life sciences. Anthropic’s 2024 guidance on building effective agents also says agentic systems are most useful when tasks are open-ended, tool-using, and require adaptation over multiple turns. [read](https://docs.anthropic.com/en/docs/claude-code/sdk)

So the practical extension is straightforward:

- **Compliance audits** need planner logic, evidence gathering, and skeptical evaluation.
- **Risk analysis agents** need criteria, thresholds, and independent challenge, not just fast drafting.
- **Content pipelines** need generation separated from editorial review and brand-quality grading.
- **Impact assessments** need clear definitions of done, traceable artifacts, and structured handoffs.

That is not a metaphor. It is the same design pattern moving into different business domains. [read](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## My take

The frontier is shifting.

For a while, the winning move was access to a better model. Then it became access to better tools. Now the harder and more valuable problem is **designing the harness** that makes the model useful over time.

That is why this Anthropic post matters so much.

It shows that long-running agent performance is not just about more tokens, bigger context windows, or nicer demos. It is about whether you can structure planning, execution, evaluation, handoffs, and simplification in a way that matches the model’s real strengths and weaknesses. Anthropic’s own conclusion is that the interesting harness space does not shrink as models improve. It moves. I think that is exactly right. [read](https://www.anthropic.com/engineering/harness-design-long-running-apps)

The companies that win from here will not just deploy agents. They will know how to **engineer the harness around them**.

And that is where serious consulting work creates value:

- choosing when a task needs a planner,
- deciding whether an evaluator is worth the cost,
- defining what “good” looks like in domains without binary tests,
- building the right handoff artifact,
- and revisiting the whole design when the model changes.

That is not prompt engineering.

That is system design.

## Further Reading

- [AI Agents for Business Workflow Redesign](https://radar.firstaimovers.com/ai-agents-for-business-workflow-redesign)
- [Agentic AI Systems vs Scripts 2026](https://radar.firstaimovers.com/agentic-ai-systems-vs-scripts-2026)
- [LangGraph vs LangChain CrewAI Autogen 2026](https://radar.firstaimovers.com/langgraph-vs-langchain-crewai-autogen-2026)
- [Scaling Agentic AI 1000 RPS Architecture 2026](https://radar.firstaimovers.com/scaling-agentic-ai-1000-rps-architecture-2026)

---

_Written by [Dr Hernani Costa](https://drhernanicosta.com), Founder and CEO of [First AI Movers](https://www.firstaimovers.com). Providing AI Strategy & Execution for Tech Leaders since 2016._

Subscribe to [First AI Movers](https://firstaimovers.com) for practical and measurable business strategies for Business Leaders. [First AI Movers](https://www.linkedin.com/company/first-ai-movers/) is part of [Core Ventures](https://coreventures.xyz).

**Ready to increase your business revenue?**
Book a [call](https://calendar.app.google/RJnKGg3b8ZRfhect5) today!

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/harness-design-long-running-ai-agents) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*