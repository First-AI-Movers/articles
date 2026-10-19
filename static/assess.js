/*
 * Seven-question workflow automation assessment (Issue #508 §5).
 *
 * Runs entirely in the browser. It makes NO network request, calls no model,
 * and persists nothing: no fetch/XMLHttpRequest/sendBeacon, no localStorage,
 * sessionStorage, IndexedDB or cookie. The downloaded record is built from a
 * Blob in memory. `tools/tests/test_assess_page.py` asserts that absence, so a
 * future edit that adds a call fails the suite rather than quietly changing
 * what the page promises its visitors.
 *
 * Every rule below is traceable to a passage in the published article,
 * articles/2026-09-27-before-you-automate-a-workflow-7-questions/article.md.
 * The rule table is the article's own text, not a scoring model invented here:
 * there are no weights and no arithmetic, because the article defines verdicts
 * by conditions, not by a score.
 */
(function () {
  'use strict';

  var QUESTIONS = [
    { id: 'q1', evidence: 'e1', text: 'What decision or outcome does the workflow exist to produce?' },
    { id: 'q2', evidence: 'e2', text: 'Where is time or failure actually concentrated?' },
    { id: 'q3', evidence: 'e3', text: 'What is the strongest non-AI alternative?' },
    { id: 'q4', evidence: 'e4', text: 'Which systems and data must be touched?' },
    { id: 'q5', evidence: 'e5', text: 'What can fail, and who notices?' },
    { id: 'q6', evidence: 'e6', text: 'What does "good enough" mean before production?' }
  ];

  var ANSWER_LABELS = {
    q1: {
      useful: 'Decision-useful and consistent output, with a named consumer',
      inconsistent: 'Specific output, but inconsistent or not trusted',
      not_useful: 'No clear decision-useful output'
    },
    q2: {
      measured: 'Baseline measured from real data; value justifies the work',
      measured_low: 'Baseline measured; value does not clearly beat current cost',
      unmeasured: 'Not measurable today'
    },
    q3: {
      none_dominates: 'Non-AI alternatives considered; none dominates',
      comparable: 'A non-AI option is roughly comparable',
      dominates: 'A non-AI option removes the need'
    },
    q4: {
      clean: 'Every input has a supported interface and a lawful basis',
      changing: 'Clean, but a dependency is changing',
      broken: 'An input has no supported interface, no lawful basis, or exists only in someone’s head'
    },
    q5: {
      owned: 'Failure modes named, with owners, rollback and audit trail',
      partial: 'Named, but rollback or audit trail incomplete',
      unacceptable: 'Failure modes cannot be made acceptable'
    },
    q6: {
      reference: 'Reference set and threshold exist or can be assembled now',
      threshold_only: 'Threshold agreed, but no reference set yet',
      none: 'Neither a reference set nor a threshold'
    }
  };

  /*
   * Verdict rules, in the article's own precedence order.
   *
   * STOP first: it is the only verdict that says the workflow should not be
   * automated at all, so it dominates readiness and value questions.
   * REPAIR_FIRST next: the article calls it "the most common honest verdict",
   * and a named dependency to fix is more actionable than "not worth it yet".
   * DEFER next, BUILD only when every one of the article's six conditions holds.
   */
  var STOP_RULES = [
    { when: { q1: 'not_useful' },
      because: 'The output is not decision-useful. The article: "A workflow whose output is not decision-useful … is a candidate for removal, not for automation."' },
    { when: { q3: 'dominates' },
      because: 'A non-AI alternative removes the need, which the article lists as a STOP condition.' },
    { when: { q5: 'unacceptable' },
      because: 'The failure modes cannot be made acceptable, which the article lists as a STOP condition.' }
  ];

  var REPAIR_RULES = [
    { when: { q2: 'unmeasured' },
      because: 'The workflow cannot be measured. The article: "a process nobody can observe is not one you can safely hand to software."' },
    { when: { q4: 'broken' },
      because: 'The integration boundary is broken — an unsupported interface, no lawful basis, or a fact that exists only in someone’s head.' },
    { when: { q6: 'none' },
      because: 'No reference set and no threshold. The article: "If you cannot assemble a reference from your own history, you have learned that the workflow is not yet observable enough."' },
    { when: { q6: 'threshold_only' },
      because: 'A threshold without a reference set cannot be tested before production.' },
    { when: { q1: 'inconsistent' },
      because: 'The output is inconsistent, which the article names as a REPAIR_FIRST condition.' },
    { when: { q5: 'partial' },
      because: 'Rollback or the audit trail is incomplete, so a failure could land before anyone notices.' }
  ];

  var DEFER_RULES = [
    { when: { q2: 'measured_low' },
      because: 'The measured value does not clearly beat the current cost, which the article names as a DEFER condition.' },
    { when: { q3: 'comparable' },
      because: 'A non-AI option is roughly comparable, so an AI build has not yet earned its place.' },
    { when: { q4: 'changing' },
      because: 'A dependency is changing, which the article names as a DEFER condition.' }
  ];

  var VERDICTS = {
    BUILD: {
      gloss: 'The outcome is decision-useful, the baseline is measured, no non-AI alternative dominates, the integration boundary is clean, failure modes have owners and rollbacks, and a reference with a threshold exists.',
      next: 'Proceed to the smallest implementation that can be tested against that reference.'
    },
    REPAIR_FIRST: {
      gloss: 'The workflow is worth automating but is not ready. The article calls this the most common honest verdict.',
      next: 'Fix the named dependency first, then run these seven questions again.'
    },
    DEFER: {
      gloss: 'Automation is plausible, but the expected value does not beat the current cost, or a dependency is changing.',
      next: 'Set the condition that reopens the decision and a date to re-check it.'
    },
    STOP: {
      gloss: 'The workflow should not be automated.',
      next: 'Retire the idea explicitly, so it does not come back as someone else’s project.'
    },
    INSUFFICIENT_EVIDENCE: {
      gloss: 'Not every question is answered yet, so no verdict is honest.',
      next: 'Answer the remaining questions. An unanswered question is itself a finding — it usually means the fact is not known.'
    }
  };

  function matches(rule, answers) {
    for (var key in rule.when) {
      if (answers[key] !== rule.when[key]) { return false; }
    }
    return true;
  }

  function collectReasons(rules, answers) {
    var out = [];
    for (var i = 0; i < rules.length; i++) {
      if (matches(rules[i], answers)) { out.push(rules[i].because); }
    }
    return out;
  }

  /* Pure: answers -> { verdict, reasons, unanswered }. Exported for tests. */
  function assess(answers) {
    var unanswered = [];
    for (var i = 0; i < QUESTIONS.length; i++) {
      if (!answers[QUESTIONS[i].id]) { unanswered.push(i + 1); }
    }
    if (unanswered.length) {
      return {
        verdict: 'INSUFFICIENT_EVIDENCE',
        unanswered: unanswered,
        reasons: ['Unanswered: question ' + unanswered.join(', question ') + '.']
      };
    }
    var stop = collectReasons(STOP_RULES, answers);
    if (stop.length) { return { verdict: 'STOP', reasons: stop, unanswered: [] }; }
    var repair = collectReasons(REPAIR_RULES, answers);
    if (repair.length) { return { verdict: 'REPAIR_FIRST', reasons: repair, unanswered: [] }; }
    var defer = collectReasons(DEFER_RULES, answers);
    if (defer.length) { return { verdict: 'DEFER', reasons: defer, unanswered: [] }; }
    return {
      verdict: 'BUILD',
      unanswered: [],
      reasons: ['Every condition the article sets for BUILD is met: decision-useful output, measured baseline, no dominating non-AI alternative, clean integration boundary, owned failure modes with rollback, and a reference with a threshold.']
    };
  }

  if (typeof module !== 'undefined' && module.exports) { module.exports = { assess: assess }; }
  if (typeof window !== 'undefined') { window.ASSESS = { assess: assess }; }

  if (typeof document === 'undefined') { return; }

  function readAnswers(form) {
    var answers = {}, evidence = {};
    for (var i = 0; i < QUESTIONS.length; i++) {
      var q = QUESTIONS[i];
      var picked = form.querySelector('input[name="' + q.id + '"]:checked');
      if (picked) { answers[q.id] = picked.value; }
      var box = form.querySelector('#' + q.evidence);
      if (box && box.value.trim()) { evidence[q.id] = box.value.trim(); }
    }
    return { answers: answers, evidence: evidence };
  }

  function buildRecord(state, result) {
    var stamp = new Date().toISOString().slice(0, 10);
    var lines = [
      '# Workflow automation assessment — one-page record',
      '',
      'Date: ' + stamp,
      'Method: "Before You Automate a Workflow: 7 Questions That Decide BUILD, REPAIR_FIRST, DEFER, or STOP"',
      'Source: https://articles.firstaimovers.com/articles/before-you-automate-a-workflow-7-questions/',
      '',
      '## Provisional recommendation: ' + result.verdict,
      '',
      VERDICTS[result.verdict].gloss,
      '',
      'This recommendation is provisional and was produced in the browser from the',
      'options selected below. It is not advice, an audit, or a certification, and it',
      'contains no estimate of savings, cost or time.',
      '',
      '## Why',
      ''
    ];
    for (var r = 0; r < result.reasons.length; r++) { lines.push('- ' + result.reasons[r]); }
    lines.push('', '## Next step', '', VERDICTS[result.verdict].next, '', '## The seven answers', '');
    for (var i = 0; i < QUESTIONS.length; i++) {
      var q = QUESTIONS[i];
      var picked = state.answers[q.id];
      lines.push((i + 1) + '. ' + q.text);
      lines.push('   Answer: ' + (picked ? ANSWER_LABELS[q.id][picked] : '(unanswered)'));
      if (state.evidence[q.id]) { lines.push('   Evidence: ' + state.evidence[q.id]); }
      lines.push('');
    }
    lines.push('7. What is the decision today?');
    lines.push('   Verdict of record: ____________________  (BUILD / REPAIR_FIRST / DEFER / STOP)');
    lines.push('   Decided by: ____________________   Date: ____________');
    lines.push('');
    return lines.join('\n');
  }

  function render(result) {
    var box = document.getElementById('assess-result');
    document.getElementById('assess-verdict').textContent = result.verdict;
    document.getElementById('assess-verdict').setAttribute('data-verdict', result.verdict);
    document.getElementById('assess-verdict-gloss').textContent = VERDICTS[result.verdict].gloss;
    var ul = document.getElementById('assess-reasons');
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    for (var i = 0; i < result.reasons.length; i++) {
      var li = document.createElement('li');
      li.textContent = result.reasons[i];
      ul.appendChild(li);
    }
    document.getElementById('assess-next').textContent = VERDICTS[result.verdict].next;
    box.hidden = false;
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('assess-form');
    if (!form) { return; }
    var last = null;

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var state = readAnswers(form);
      var result = assess(state.answers);
      last = { state: state, result: result };
      render(result);
    });

    var reset = document.getElementById('assess-reset');
    if (reset) {
      reset.addEventListener('click', function () {
        form.reset();
        last = null;
        document.getElementById('assess-result').hidden = true;
      });
    }

    var download = document.getElementById('assess-download');
    if (download) {
      download.addEventListener('click', function () {
        if (!last) { return; }
        var text = buildRecord(last.state, last.result);
        var blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'workflow-assessment-' + new Date().toISOString().slice(0, 10) + '.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      });
    }

    var print = document.getElementById('assess-print');
    if (print) { print.addEventListener('click', function () { window.print(); }); }
  });
})();
