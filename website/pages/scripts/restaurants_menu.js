const JSON_PATH = '../../etl/extract/health_dept/health_inspections.json';

let allRestaurants = [];
const activeFilters = { followup: false, rfi: false };

async function loadData() {
  const status = document.getElementById('status');
  status.textContent = 'Loading inspections...';

  try {
    const response = await fetch(JSON_PATH);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    allRestaurants = Object.values(data)
      .map(r => {
        const matches = r.health_dept_matches || [];
        const hasFollowup = matches.some(m =>
          (m.inspections || []).some(i => i.type === 'Follow-Up')
        );
        const hasRfi = matches.some(m =>
          (m.inspections || []).some(i => (i.detail?.rfi_count ?? 0) > 0)
        );
        const allDates = matches.flatMap(m =>
          (m.inspections || []).map(i => toIsoDate(i.date)).filter(Boolean)
        );
        const lastInspectionDate = allDates.length ? allDates.sort().at(-1) : null;
        return {
          place_id: r.place_id,
          name: r.google_name,
          address: r.google_address,
          matches,
          hasFollowup,
          hasRfi,
          lastInspectionDate
        };
      })
      .sort((a, b) => a.name.localeCompare(b.name));

    status.textContent = '';
    applyFilters();
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
  const totalInspections = restaurant.matches.reduce(
    (sum, m) => sum + (m.inspections || []).length, 0
  );

  const card = document.createElement('div');
  card.className = 'restaurant-card';

  const header = document.createElement('div');
  header.className = 'restaurant-header';
  header.innerHTML = `
    <div class="restaurant-info">
      <span class="restaurant-name">${escapeHtml(restaurant.name)}</span>
      <span class="restaurant-address">${escapeHtml(restaurant.address)}</span>
    </div>
    <div class="restaurant-meta">
      <span class="inspection-count-badge">${totalInspections} inspection${totalInspections !== 1 ? 's' : ''}</span>
      <span class="chevron">&#9654;</span>
    </div>
  `;

  const body = document.createElement('div');
  body.className = 'restaurant-body collapsed';

  const multipleMatches = restaurant.matches.length > 1;
  restaurant.matches.forEach(match => {
    body.appendChild(buildMatchSection(match, multipleMatches));
  });

  header.addEventListener('click', () => {
    body.classList.toggle('collapsed');
    header.classList.toggle('open');
  });

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

function buildMatchSection(match, showTitle) {
  const section = document.createElement('div');
  section.className = 'match-section';

  if (showTitle) {
    const title = document.createElement('div');
    title.className = 'match-title';
    title.textContent = match.name;
    section.appendChild(title);
  }

  const inspections = match.inspections || [];

  if (inspections.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'no-inspections';
    empty.textContent = 'No inspections on record.';
    section.appendChild(empty);
    return section;
  }

  inspections.forEach(insp => section.appendChild(buildInspectionRow(insp)));
  return section;
}

function buildInspectionRow(inspection) {
  const rfiCount = inspection.detail?.rfi_count ?? 0;

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

  const violations = inspection.detail?.violations || [];
  if (violations.length === 0) {
    body.innerHTML = '<div class="no-violations">No violations recorded.</div>';
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
  const card = document.createElement('div');
  card.className = `violation-card${violation.is_rfi ? ' is-rfi' : ''}`;

  card.innerHTML = `
    <div class="violation-header">
      <span class="violation-code">${escapeHtml(violation.code)}</span>
      ${violation.is_rfi ? '<span class="rfi-tag">RFI</span>' : ''}
    </div>
    <div class="violation-description">${escapeHtml(violation.description)}</div>
    ${violation.observations ? `<div class="violation-section"><strong>Observations:</strong> ${escapeHtml(violation.observations)}</div>` : ''}
    ${violation.resolution ? `<div class="violation-section"><strong>Resolution:</strong> ${escapeHtml(violation.resolution)}</div>` : ''}
  `;

  return card;
}

function updateCount(count) {
  document.getElementById('result-count').textContent =
    `${count} restaurant${count !== 1 ? 's' : ''}`;
}

function toIsoDate(str) {
  if (!str) return null;
  const [m, d, y] = str.split('/');
  if (!m || !d || !y) return null;
  return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function applyFilters() {
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
  renderRestaurants(filtered);
  updateCount(filtered.length);
}

document.getElementById('search').addEventListener('input', applyFilters);
document.getElementById('date-from').addEventListener('change', applyFilters);
document.getElementById('date-to').addEventListener('change', applyFilters);

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const filter = btn.dataset.filter;
    activeFilters[filter] = !activeFilters[filter];
    btn.classList.toggle('active', activeFilters[filter]);
    applyFilters();
  });
});

loadData();
