const JSON_PATH = 'https://storage.googleapis.com/missoula_restaurants/output/restaurants.json';

let allRestaurants = [];
const activeFilters = { followup: false, rfi: false };

const SEVERITY_LABEL = {
  Critical: { text: 'Critical', cls: 'severity-critical' },
  High:     { text: 'High',     cls: 'severity-high' },
  Medium:   { text: 'Medium',   cls: 'severity-medium' },
  Low:      { text: 'Low',      cls: 'severity-low' },
  Clean:    { text: 'Clean',    cls: 'severity-clean' },
  None:     { text: 'None',     cls: 'severity-none' },
};

function computeDisplaySeverity(r) {
  const sev = r.worst_recent_severity || 'None';
  if (sev !== 'None') return sev;
  // Distinguish a clean routine inspection from truly unclassified
  const routine = (r.inspections || []).filter(i =>
    i.type && i.type.toLowerCase().includes('routine')
  );
  if (routine.length > 0) {
    const latest = routine.reduce((a, b) => (a.date > b.date ? a : b));
    if ((latest.violations || []).length === 0) return 'Clean';
  }
  return 'None';
}

async function loadData() {
  const status = document.getElementById('status');
  status.textContent = 'Loading inspections...';

  try {
    const response = await fetch(JSON_PATH);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    allRestaurants = data
      .map(r => {
        const inspections = r.inspections || [];
        const hasFollowup = inspections.some(i => i.type === 'Follow-Up');
        const hasRfi = inspections.some(i => (i.rfi_count ?? 0) > 0);
        return {
          place_id: r.place_id,
          name: r.google_name,
          address: r.address,
          severity: computeDisplaySeverity(r),
          lastInspectionDate: r.last_inspection_date || null,
          inspections,
          hasFollowup,
          hasRfi,
        };
      });

    applySortAndFilter();

    status.textContent = '';
  } catch (err) {
    status.textContent = `Failed to load data: ${err.message}`;
    status.classList.add('error');
  }
}

function renderRestaurants(restaurants) {
  const list = document.getElementById('restaurant-list');
  list.innerHTML = '';
  if (restaurants.length === 0) {
    list.innerHTML = '<div class="no-results">No restaurants match your search.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  restaurants.forEach(r => fragment.appendChild(buildRestaurantCard(r)));
  list.appendChild(fragment);
}

function buildRestaurantCard(restaurant) {
  const totalInspections = restaurant.inspections.length;
  const sev = SEVERITY_LABEL[restaurant.severity] || SEVERITY_LABEL.None;

  const card = document.createElement('div');
  card.className = 'restaurant-card';
  card.id = restaurant.place_id;

  const header = document.createElement('div');
  header.className = 'restaurant-header';
  header.innerHTML = `
    <div class="restaurant-info">
      <span class="restaurant-name">${escapeHtml(restaurant.name)}</span>
      <span class="restaurant-address">${escapeHtml(restaurant.address)}</span>
    </div>
    <div class="restaurant-meta">
      <span class="severity-badge ${sev.cls}">${sev.text}</span>
      <span class="inspection-count-badge">${totalInspections} inspection${totalInspections !== 1 ? 's' : ''}</span>
      <span class="chevron">&#9654;</span>
    </div>
  `;

  const body = document.createElement('div');
  body.className = 'restaurant-body collapsed';

  if (restaurant.inspections.length === 0) {
    body.innerHTML = '<div class="no-inspections" style="padding:12px 0;">No inspections on record.</div>';
  } else {
    restaurant.inspections.forEach(insp => body.appendChild(buildInspectionRow(insp)));
  }

  header.addEventListener('click', () => {
    body.classList.toggle('collapsed');
    header.classList.toggle('open');
  });

  // Auto-expand if navigated via anchor
  if (window.location.hash === `#${restaurant.place_id}`) {
    body.classList.remove('collapsed');
    header.classList.add('open');
    setTimeout(() => card.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
  }

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

function buildInspectionRow(inspection) {
  const rfiCount = inspection.rfi_count ?? 0;

  const row = document.createElement('div');
  row.className = 'inspection-row';

  const header = document.createElement('div');
  header.className = 'inspection-header';
  header.innerHTML = `
    <div class="inspection-info">
      <span class="inspection-type">${escapeHtml(inspection.type)}</span>
      <span class="inspection-date">${escapeHtml(inspection.date)}</span>
      <span class="rfi-badge ${rfiCount > 0 ? 'rfi-has' : 'rfi-none'}">${rfiCount} RFI</span>
    </div>
    <span class="chevron">&#9654;</span>
  `;

  const body = document.createElement('div');
  body.className = 'inspection-body collapsed';

  if (inspection.summary) {
    const summary = document.createElement('div');
    summary.className = 'inspection-summary';
    summary.textContent = inspection.summary;
    body.appendChild(summary);
  }

  const violations = inspection.violations || [];
  if (violations.length === 0) {
    const noViol = document.createElement('div');
    noViol.className = 'no-violations';
    noViol.textContent = 'No violations recorded.';
    body.appendChild(noViol);
  } else {
    violations.forEach(v => body.appendChild(buildViolationCard(v)));
  }

  header.addEventListener('click', () => {
    body.classList.toggle('collapsed');
    header.classList.toggle('open');
  });

  row.appendChild(header);
  row.appendChild(body);
  return row;
}

function buildViolationCard(violation) {
  const cl = violation.classification;
  const sev = cl?.severity;
  const sevClass = sev ? `severity-${sev.toLowerCase()}` : '';

  const card = document.createElement('div');
  card.className = `violation-card${violation.is_rfi ? ' is-rfi' : ''}${sevClass ? ' ' + sevClass : ''}`;

  const classificationHtml = cl
    ? `<div class="violation-classification">
        <span class="severity-tag ${sevClass}">${escapeHtml(sev)}</span>
        <span class="severity-reasoning">${escapeHtml(cl.reasoning)}</span>
       </div>`
    : '';

  card.innerHTML = `
    <div class="violation-header">
      <span class="violation-code">${escapeHtml(violation.code)}</span>
      ${violation.is_rfi ? '<span class="rfi-tag">RFI</span>' : ''}
    </div>
    <div class="violation-description">${escapeHtml(violation.description)}</div>
    ${classificationHtml}
    ${violation.observations ? `<div class="violation-section"><strong>Observations:</strong> ${escapeHtml(violation.observations)}</div>` : ''}
    ${violation.resolution ? `<div class="violation-section"><strong>Resolution:</strong> ${escapeHtml(violation.resolution)}</div>` : ''}
  `;

  return card;
}

function updateCount(count) {
  document.getElementById('result-count').textContent =
    `${count} restaurant${count !== 1 ? 's' : ''}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function applySortAndFilter() {
  const query = document.getElementById('search').value.toLowerCase().trim();
  let filtered = allRestaurants;
  if (query) {
    filtered = filtered.filter(r =>
      r.name.toLowerCase().includes(query) ||
      r.address.toLowerCase().includes(query)
    );
  }
  if (activeFilters.followup) filtered = filtered.filter(r => r.hasFollowup);
  if (activeFilters.rfi) filtered = filtered.filter(r => r.hasRfi);
  const dateFrom = document.getElementById('date-from').value;
  const dateTo = document.getElementById('date-to').value;
  if (dateFrom) filtered = filtered.filter(r => r.lastInspectionDate && r.lastInspectionDate >= dateFrom);
  if (dateTo) filtered = filtered.filter(r => r.lastInspectionDate && r.lastInspectionDate <= dateTo);

  const sort = document.getElementById('sort-select').value;
  if (sort === 'name-asc')  filtered = [...filtered].sort((a, b) => a.name.localeCompare(b.name));
  if (sort === 'name-desc') filtered = [...filtered].sort((a, b) => b.name.localeCompare(a.name));
  if (sort === 'date-desc') filtered = [...filtered].sort((a, b) => (b.lastInspectionDate || '').localeCompare(a.lastInspectionDate || ''));
  if (sort === 'date-asc')  filtered = [...filtered].sort((a, b) => (a.lastInspectionDate || '').localeCompare(b.lastInspectionDate || ''));

  renderRestaurants(filtered);
  updateCount(filtered.length);
}

document.getElementById('search').addEventListener('input', applySortAndFilter);
document.getElementById('date-from').addEventListener('change', applySortAndFilter);
document.getElementById('date-to').addEventListener('change', applySortAndFilter);
document.getElementById('sort-select').addEventListener('change', applySortAndFilter);

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const filter = btn.dataset.filter;
    activeFilters[filter] = !activeFilters[filter];
    btn.classList.toggle('active', activeFilters[filter]);
    applySortAndFilter();
  });
});

loadData();
