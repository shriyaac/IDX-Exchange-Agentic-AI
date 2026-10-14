// Week 3: searches on rets_property (active listings) and california_sold (sold comps).
// Based on the handbook's searchActiveListings and getSoldComps, converted to JavaScript.
// Changes from the handbook:
//   - LIMIT/OFFSET are checked whole numbers placed in the SQL (some drivers reject them as ? params)
//   - limit capped at 50 rows (handbook safety rule)
//   - sold comps skip 4 typo rows dated in the future (2028-2072)
import { query } from "./db.mjs";

export async function searchActiveListings(filters, page = 1, limit = 10) {
  limit = Math.min(Math.max(parseInt(limit) || 10, 1), 50);
  page = Math.max(parseInt(page) || 1, 1);
  const offset = (page - 1) * limit;
  let sql = `
    SELECT
      L_ListingID, L_DisplayId, L_Address, L_City, L_Zip,
      L_SystemPrice AS price, L_Keyword2 AS beds, LM_Dec_3 AS baths,
      LM_Int2_3 AS sqft, L_Type_ AS type, L_Status AS status,
      LMD_MP_Latitude AS lat, LMD_MP_Longitude AS lng,
      YearBuilt, AssociationFee, DaysOnMarket,
      PoolPrivateYN, ViewYN, FireplaceYN, PhotoCount,
      LA1_UserFirstName, LA1_UserLastName, LO1_OrganizationName
    FROM rets_property WHERE L_Status = 'Active'
  `;
  const params = [];

  if (filters.city)     { sql += " AND L_City = ?";        params.push(filters.city); }
  if (filters.maxPrice) { sql += " AND L_SystemPrice <= ?"; params.push(filters.maxPrice); }
  if (filters.beds)     { sql += " AND L_Keyword2 >= ?";    params.push(filters.beds); }
  if (filters.baths)    { sql += " AND LM_Dec_3 >= ?";      params.push(filters.baths); }
  if (filters.sqft)     { sql += " AND LM_Int2_3 >= ?";     params.push(filters.sqft); }
  if (filters.type)     { sql += " AND L_Type_ = ?";        params.push(filters.type); }
  if (filters.pool)     { sql += " AND PoolPrivateYN = ?";  params.push(filters.pool); }
  if (filters.hasView)  { sql += " AND ViewYN = ?";         params.push(filters.hasView); }

  sql += ` ORDER BY L_SystemPrice ASC LIMIT ${limit} OFFSET ${offset}`;
  return query(sql, params);
}

export async function getSoldComps(city, months = 12) {
  months = Math.min(Math.max(parseInt(months) || 12, 1), 60);
  const sql = `
    SELECT
      ListingKey, UnparsedAddress, City, CloseDate, ClosePrice,
      OriginalListPrice, ListPrice, DaysOnMarket,
      BedroomsTotal, BathroomsTotalInteger, LivingArea,
      PropertyType, PropertySubType, YearBuilt,
      ListAgentFullName, ListOfficeName, BuyerOfficeName
    FROM california_sold
    WHERE City = ?
      AND CloseDate >= DATE_SUB(CURDATE(), INTERVAL ? MONTH)
      AND CloseDate <= CURDATE()
      AND PropertyType = 'Residential'
    ORDER BY CloseDate DESC
    LIMIT 50
  `;
  return query(sql, [city, months]);
}

// ---- Property cards: turn database rows into short readable text ----
const money = n => (n == null ? "?" : "$" + Number(n).toLocaleString("en-US"));
const num = n => (n == null ? "?" : Number(n).toLocaleString("en-US"));
const pretty = t => (t || "").replace(/([a-z])([A-Z])/g, "$1 $2");

export function formatListingCard(l) {
  const extras = [l.PoolPrivateYN === "1" ? "pool" : null, l.ViewYN === "1" ? "view" : null]
    .filter(Boolean).join(", ");
  return [
    `${l.L_Address ?? "(address not listed)"}, ${l.L_City} ${l.L_Zip ?? ""}`.trim(),
    `${money(l.price)} | ${num(l.beds)} bd / ${num(l.baths)} ba | ${num(l.sqft)} sq ft | ${pretty(l.type)}`,
    `${num(l.DaysOnMarket)} days on market${extras ? " | " + extras : ""} | MLS# ${l.L_DisplayId}`,
  ].join("\n");
}

export function formatSoldCard(s) {
  return [
    `${s.UnparsedAddress ?? "(address not listed)"}, ${s.City}`,
    `Sold ${money(s.ClosePrice)} on ${s.CloseDate} (listed at ${money(s.ListPrice)}) | ${num(s.DaysOnMarket)} days on market`,
    `${num(s.BedroomsTotal)} bd / ${num(s.BathroomsTotalInteger)} ba | ${num(s.LivingArea)} sq ft | ${pretty(s.PropertySubType)}`,
  ].join("\n");
}
