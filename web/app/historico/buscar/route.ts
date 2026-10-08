import { loadProfiles, searchProfiles } from "@/lib/profiles";

/** Players of the history by name, for the search box of /epocas. */
export async function GET(request: Request) {
  const query = new URL(request.url).searchParams.get("q") ?? "";
  const results = query.trim().length >= 2 ? searchProfiles(query, await loadProfiles()) : [];
  return Response.json(results, { headers: { "Cache-Control": "public, s-maxage=604800" } });
}
