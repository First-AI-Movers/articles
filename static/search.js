/**
 * Client-side archive search over index.json.
 *
 * Fetches the article catalog, indexes it in memory, and filters
 * results on input.  Links to local archive article pages.
 */
(function() {
  var input = document.getElementById('archive-search');
  var resultsEl = document.getElementById('search-results');
  if (!input || !resultsEl) return;

  var depth = (window.location.pathname.match(/\//g) || []).length - 1;
  var prefix = depth > 0 ? new Array(depth + 1).join('../') : '';
  var indexUrl = prefix + 'index.json';

  var articles = [];
  var indexLoaded = false;

  function normalize(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function hostLabel(url) {
    try {
      var u = new URL(url);
      var map = {
        'radar.firstaimovers.com': 'Radar',
        'www.firstaimovers.com': 'First AI Movers',
        'firstaimovers.com': 'First AI Movers',
        'insights.firstaimovers.com': 'Insights',
        'voices.firstaimovers.com': 'Voices',
        'www.linkedin.com': 'LinkedIn',
        'linkedin.com': 'LinkedIn',
        'medium.com': 'Medium'
      };
      return map[u.hostname] || u.hostname;
    } catch (e) {
      return 'source';
    }
  }

  function search(query) {
    var q = normalize(query).trim();
    if (!q) return [];
    var terms = q.split(/\s+/);
    var out = [];
    for (var i = 0; i < articles.length; i++) {
      var a = articles[i];
      var hay = normalize([
        a.title,
        (a.topics || []).join(' '),
        (a.tags || []).join(' '),
        a.canonical_url || ''
      ].join(' '));
      var match = true;
      for (var j = 0; j < terms.length; j++) {
        if (hay.indexOf(terms[j]) === -1) { match = false; break; }
      }
      if (match) out.push(a);
      if (out.length >= 25) break;
    }
    return out;
  }

  function render(results) {
    if (!results.length) {
      resultsEl.innerHTML = '<p class="search-empty">No articles found.</p>';
      return;
    }
    var html = '';
    for (var i = 0; i < results.length; i++) {
      var a = results[i];
      var slug = a.slug || a.folder || '';
      var localPath = prefix + 'articles/' + slug + '/';
      var topics = (a.topics || []).slice(0, 3).join(', ');
      html += '<article class="search-result">' +
        '<h3><a href="' + localPath + '">' + (a.title || 'Untitled') + '</a></h3>' +
        '<p class="search-meta">' + (a.published_date || '') +
        (topics ? ' · ' + topics : '') +
        ' · ' + hostLabel(a.canonical_url || '') + '</p>' +
        '</article>';
    }
    resultsEl.innerHTML = html;
  }

  var debounce;
  input.addEventListener('input', function() {
    clearTimeout(debounce);
    debounce = setTimeout(function() {
      render(search(input.value));
    }, 150);
  });

  fetch(indexUrl)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      articles = data.articles || [];
      indexLoaded = true;
    })
    .catch(function(e) {
      console.error('[search] Failed to load index.json', e);
      resultsEl.innerHTML = '<p class="search-empty">Search unavailable.</p>';
    });
})();
