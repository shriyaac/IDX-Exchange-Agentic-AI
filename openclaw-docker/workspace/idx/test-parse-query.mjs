// Week 2: runs the parser on test queries and checks each answer.
// Run:  node test-parse-query.mjs
import { parsePropertyQuery } from "./parse-query.mjs";

// Each test: a question, and the filters we expect back.
// Any filter not listed is expected to be null.
const tests = [
  { q: "Show me 3-bedroom condos in Irvine under $1.5M with a pool.",
    want: { city: "Irvine", maxPrice: 1500000, beds: 3, type: "Condominium", pool: "1" } },
  { q: "Find homes in Pasadena under $900k",
    want: { city: "Pasadena", maxPrice: 900000 } },
  { q: "2 bedroom townhome in San Diego under $750,000",
    want: { city: "San Diego", maxPrice: 750000, beds: 2, type: "Townhouse" } },
  { q: "single family homes in Newport Beach with a view",
    want: { city: "Newport Beach", type: "SingleFamilyResidence", hasView: "1" } },
  { q: "4 beds 2.5 baths in Riverside under $800k",
    want: { city: "Riverside", maxPrice: 800000, beds: 4, baths: 2.5 } },
  { q: "condo with ocean view in Long Beach under 1.2m",
    want: { city: "Long Beach", maxPrice: 1200000, type: "Condominium", hasView: "1" } },
  { q: "5 bedroom house in Temecula with pool",
    want: { city: "Temecula", beds: 5, pool: "1" } },
  { q: "3 bed 2 bath at least 1800 sqft in Corona",
    want: { city: "Corona", beds: 3, baths: 2, sqft: 1800 } },
  { q: "townhome in Anaheim under $650k with a pool",
    want: { city: "Anaheim", maxPrice: 650000, type: "Townhouse", pool: "1" } },
  { q: "2000 square feet single family in Fontana",
    want: { city: "Fontana", sqft: 2000, type: "SingleFamilyResidence" } },
  { q: "1 bedroom condo in Los Angeles under $500k",
    want: { city: "Los Angeles", maxPrice: 500000, beds: 1, type: "Condominium" } },
  { q: "homes in Malibu with a view under $5M",
    want: { city: "Malibu", maxPrice: 5000000, hasView: "1" } },
];

const fields = ["city", "maxPrice", "beds", "baths", "sqft", "type", "pool", "hasView"];
let passed = 0;
for (const [i, t] of tests.entries()) {
  const got = await parsePropertyQuery(t.q);
  const wrong = fields.filter(f => (t.want[f] ?? null) !== got[f]);
  if (wrong.length === 0) { passed++; console.log(`PASS  ${i + 1}. ${t.q}`); }
  else {
    console.log(`FAIL  ${i + 1}. ${t.q}`);
    for (const f of wrong) console.log(`        ${f}: expected ${JSON.stringify(t.want[f] ?? null)}, got ${JSON.stringify(got[f])}`);
  }
}
console.log(`\n${passed} of ${tests.length} tests passed`);
