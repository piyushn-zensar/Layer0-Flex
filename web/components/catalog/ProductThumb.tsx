"use client";
// A product's picture in the table (J-19, C-65): its family's verified image, otherwise a placeholder that says why
// (no image, image not verified, image did not load, still loading).  Never breaks when a file is missing.  Owner: Janvia.
import { useState } from "react";
import type { ProductRow } from "@/lib/types";
import { hasUnverifiedImage, imageOf, type MediaIndex } from "./products";

/** The address of an image file of data/axiom_products/images/ (served by web/app/catalog/image/route.ts). */
export const imageUrl = (file: string) => `/catalog/image?file=${encodeURIComponent(file)}`;

export default function ProductThumb({ row, idx, ready }: { row: ProductRow; idx: MediaIndex; ready: boolean }) {
  const [failed, setFailed] = useState<string>();
  const image = imageOf(row, idx);
  if (image && failed !== image.file) {
    return <img className="thumb" src={imageUrl(image.file)} alt={`${row.series ?? row.part_number}: ${image.kind} from ${image.source_file}, page ${image.page}`}
      title={`${image.kind === "photo" ? "Photograph" : "Illustration"} of the ${row.series ?? "product"} family, from ${image.source_file}, page ${image.page}`}
      loading="lazy" width={44} height={44} onError={() => setFailed(image.file)} />;
  }
  const why = failed ? "The image file could not be loaded"
    : !row.family_key ? "No image: the supplied PDFs show no picture for this product"
    : !ready ? "Loading"
    : hasUnverifiedImage(row, idx) ? "Image not verified: a picture exists but the page does not name this product beside it"
    : "No image: the supplied PDFs show no picture for this product";
  return <span className="thumb ph" role="img" aria-label={why} title={why}>
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="14" rx="2" fill="none" stroke="currentColor" strokeWidth="1.5" /><circle cx="9" cy="10" r="1.6" fill="currentColor" /><path d="M4 17l5-5 4 4 3-3 4 4" fill="none" stroke="currentColor" strokeWidth="1.5" /></svg>
  </span>;
}
