(function () {
  'use strict';

  var D = JSON.parse(document.getElementById('site-data').textContent);
  var NS = 'http://www.w3.org/2000/svg';

  /* ---------- форматирование ---------- */
  var fmt0 = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });
  var fmtN = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 });
  var fmt1 = new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  function rub(x) { return fmt0.format(Math.round(x)).replace(/ | /g, ' ') + ' ₽'; }
  function pct(x) { return fmtN.format(x) + '%'; }

  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) { if (Object.prototype.hasOwnProperty.call(attrs, k)) n.setAttribute(k, attrs[k]); }
    if (parent) parent.appendChild(n);
    return n;
  }

  /* ---------- общий каркас графика ---------- */
  function frame(host, cfg) {
    host.textContent = '';
    var W = Math.max(280, Math.floor(host.clientWidth || 640));
    var H = W < 520 ? 250 : 300;
    var m = { l: 40, r: cfg.rightPad || 16, t: 14, b: 28 };
    var pw = W - m.l - m.r, ph = H - m.t - m.b;
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'img', 'aria-label': cfg.aria, tabindex: 0 }, host);
    var Y = function (v) { return m.t + ph * (1 - (v - cfg.min) / (cfg.max - cfg.min)); };
    for (var v = cfg.min; v <= cfg.max + 1e-9; v += cfg.step) {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), 'class': 'grid' }, svg);
      var t = el('text', { x: m.l - 8, y: Y(v) + 4, 'text-anchor': 'end', 'class': 'tick' }, svg);
      t.textContent = fmt0.format(v);
    }
    return { svg: svg, W: W, H: H, m: m, pw: pw, ph: ph, Y: Y };
  }

  function xLabels(f, labels, X) {
    var skip = f.W < 480 ? 2 : 1;
    labels.forEach(function (l, i) {
      if (i % skip !== 0 && i !== labels.length - 1) return;
      var t = el('text', { x: X(i), y: f.H - 8, 'text-anchor': 'middle', 'class': 'tick' }, f.svg);
      t.textContent = l;
    });
  }

  function bindPick(f, n, X, get, set) {
    var rect = el('rect', { x: f.m.l - 10, y: f.m.t, width: f.pw + 20, height: f.ph + 20, fill: 'transparent' }, f.svg);
    function fromEvent(e) {
      var r = f.svg.getBoundingClientRect();
      var x = (e.clientX - r.left) * (f.W / r.width);
      var best = 0, bd = 1e9;
      for (var i = 0; i < n; i++) { var d = Math.abs(X(i) - x); if (d < bd) { bd = d; best = i; } }
      set(best);
    }
    rect.addEventListener('pointermove', fromEvent);
    rect.addEventListener('pointerdown', fromEvent);
    f.svg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { set(Math.max(0, get() - 1)); e.preventDefault(); }
      if (e.key === 'ArrowRight') { set(Math.min(n - 1, get() + 1)); e.preventDefault(); }
      if (e.key === 'Home') { set(0); e.preventDefault(); }
      if (e.key === 'End') { set(n - 1); e.preventDefault(); }
    });
  }

  /* ---------- график 1: ставка и инфляция ---------- */
  var rateIdx = D.rate.labels.length - 1;
  var rateReadout = document.getElementById('readout-rate');

  function drawRate() {
    var host = document.getElementById('chart-rate');
    var n = D.rate.labels.length;
    var f = frame(host, { min: 0, max: 18, step: 3, rightPad: 48, aria: 'График: ключевая ставка и инфляция по месяцам, декабрь 2025 – сентябрь 2026' });
    var X = function (i) { return f.m.l + f.pw * i / (n - 1); };
    xLabels(f, D.rate.labels, X);

    function path(vals) { return vals.map(function (v, i) { return (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + f.Y(v).toFixed(1); }).join(' '); }
    // ставка рисуется ступенькой: она меняется только на заседаниях
    var step = D.rate.key.map(function (v, i) {
      return i === 0 ? 'M' + X(0).toFixed(1) + ' ' + f.Y(v).toFixed(1)
        : 'L' + X(i).toFixed(1) + ' ' + f.Y(D.rate.key[i - 1]).toFixed(1) + ' L' + X(i).toFixed(1) + ' ' + f.Y(v).toFixed(1);
    }).join(' ');
    el('path', { d: step, 'class': 's1' }, f.svg);
    el('path', { d: path(D.rate.infl), 'class': 's2' }, f.svg);

    var last = n - 1;
    var l1 = el('text', { x: X(last) + 8, y: f.Y(D.rate.key[last]) + 4, 'class': 'endl1' }, f.svg);
    l1.textContent = fmtN.format(D.rate.key[last]);
    var l2 = el('text', { x: X(last) + 8, y: f.Y(D.rate.infl[last]) + 4, 'class': 'endl2' }, f.svg);
    l2.textContent = fmtN.format(D.rate.infl[last]);

    var cur = el('line', { y1: f.m.t, y2: f.m.t + f.ph, 'class': 'cursor' }, f.svg);
    var d1 = el('circle', { r: 5, 'class': 'dot1' }, f.svg);
    var d2 = el('circle', { r: 5, 'class': 'dot2' }, f.svg);

    function show(i) {
      rateIdx = i;
      cur.setAttribute('x1', X(i)); cur.setAttribute('x2', X(i));
      d1.setAttribute('cx', X(i)); d1.setAttribute('cy', f.Y(D.rate.key[i]));
      d2.setAttribute('cx', X(i)); d2.setAttribute('cy', f.Y(D.rate.infl[i]));
      var gap = D.rate.key[i] - D.rate.infl[i];
      rateReadout.innerHTML =
        '<span class="rd">' + D.rate.full[i] + '</span>' +
        '<span class="r1">Ставка <b>' + pct(D.rate.key[i]) + '</b></span>' +
        '<span class="r2">Инфляция <b>' + pct(D.rate.infl[i]) + '</b></span>' +
        '<span class="rd">Разрыв ' + fmtN.format(gap) + ' п. п.</span>';
    }
    bindPick(f, n, X, function () { return rateIdx; }, show);
    show(rateIdx);
  }

  /* ---------- график 2: зарплаты ---------- */
  var wageIdx = D.wage.values.length - 1;
  var wageReadout = document.getElementById('readout-wage');

  function drawWage() {
    var host = document.getElementById('chart-wage');
    var vals = D.wage.values, n = vals.length;
    var f = frame(host, { min: 0, max: 150, step: 50, rightPad: 16, aria: 'График: средняя начисленная зарплата по месяцам, октябрь 2025 – июль 2026' });
    var slot = f.pw / n, bw = Math.min(46, slot * 0.62);
    var X = function (i) { return f.m.l + slot * (i + 0.5); };
    xLabels(f, D.wage.labels, X);
    var bars = [];
    vals.forEach(function (v, i) {
      if (v === null) {
        el('rect', { x: X(i) - bw / 2, y: f.Y(30), width: bw, height: f.Y(0) - f.Y(30), rx: 2, 'class': 'bar-gap' }, f.svg);
        bars.push(null);
      } else {
        bars.push(el('rect', { x: X(i) - bw / 2, y: f.Y(v), width: bw, height: f.Y(0) - f.Y(v), rx: 2, 'class': 'bar-rect' }, f.svg));
      }
    });
    function show(i) {
      wageIdx = i;
      bars.forEach(function (b, j) { if (b) b.setAttribute('class', 'bar-rect' + (j === i ? ' on' : '')); });
      var v = vals[i];
      wageReadout.innerHTML = '<span class="rd">' + D.wage.full[i] + '</span>' +
        (v === null ? '<span class="rd">значение не найдено в источниках</span>'
          : '<span class="r1">Зарплата <b>' + rub(v * 1000) + '</b></span>');
    }
    bindPick(f, n, X, function () { return wageIdx; }, show);
    show(wageIdx);
  }

  /* ---------- вкладки графиков ---------- */
  var tabRate = document.getElementById('tab-rate');
  var tabWage = document.getElementById('tab-wage');
  var panelRate = document.getElementById('panel-rate');
  var panelWage = document.getElementById('panel-wage');

  function selectTab(which) {
    var isRate = which === 'rate';
    tabRate.setAttribute('aria-selected', isRate); tabWage.setAttribute('aria-selected', !isRate);
    tabRate.tabIndex = isRate ? 0 : -1; tabWage.tabIndex = isRate ? -1 : 0;
    panelRate.hidden = !isRate; panelWage.hidden = isRate;
    redraw();
  }
  tabRate.addEventListener('click', function () { selectTab('rate'); });
  tabWage.addEventListener('click', function () { selectTab('wage'); });
  [tabRate, tabWage].forEach(function (t) {
    t.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        var toWage = t === tabRate;
        selectTab(toWage ? 'wage' : 'rate');
        (toWage ? tabWage : tabRate).focus();
        e.preventDefault();
      }
    });
  });

  function redraw() {
    if (!panelRate.hidden) drawRate();
    if (!panelWage.hidden) drawWage();
  }
  redraw();
  var lastW = window.innerWidth;
  window.addEventListener('resize', function () {
    if (window.innerWidth !== lastW) { lastW = window.innerWidth; redraw(); }
  });

  /* ---------- калькулятор вклада ---------- */
  var dAmount = document.getElementById('dep-amount');
  var dMonths = document.getElementById('dep-months');
  var dMonthsOut = document.getElementById('dep-months-out');
  var dRate = document.getElementById('dep-rate');
  var dRateHint = document.getElementById('dep-rate-hint');
  var dCap = document.getElementById('dep-cap');
  var rateEdited = false;

  function num(input, fallback) {
    var v = parseFloat(String(input.value).replace(',', '.'));
    return isFinite(v) && v >= 0 ? v : fallback;
  }
  function monthsText(m) {
    if (m % 12 === 0) { var y = m / 12; return y + (y === 1 ? ' год' : y < 5 ? ' года' : ' лет'); }
    return m + ' мес.';
  }
  function bucketFor(m) {
    for (var i = 0; i < D.depositRates.length; i++) { if (m <= D.depositRates[i].upto_months) return D.depositRates[i]; }
    return D.depositRates[D.depositRates.length - 1];
  }

  function calcDeposit() {
    var P = num(dAmount, 0), m = parseInt(dMonths.value, 10), r = num(dRate, 0);
    dMonthsOut.textContent = monthsText(m);
    var b = bucketFor(m);
    if (!rateEdited) { dRate.value = b.rate; r = b.rate; }
    dRateHint.textContent = rateEdited ? '' : 'средняя максимальная для срока: ' + b.label;
    var final = dCap.checked ? P * Math.pow(1 + r / 100 / 12, m) : P * (1 + r / 100 * m / 12);
    var income = final - P;
    var real = final / Math.pow(1 + D.inflation / 100, m / 12) - P;
    document.getElementById('dep-income').textContent = rub(income);
    document.getElementById('dep-final').textContent = rub(final);
    document.getElementById('dep-real').textContent = (real < 0 ? '−' : '') + rub(Math.abs(real));
    document.getElementById('dep-warn').textContent =
      r > D.keyRate ? 'Ставка выше ключевой (' + pct(D.keyRate) + '). Такие предложения обычно действуют на ограниченный срок или при условиях.' : '';
  }
  dRate.addEventListener('input', function () { rateEdited = true; calcDeposit(); });
  [dAmount, dMonths, dCap].forEach(function (i) { i.addEventListener('input', calcDeposit); });
  dMonths.addEventListener('input', function () { /* ставка подстраивается под срок, пока её не меняли вручную */ });
  calcDeposit();

  /* ---------- калькулятор ипотеки ---------- */
  var mPrice = document.getElementById('mor-price');
  var mDown = document.getElementById('mor-down');
  var mDownOut = document.getElementById('mor-down-out');
  var mYears = document.getElementById('mor-years');
  var mYearsOut = document.getElementById('mor-years-out');
  var mPreset = document.getElementById('mor-preset');
  var mRate = document.getElementById('mor-rate');

  function yearsText(y) { return y + (y === 1 ? ' год' : (y >= 2 && y <= 4) ? ' года' : ' лет'); }

  function calcMortgage() {
    var price = num(mPrice, 0), down = parseInt(mDown.value, 10), years = parseInt(mYears.value, 10), rate = num(mRate, 0);
    mDownOut.textContent = down + '% (' + rub(price * down / 100) + ')';
    mYearsOut.textContent = yearsText(years);
    var loan = price * (1 - down / 100), n = years * 12, i = rate / 100 / 12;
    var pay = loan === 0 ? 0 : (i === 0 ? loan / n : loan * i / (1 - Math.pow(1 + i, -n)));
    var over = pay * n - loan;
    document.getElementById('mor-pay').textContent = rub(pay);
    document.getElementById('mor-loan').textContent = rub(loan);
    document.getElementById('mor-over').textContent = rub(over);
    document.getElementById('mor-share').textContent = fmt1.format(pay / D.avgWage * 100) + '%';
  }
  mPreset.addEventListener('change', function () {
    if (mPreset.value !== 'custom') { mRate.value = mPreset.value; }
    calcMortgage();
  });
  mRate.addEventListener('input', function () {
    var match = false;
    Array.prototype.forEach.call(mPreset.options, function (o) { if (o.value !== 'custom' && parseFloat(o.value) === parseFloat(mRate.value)) { mPreset.value = o.value; match = true; } });
    if (!match) mPreset.value = 'custom';
    calcMortgage();
  });
  [mPrice, mDown, mYears].forEach(function (i) { i.addEventListener('input', calcMortgage); });
  calcMortgage();

  /* ---------- сортировка таблицы регионов ---------- */
  var table = document.getElementById('regions-table');
  var tbody = table.tBodies[0];
  var sortState = { key: null, dir: 'desc' };
  Array.prototype.forEach.call(table.querySelectorAll('button.sort'), function (btn) {
    btn.addEventListener('click', function () {
      var key = btn.getAttribute('data-key');
      sortState.dir = sortState.key === key && sortState.dir === 'desc' ? 'asc' : 'desc';
      sortState.key = key;
      Array.prototype.forEach.call(table.querySelectorAll('button.sort'), function (b) { b.removeAttribute('data-dir'); });
      btn.setAttribute('data-dir', sortState.dir);
      var rows = Array.prototype.filter.call(tbody.rows, function (r) { return !r.classList.contains('pinned'); });
      rows.sort(function (a, b) {
        var va = parseFloat(a.getAttribute('data-' + key)), vb = parseFloat(b.getAttribute('data-' + key));
        var na = isNaN(va), nb = isNaN(vb);
        if (na && nb) return 0;
        if (na) return 1;
        if (nb) return -1;
        return sortState.dir === 'desc' ? vb - va : va - vb;
      });
      rows.forEach(function (r) { tbody.appendChild(r); });
    });
  });
})();
