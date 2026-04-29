/**
 * Ask the Archive — client-side chat interface.
 *
 * Posts questions to /api/ask (or a configurable endpoint) and renders
 * answers with citations. Falls back gracefully when the endpoint is
 * unavailable (e.g. not yet deployed).
 */
(function() {
  var form = document.getElementById('ask-form');
  var textarea = document.getElementById('ask-question');
  var submitBtn = document.getElementById('ask-submit');
  var loadingEl = document.getElementById('ask-loading');
  var errorEl = document.getElementById('ask-error');
  var disabledEl = document.getElementById('ask-disabled');
  var answerEl = document.getElementById('ask-answer');
  var answerTextEl = document.getElementById('ask-answer-text');
  var citationsEl = document.getElementById('ask-citations');
  var citationsListEl = document.getElementById('ask-citations-list');

  var endpoint = (window.ASK_ARCHIVE_ENDPOINT || '/api/ask').trim();

  function setHidden(el, hidden) {
    if (!el) return;
    el.hidden = hidden;
    if (!hidden) el.removeAttribute('hidden');
  }

  function showError(msg) {
    if (!errorEl) return;
    errorEl.textContent = msg;
    setHidden(errorEl, false);
  }

  function clearUI() {
    setHidden(loadingEl, true);
    setHidden(errorEl, true);
    setHidden(disabledEl, true);
    setHidden(answerEl, true);
    setHidden(citationsEl, true);
    if (answerTextEl) answerTextEl.innerHTML = '';
    if (citationsListEl) citationsListEl.innerHTML = '';
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function(ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch];
    });
  }

  function renderAnswer(text) {
    if (!answerTextEl) return;
    // Simple paragraph splitting — no markdown parser needed for v1
    var paragraphs = text.split(/\n\n+/);
    var html = '';
    for (var i = 0; i < paragraphs.length; i++) {
      var p = paragraphs[i].trim();
      if (!p) continue;
      html += '<p>' + escapeHtml(p) + '</p>';
    }
    answerTextEl.innerHTML = html;
  }

  function renderCitations(citations) {
    if (!citationsListEl) return;
    if (!citations || !citations.length) {
      setHidden(citationsEl, true);
      return;
    }
    var html = '';
    for (var i = 0; i < citations.length; i++) {
      var c = citations[i];
      var local = c.local_url || '';
      var canonical = c.canonical_url || '';
      var title = c.title || 'Untitled';
      html += '<li>' +
        '<strong>' + escapeHtml(title) + '</strong>' +
        ' <span class="ask-citation-score">(score ' + (typeof c.score === 'number' ? c.score.toFixed(3) : '—') + ')</span>' +
        '<br><a href="' + escapeHtml(local) + '">Read in archive</a>';
      if (canonical && canonical !== local) {
        html += ' · <a href="' + escapeHtml(canonical) + '" rel="noopener noreferrer">Original source</a>';
      }
      html += '</li>';
    }
    citationsListEl.innerHTML = html;
    setHidden(citationsEl, false);
  }

  if (!form) return;

  form.addEventListener('submit', function(ev) {
    ev.preventDefault();
    clearUI();

    var question = (textarea.value || '').trim();
    if (question.length < 3) {
      showError('Please enter a question of at least 3 characters.');
      return;
    }

    setHidden(loadingEl, false);
    if (submitBtn) submitBtn.disabled = true;

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question, limit: 5 }),
    })
      .then(function(res) {
        setHidden(loadingEl, true);
        if (submitBtn) submitBtn.disabled = false;

        if (res.status === 404 || res.status === 501 || res.status === 503) {
          setHidden(disabledEl, false);
          return;
        }

        if (!res.ok) {
          return res.json().then(function(data) {
            throw new Error(data.error || 'Server error (' + res.status + ')');
          }).catch(function() {
            throw new Error('Server error (' + res.status + ')');
          });
        }

        return res.json();
      })
      .then(function(data) {
        if (!data) return;
        if (data.error) {
          showError(data.error);
          return;
        }
        if (data.answer) {
          renderAnswer(data.answer);
          setHidden(answerEl, false);
        }
        if (data.citations) {
          renderCitations(data.citations);
        }
      })
      .catch(function(err) {
        setHidden(loadingEl, true);
        if (submitBtn) submitBtn.disabled = false;
        showError('Failed to reach the answer endpoint. ' + err.message);
      });
  });
})();
