// Serves the product pictures of data/axiom_products/images/ to the catalog page (J-19, C-65).  Owner: Janvia.
// GET /catalog/image?file=images/<name>.jpg|png  (the `file` of images.json).  Only that folder, only plain names, only .jpg / .png;
// the sign-in guard in proxy.ts covers this path like every other page.
// ponytail: the web server reads the repo's data folder directly, which only works while web/ and data/ sit side by side.
// Replace it with GET /api/catalog/image once Piyush adds that route (contract change), then delete this file.
import { readFile } from "node:fs/promises";
import path from "node:path";

const FOLDER = path.join(process.cwd(), "..", "data", "axiom_products", "images");
const TYPES: Record<string, string> = { ".jpg": "image/jpeg", ".png": "image/png" };

export async function GET(request: Request) {
  const file = new URL(request.url).searchParams.get("file") ?? "";
  const name = file.startsWith("images/") ? file.slice("images/".length) : file;
  if (!/^[a-z0-9][a-z0-9-]*\.(jpg|png)$/.test(name)) return new Response("Not found", { status: 404 });
  try {
    const bytes = await readFile(path.join(FOLDER, name));
    return new Response(new Uint8Array(bytes), { headers: { "Content-Type": TYPES[path.extname(name)], "Cache-Control": "private, max-age=3600" } });
  } catch {
    return new Response("Not found", { status: 404 });
  }
}
