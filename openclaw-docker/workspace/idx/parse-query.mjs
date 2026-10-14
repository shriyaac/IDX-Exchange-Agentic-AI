// Week 2: natural-language property query parser.
// Based on the handbook's parsePropertyQuery, converted from TypeScript to JavaScript.
// Changes from the handbook (because of the real data):
//   - pool and view return "1" instead of "True" (that's how rets_property stores them)
//   - "land" removed from the type map (there are no land listings)
export async function parsePropertyQuery(query) {
  const cityMatch  = query.match(/in ([A-Za-z\s]+?)(?:\s+under|\s+with|\s+at|$)/i);
  const priceMatch = query.match(/under \$?([\d,.]+)(k|m)?/i);
  const bedsMatch  = query.match(/(\d+)[\s-]*(bed|beds|bedroom|bedrooms)/i);
  const bathsMatch = query.match(/(\d+(?:\.5)?)[\s-]*(bath|baths|bathroom)/i);
  const sqftMatch  = query.match(/(\d+)[\s,]*(sqft|sq ft|square feet)/i);
  const poolMatch  = /pool/i.test(query);
  const viewMatch  = /view/i.test(query);

  const typeMap = {
    condo: "Condominium", townhome: "Townhouse",
    "single family": "SingleFamilyResidence"
  };
  const typeKey = Object.keys(typeMap).find(k => query.toLowerCase().includes(k));

  let maxPrice = null;
  if (priceMatch) {
    maxPrice = Number(priceMatch[1].replace(/,/g, ""));
    if (priceMatch[2]?.toLowerCase() === "k") maxPrice *= 1000;
    if (priceMatch[2]?.toLowerCase() === "m") maxPrice *= 1_000_000;
  }

  return {
    city:     cityMatch?.[1]?.trim() || null,
    maxPrice,
    beds:     bedsMatch ? Number(bedsMatch[1]) : null,
    baths:    bathsMatch ? Number(bathsMatch[1]) : null,
    sqft:     sqftMatch ? Number(sqftMatch[1]) : null,
    type:     typeKey ? typeMap[typeKey] : null,
    pool:     poolMatch ? "1" : null,
    hasView:  viewMatch ? "1" : null,
  };
}

// Lets you run it from Terminal:  node parse-query.mjs 'your question here'
if (import.meta.url === `file://${process.argv[1]}`) {
  parsePropertyQuery(process.argv.slice(2).join(" "))
    .then(result => console.log(JSON.stringify(result, null, 2)));
}
