import { ShieldCheck } from "lucide-react";

export function StaffAccessLoading({ message }: { message: string }) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#f6f8f6] px-5">
      <div className="flex items-center gap-3 rounded-2xl border border-black/5 bg-white px-5 py-4 text-sm font-bold text-sage shadow-sm">
        <ShieldCheck size={19} className="text-emerald" />
        {message}
      </div>
    </main>
  );
}
