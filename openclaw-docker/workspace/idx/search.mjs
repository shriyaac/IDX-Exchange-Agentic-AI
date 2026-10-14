// Week 3: command-line entry point used by the OpenClaw skill.
//   node search.mjs listings '<question>' [page]   -> parse question (Week 2), search rets_property
//   node search.mjs comps '<City>' [months]         -> recent sales from california_sold
import { parsePropertyQuery } from "./parse-query.mjs";
import { searchActiveListings, getSoldComps, formatListingCard, formatSoldCard } from "./queries.mjs";
import { closePool } from "./db.mjs";

const [mode, text = "", extra] = process.argv.slice(2);

try {
  if (mode === "listings") {
    const filters = await parsePropertyQuery(text);
    const page = parseInt(extra) || 1;
    const rows = await searchActiveListings(filters, page, 10);
    console.log("Filters: " + JSON.stringify(filters));
    console.log(`Page ${page}: ${rows.length} listing(s), cheapest first\n`);
    rows.forEach((r, i) => console.log(`${(page - 1) * 10 + i + 1}. ${formatListingCard(r)}\n`));
    if (rows.length === 10) console.log(`More results: run again with page ${page + 1}`);
    if (rows.length === 0) console.log("No active listings match these filters.");
  } else if (mode === "comps") {
    const months = parseInt(extra) || 12;
    const rows = await getSoldComps(text, months);
    console.log(`Sold homes in ${text}, last ${months} months: ${rows.length} shown (max 50, newest first)\n`);
    rows.slice(0, 10).forEach((r, i) => console.log(`${i + 1}. ${formatSoldCard(r)}\n`));
    if (rows.length > 10) console.log(`(${rows.length - 10} more not shown)`);
    if (rows.length === 0) console.log("No sales found. Check the city spelling (e.g. 'Irvine').");
  } else {
    console.log("Usage: node search.mjs listings '<question>' [page]  |  node search.mjs comps '<City>' [months]");
  }
} catch (err) {
  console.error("Search failed: " + err.message);
  process.exitCode = 1;
} finally {
  await closePool();
}
