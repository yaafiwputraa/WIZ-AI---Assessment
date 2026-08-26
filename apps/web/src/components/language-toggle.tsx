import type { Locale } from "@/types";

export function LanguageToggle({
  locale,
  onChange,
}: {
  locale: Locale;
  onChange: (locale: Locale) => void;
}) {
  return (
    <div className="flex rounded-full border border-black/10 bg-white/80 p-1 text-xs font-bold shadow-sm">
      {(["id", "en"] as Locale[]).map((item) => (
        <button
          key={item}
          type="button"
          aria-label={item === "id" ? "Gunakan Bahasa Indonesia" : "Use English"}
          aria-pressed={locale === item}
          onClick={() => onChange(item)}
          className={`rounded-full px-3 py-1.5 transition ${
            locale === item ? "bg-ink text-white" : "text-sage hover:text-ink"
          }`}
        >
          {item.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

