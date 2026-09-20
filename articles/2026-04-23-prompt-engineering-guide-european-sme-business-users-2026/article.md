---
title: "How to Write Prompts That Actually Work: A Business User's Guide for European SMEs"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/prompt-engineering-guide-european-sme-business-users-2026"
published_date: "2026-04-23"
license: "CC BY 4.0"
---

> **TL;DR:** Practical prompt engineering guide for non-technical European SME staff. Five patterns for Claude, ChatGPT, and Gemini, with GDPR privacy rules.

Most people in small and mid-sized businesses who use AI tools spend the first few weeks frustrated. The tool produces generic, off-target answers. They assume the tool is the problem. Usually, the problem is the prompt. Why this matters: a well-structured prompt can turn a 10-minute rewrite into a 90-second task, and the difference between a vague prompt and a precise one is a handful of sentences, not technical expertise. This guide is for operations leaders, department managers, founders, and anyone at a growing company in Europe who uses Claude, ChatGPT, or Gemini for day-to-day work and wants consistently better results without needing a developer to explain it.

You will also find a section on what not to put in a prompt, which matters especially in Europe where GDPR governs how personal data can be handled by third-party services.

---

## Why Prompts Fail and What to Do About It

The most common reason a prompt produces a poor result is not that the AI is unintelligent. It is that the AI has received insufficient context to choose between several plausible interpretations of your request.

"Write a summary of this meeting" could mean: a three-line executive summary for the CEO, a detailed action-item list for the project team, a client-facing recap for an email, or a compliance record for an internal audit trail. Without guidance, the AI picks one interpretation. It may not be yours.

The five patterns below give the AI the context it needs to make the right choice the first time. They work across Claude, ChatGPT, and Gemini. They require no technical knowledge. They take about 30 seconds longer to write than a vague prompt, and they produce results that require significantly less editing.

---

## Pattern 1: Role + Context + Task

The most reliable general-purpose prompt structure. Tell the AI who you want it to be, give it the relevant background, then state the task.

Structure: "You are [role]. [Context]. [Task]."

Example for a client email: "You are a senior account manager at a professional services firm. Our client, a 30-person logistics company, has just asked us to extend a project deadline by three weeks. We agreed internally. Write a short email (under 150 words) confirming the extension, thanking them for their patience, and outlining the revised delivery date of 15 June."

What changes when you add the role: the AI adopts a register appropriate to client communication rather than generic business writing. The context prevents it from making up project details. The task specification sets the length and structure before the AI starts.

Use this pattern for: client communications, internal briefings, policy summaries, onboarding documents.

---

## Pattern 2: Output Format Specification

Many unhelpful AI responses are not wrong in content but wrong in format. A wall of prose when you needed bullet points. Five paragraphs when you needed a table. A numbered list when you needed flowing text for a presentation slide.

Add your format requirement explicitly, at the start of the prompt rather than the end.

Example for a supplier comparison: "Format your response as a table with four columns: Supplier Name, Key Strength, Key Risk, Recommended Use Case. Do not include introductory paragraphs. Here are the three suppliers we are evaluating: [paste supplier information]."

Formats you can specify: bullet list, numbered list, table, one-paragraph summary, two-sentence TL;DR, slide-ready bullets (under 8 words each), JSON (useful when passing output to another tool), step-by-step instructions, FAQs.

For a department manager preparing a board report, output format specification is the single change that saves the most editing time. The AI already knows the content; you are just telling it how to arrange it.

---

## Pattern 3: Step-by-Step Reasoning

For analytical tasks, asking the AI to show its reasoning before giving a conclusion produces more reliable output. This is because the AI is less likely to jump to a convenient answer if it has been asked to work through the evidence first.

Structure: "Think through this step by step before giving your final answer."

Example for contract analysis: "Read the following supplier contract clause. Think through the implications step by step: first, what does the clause require us to do? Second, what happens if we do not comply? Third, is there anything in the clause that is unusual or that we should ask a lawyer to review? Then give your final assessment. [Paste clause text.]"

This pattern is especially useful for: analysing terms and conditions, reviewing supplier proposals, assessing risk in procurement decisions, evaluating options where trade-offs exist.

One caution: step-by-step reasoning makes responses longer. If you need a brief output, ask for step-by-step reasoning followed by a one-sentence conclusion.

---

## Pattern 4: Few-Shot Examples

The fastest way to align the AI with your house style, your tone, or your specific format is to show it an example of what you want before you ask for the new version.

Structure: "Here is an example of the kind of output I need: [example]. Now write the same type of content for: [new input]."

Example for meeting summaries: "Here is an example of how we summarise meetings internally: [paste one previous summary]. Using the same format and tone, summarise the following meeting notes: [paste new notes]."

This pattern is also useful for: keeping AI-generated emails consistent with your company voice, producing reports that match your standard template, generating social media posts that follow your editorial style.

For a finance team or operations function that produces the same type of document repeatedly, creating a short library of three to four examples to reuse in prompts eliminates most style editing entirely. A founder-led company with a strong brand voice will find this pattern particularly valuable for maintaining consistency across staff who use AI tools independently.

---

## Pattern 5: Constraint Setting

Constraints tell the AI what to leave out. Without them, the AI tends to be comprehensive, which is often not what you need in a business context where brevity signals professionalism.

Useful constraints: word or character limits, exclusions ("do not mention pricing"), perspective requirements ("write from the client's point of view, not ours"), audience restrictions ("assume the reader has no technical background"), and tone controls ("formal, not friendly").

Example for an internal report: "Summarise the attached survey results in under 200 words. Do not include raw numbers or percentages. Focus only on the three most significant patterns. Write for a non-technical audience. Use plain language."

Combine constraint setting with Pattern 1 and Pattern 2 for the most controlled output: role tells the AI who it is, format tells it how to structure the response, and constraints tell it what to exclude.

---

## GDPR: What You Must Not Put in a Prompt

This section applies to all European SME staff using any AI tool, including Claude, ChatGPT, and Gemini. It is not optional.

When you paste text into an AI tool, that text is processed by the tool's servers. Under GDPR, personal data cannot be sent to a third-party processor without a lawful basis and, in most cases, without a Data Processing Agreement in place with that processor.

Practical rule: do not paste the following into an AI prompt unless your company has confirmed a DPA is in place with the AI provider and that processing is covered.

Items to exclude from prompts:
- Full names of customers, employees, or business contacts
- Email addresses or phone numbers
- National identity numbers, tax reference numbers, passport numbers
- Health or financial data relating to an individual
- Home addresses or precise location data
- Any combination of data points that would identify a specific person

What you can do instead: replace personal identifiers with generic labels before pasting. "Our customer Maria Schmidt in Berlin" becomes "our customer in Germany." "Employee ID 4421 earning €62,000" becomes "an employee in the mid-salary band." The AI can still do useful analytical work on anonymised or pseudonymised data.

EU AI Act transparency obligations also apply here. From 2026, business users deploying AI-generated content in customer-facing contexts may have labelling obligations. If you are using AI to draft customer communications, check with your legal team whether disclosure is required in your sector.

For a deeper view of shadow AI risk in business settings, see [Shadow AI Detection and Governance for European SMEs](https://radar.firstaimovers.com/shadow-ai-detection-governance-european-smes-2026).

---

## Four Concrete Examples by Business Function

**Writing a meeting summary (operations leader):** "You are an executive assistant summarising an internal meeting for the leadership team. The meeting covered Q2 budget allocation, a new supplier contract, and a hiring decision. Format your summary as: (1) decisions made, (2) actions required with owners, (3) open questions. Use no more than 250 words. Here are the meeting notes: [paste notes]."

**Drafting a client email (account manager at a mid-sized company):** "You are a senior relationship manager at a consulting firm. Write a 120-word email to a long-standing client explaining that we are raising our day rate by 8% from 1 July. The tone should be direct and confident, not apologetic. Do not include a justification for the increase unless asked."

**Analysing a supplier contract (operations or procurement):** "Read the following termination clause from a supplier contract. Think step by step: what are our obligations under this clause? What notice period applies? Is there anything unusual that a lawyer should review? Give your assessment in three short paragraphs. [Paste clause.]"

**Creating a report for leadership (department manager):** "Format your response as a one-page briefing for a board audience. Use the following structure: Situation (2 sentences), Key findings (4 bullet points, each under 15 words), Recommended action (1 sentence). Do not use jargon. Here is the background: [paste data or notes]."

---

## Building a Personal Prompt Library

The most effective business users of AI tools do not start from scratch every time. They maintain a short document, sometimes called a prompt library, containing their five to ten most reused prompt templates with placeholders for the variable parts.

A prompt library does not need to be complex. A shared document in your team's workspace with sections by function (communications, analysis, reports, summaries) and a few tested examples per section will save every team member the trial-and-error phase on each new task.

For a structured view of how European SMEs should be building AI governance frameworks that support safe and effective use by non-technical staff, see [Fractional CTO AI Governance for European SMEs](https://radar.firstaimovers.com/fractional-cto-ai-governance-lead-european-smes-2026).

---

## Frequently Asked Questions

### Do these prompt patterns work the same way on Claude, ChatGPT, and Gemini?

Largely yes. The five patterns described here (role plus context plus task, output format, step-by-step reasoning, few-shot examples, constraint setting) reflect how large language models process instructions, not how any one product is designed. You may see small differences in default verbosity or tone between tools, but the same structured prompt will outperform a vague prompt on any of the three platforms.

### How long should a prompt be?

Long enough to eliminate ambiguity, short enough to stay focused. For most business tasks, a prompt of three to six sentences is sufficient if it includes role, context, task, and at least one format or constraint instruction. Prompts do not need to be long; they need to be precise.

### What should we do if the output still misses the mark?

Treat the first response as a draft and use the conversation. Reply with a specific correction rather than starting again: "The tone is too formal for this audience. Rewrite the second paragraph to be more direct and less deferential." Iterating within a session is faster than rewriting the prompt from scratch and produces better calibration over time.

---

## Further Reading

- [Shadow AI Detection and Governance for European SMEs](https://radar.firstaimovers.com/shadow-ai-detection-governance-european-smes-2026)
- [AI Vendor Evaluation Scorecard for European SMEs](https://radar.firstaimovers.com/ai-vendor-evaluation-scorecard-european-smes-2026)
- [Fractional CTO AI Governance for European SMEs](https://radar.firstaimovers.com/fractional-cto-ai-governance-lead-european-smes-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to Write Prompts That Actually Work: A Business User's Guide for European SMEs",
  "description": "Practical prompt engineering guide for non-technical European SME staff. Five patterns for Claude, ChatGPT, and Gemini, with GDPR privacy rules.",
  "datePublished": "2026-04-23T12:02:54.933579+00:00",
  "dateModified": "2026-04-23T12:02:54.933579+00:00",
  "author": {
    "@type": "Person",
    "@id": "https://radar.firstaimovers.com/page/dr-hernani-costa#dr-hernani-costa",
    "name": "Dr. Hernani Costa",
    "url": "https://radar.firstaimovers.com/page/dr-hernani-costa"
  },
  "publisher": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://radar.firstaimovers.com/favicon.ico"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://radar.firstaimovers.com/prompt-engineering-guide-european-sme-business-users-2026"
  },
  "image": "https://images.unsplash.com/photo-1581093588401-fbb62a02f120?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Do these prompt patterns work the same way on Claude, ChatGPT, and Gemini?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Largely yes. The five patterns described here (role plus context plus task, output format, step-by-step reasoning, few-shot examples, constraint setting) reflect how large language models process instructions, not how any one product is designed. You may see small differences in default verbosity..."
      }
    },
    {
      "@type": "Question",
      "name": "How long should a prompt be?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Long enough to eliminate ambiguity, short enough to stay focused. For most business tasks, a prompt of three to six sentences is sufficient if it includes role, context, task, and at least one format or constraint instruction. Prompts do not need to be long; they need to be precise."
      }
    },
    {
      "@type": "Question",
      "name": "What should we do if the output still misses the mark?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Treat the first response as a draft and use the conversation. Reply with a specific correction rather than starting again: "The tone is too formal for this audience. Rewrite the second paragraph to be more direct and less deferential." Iterating within a session is faster than rewriting the promp..."
      }
    }
  ]
}
</script>
-->