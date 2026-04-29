/**
 * Client-side archive search over index.json.
 */
(function() {
  var input = document.getElementById('archive-search');
  var resultsEl = document.getElementById('search-results');
  if (!input || !resultsEl) return;

  var articles = [];
  fetch('index.json')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      articles = data.articles || [];
    })
    .catch(function(e) {
      console.error('[search] Failed to load index.json', e);
    });

  function search(query) {
    var q = query.toLowerCase().trim();
    if (!q) return [];
    var terms = q.split(/\s+/);
    var out = [];
    for (var i = 0; i < articles.length; i++) {
      var a = articles[i];
      var hay = [a.title, (a.topics || []).join(' ')].join(' ').toLowerCase();
      var match = true;
      for (var j = 0; j < terms.length; j++) {
        if (hay.indexOf(terms[j]) === -1) { match = false; break; }
      }
      if (match) out.push(a);
      if (out.length >= 25) break;
    }
    return out;
  }

  input.addEventListener('input', function() {
    var results = search(input.value);
    if (!results.length) {
      resultsEl.innerHTML = '<p class="search-empty">No articles found.</p>';
      return;
    }
    var html = '';
    for (var i = 0; i < results.length; i++) {
      var a = results[i];
      html += '<article class="search-result"><h3><a href="articles/' + a.slug + '/">' + a.title + '</a></h3></article>';
    }
    resultsEl.innerHTML = html;
  });
})();
