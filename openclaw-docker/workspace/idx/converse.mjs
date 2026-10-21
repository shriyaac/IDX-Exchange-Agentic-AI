// Week 4: multi-turn conversational search.
//   node converse.mjs <userId> '<message>'
// Each message is merged into the user's saved session (sessions.mjs). The script then
// either asks the next follow-up question (city -> budget -> property type) or, once it
// has enough, searches rets_property with everything remembered so far.
import { parsePropertyQuery } from "./parse-query.mjs";
import { searchActiveListings, formatListingCard } from "./queries.mjs";
import { getSession, updateSession, clearSession } from "./sessions.mjs";
import { closePool } from "./db.mjs";

const FILTERS = ["city", "maxPrice", "beds", "baths", "sqft", "type", "pool", "hasView"];
const [userId, ...words] = process.argv.slice(2);
const message = words.join(" ").trim();

// Short answers to a follow-up question ("Irvine", "1.2M", "any") don't contain the
// words the Week 2 parser looks for ("in Irvine", "under $1.2M"), so read them here.
function readShortAnswer(asked, text) {
  if (asked === "city" && /^[A-Za-z][A-Za-z .'-]*$/.test(text)) {
    return { city: text.replace(/\b\w/g, c => c.toUpperCase()) };
  }
  if (asked === "budget") {
    const m = text.match(/\$?\s*([\d,.]+)\s*(k|m|million)?/i);
    if (m) {
      let n = Number(m[1].replace(/,/g, ""));
      const unit = (m[2] || "").toLowerCase();
      if (unit === "k") n *= 1000;
      if (unit === "m" || unit === "million") n *= 1_000_000;
      if (n > 0) return { maxPrice: n };
    }
  }
  if (asked === "type" && /\b(any|no preference|doesn'?t matter|either|all)\b/i.test(text)) {
    return { typeAnswered: true };
  }
  return {};
}

function nextQuestion(s) {
  if (!s.city) return ["city", "Which city are you looking in?"];
  if (!s.maxPrice) return ["budget", "What is your budget?"];
  if (!s.type && !s.typeAnswered) return ["type", "Any preference: condo, townhome, or single family?"];
  return [null, null];
}

try {
  if (!userId || !message) {
    console.log("Usage: node converse.mjs <userId> '<message>'");
  } else if (/\b(start over|new search|reset)\b/i.test(message)) {
    clearSession(userId);
    console.log("Agent: Okay, starting a new search. Which city are you looking in?");
    updateSession(userId, { conversationStep: 1, asked: "city" });
  } else {
    let s = getSession(userId);
    const wantsMore = /^(more|next|show more|next page)\b/i.test(message);

    if (!wantsMore) {
      // 1. Merge what this message says into the session (only filters it mentions).
      const parsed = await parsePropertyQuery(message);
      const updates = {};
      for (const f of FILTERS) if (parsed[f] != null) updates[f] = parsed[f];
      // Short answers only fill in what the parser didn't already find.
      const short = Object.keys(updates).length ? {} : readShortAnswer(s.asked, message);
      for (const [k, v] of Object.entries(short)) if (updates[k] == null) updates[k] = v;
      if (updates.type) updates.typeAnswered = true;
      s = updateSession(userId, { ...updates, conversationStep: (s.conversationStep || 0) + 1, page: 1 });
    }

    // 2. Ask the next follow-up question, or search.
    const [asked, question] = nextQuestion(s);
    if (asked && !wantsMore) {
      updateSession(userId, { asked });
      console.log("Agent: " + question);
    } else {
      const page = wantsMore ? (s.page || 1) + 1 : 1;
      const filters = Object.fromEntries(FILTERS.map(f => [f, s[f] ?? null]));
      const rows = await searchActiveListings(filters, page, 5);
      updateSession(userId, {
        asked: null, page,
        lastResults: rows.map(r => ({ id: r.L_ListingID, address: r.L_Address, price: r.price })),
      });
      console.log("Searching with: " + JSON.stringify(filters));
      if (rows.length === 0) {
        console.log(page > 1 ? "Agent: No more listings." :
          "Agent: No listings match. Try a higher budget or a different property type, or say 'start over'.");
      } else {
        console.log(`Agent: Here are listings ${(page - 1) * 5 + 1}-${(page - 1) * 5 + rows.length}, cheapest first:\n`);
        rows.forEach((r, i) => console.log(`${(page - 1) * 5 + i + 1}. ${formatListingCard(r)}\n`));
        if (rows.length === 5) console.log("Say 'more' for the next 5, or add a filter (e.g. 'with a pool').");
      }
    }
  }
} catch (err) {
  console.error("Conversation failed: " + err.message);
  process.exitCode = 1;
} finally {
  await closePool();
}
