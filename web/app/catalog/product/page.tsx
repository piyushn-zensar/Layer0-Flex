"use client";
// Product details page (J-20): /catalog/product?part=<part number or catalog ID>, the deep link the configurator's candidates and the
// all-products table use.  Owner: Janvia (built by Piyush, 23 Oct).
import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import PageHead from "@/components/shell/PageHead";
import { EmptyState, Skeleton } from "@/components/ui";
import ProductDetails from "@/components/catalog/ProductDetails";

function ProductPage() {
  const part = useSearchParams().get("part") ?? "";
  return (
    <div className="content">
      <p className="muted"><Link href="/catalog">← All products</Link></p>
      <PageHead title={part || "Product"} help="Everything the catalog holds about one product: its values with their sources, conflicts with the web pages, related boards or parts, published ratings, documents and images." />
      {part ? <ProductDetails key={part} part={part} /> : <EmptyState title="No product chosen" hint="Open a product from the Product catalog." />}
    </div>
  );
}

export default function ProductRoute() {
  return <Suspense fallback={<div className="content"><Skeleton lines={4} /></div>}><ProductPage /></Suspense>;
}
