/* Renders the "where your donation went" map on the impact dashboard.
 *
 * Data: GET /api/impact -> { product_count, states: { "TX": 3, ... } }
 * Map:  us-atlas states topology (pre-projected Albers, 975x610), drawn with
 *       d3 + topojson-client (loaded from CDN in impact.html).
 *
 * Encoding: one dot per state that received products, dot AREA scaled by
 * count (single-hue sequential — magnitude, not identity). Hover tooltip on
 * every dot; a <table> fallback is filled in for screen readers / no-JS-map.
 */
(async function () {
  const container = document.getElementById("impact-map");
  const tooltip = document.getElementById("map-tooltip");
  const tableBody = document.querySelector("#impact-table tbody");
  if (!container) return;

  if (typeof d3 === "undefined" || typeof topojson === "undefined") {
    container.innerHTML =
      '<p class="muted">The map libraries could not load (no internet access ' +
      "or the CDN is blocked). Your product data is still shown on the left.</p>";
    return;
  }

  const STATE_ABBR = {
    Alabama: "AL", Alaska: "AK", Arizona: "AZ", Arkansas: "AR", California: "CA",
    Colorado: "CO", Connecticut: "CT", Delaware: "DE", "District of Columbia": "DC",
    Florida: "FL", Georgia: "GA", Hawaii: "HI", Idaho: "ID", Illinois: "IL",
    Indiana: "IN", Iowa: "IA", Kansas: "KS", Kentucky: "KY", Louisiana: "LA",
    Maine: "ME", Maryland: "MD", Massachusetts: "MA", Michigan: "MI",
    Minnesota: "MN", Mississippi: "MS", Missouri: "MO", Montana: "MT",
    Nebraska: "NE", Nevada: "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", Ohio: "OH", Oklahoma: "OK", Oregon: "OR",
    Pennsylvania: "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", Tennessee: "TN", Texas: "TX", Utah: "UT",
    Vermont: "VT", Virginia: "VA", Washington: "WA", "West Virginia": "WV",
    Wisconsin: "WI", Wyoming: "WY",
  };

  let impact, topology;
  try {
    [impact, topology] = await Promise.all([
      fetch("/api/impact").then((r) => {
        if (!r.ok) throw new Error(`impact API returned ${r.status}`);
        return r.json();
      }),
      fetch("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json").then((r) => {
        if (!r.ok) throw new Error("map data CDN unreachable");
        return r.json();
      }),
    ]);
  } catch (err) {
    container.innerHTML =
      `<p class="muted">The map could not load (${err.message}). ` +
      `Your product data is still shown on the left.</p>`;
    return;
  }
  const stateCounts = impact.states || {};

  const width = 975;
  const height = 610;
  const projection = d3.geoAlbersUsa().scale(1300).translate([width / 2, height / 2]);
  const path = d3.geoPath(projection);
  const states = topojson.feature(topology, topology.objects.states).features;

  const svg = d3
    .select(container)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("aria-hidden", "true");

  svg
    .selectAll("path")
    .data(states)
    .join("path")
    .attr("class", "state-shape")
    .attr("d", path);

  // Dot area (not radius) scales with count, floor of 6px radius for hover.
  const maxCount = Math.max(1, ...Object.values(stateCounts));
  const radius = d3.scaleSqrt().domain([0, maxCount]).range([0, 22]);

  const dots = states
    .map((feature) => {
      const abbr = STATE_ABBR[feature.properties.name];
      const count = stateCounts[abbr];
      if (!count) return null;
      const [x, y] = path.centroid(feature);
      return { abbr, name: feature.properties.name, count, x, y };
    })
    .filter(Boolean)
    .sort((a, b) => b.count - a.count);

  svg
    .selectAll("circle")
    .data(dots)
    .join("circle")
    .attr("class", "impact-dot")
    .attr("cx", (d) => d.x)
    .attr("cy", (d) => d.y)
    .attr("r", (d) => Math.max(6, radius(d.count)))
    .on("mousemove", (event, d) => {
      tooltip.hidden = false;
      tooltip.textContent = `${d.name}: ${d.count} product${d.count === 1 ? "" : "s"}`;
      tooltip.style.left = `${event.clientX + 12}px`;
      tooltip.style.top = `${event.clientY + 12}px`;
    })
    .on("mouseleave", () => {
      tooltip.hidden = true;
    });

  // Accessible table view mirrors the map data.
  if (tableBody) {
    tableBody.innerHTML = dots
      .map((d) => `<tr><td>${d.name}</td><td>${d.count}</td></tr>`)
      .join("") || `<tr><td colspan="2">No shipments recorded yet.</td></tr>`;
  }
})();
