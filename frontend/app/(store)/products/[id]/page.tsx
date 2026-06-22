import { products } from "@/lib/api";
import { VariantSelector } from "@/components/product/VariantSelector";
import { notFound } from "next/navigation";

export default async function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await products.get(Number(id)).catch(() => null);
  if (!product) notFound();
  const image = product.images[0]?.image_url;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Image */}
        <div className="aspect-square bg-zinc-50 rounded-2xl overflow-hidden">
          {image ? (
            <img src={image} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-6xl text-gray-200">📦</div>
          )}
        </div>
        {/* Info */}
        <div className="flex flex-col gap-4">
          <div>
            <p className="text-sm text-gray-400 mb-1">{product.category_name}</p>
            <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
            {product.brand_name && <p className="text-sm text-gray-500 mt-1">by {product.brand_name}</p>}
          </div>
          <VariantSelector variants={product.variants} />
          {product.description && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
              <p className="text-sm text-gray-600 leading-relaxed">{product.description}</p>
            </div>
          )}
          {Object.keys(product.specifications).length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Specifications</h3>
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(product.specifications).map(([k, v]) => (
                    <tr key={k} className="border-t border-gray-100">
                      <td className="py-1.5 text-gray-500 pr-4">{k}</td>
                      <td className="py-1.5 text-gray-900 font-medium">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
