import type { EscalationStatus, Priority, SummaryStatus } from "@/types";

const priorityStyles: Record<Priority, string> = {
  high: "bg-red-50 text-red-700 ring-red-600/10",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/10",
  low: "bg-sky-50 text-sky-700 ring-sky-600/10",
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`badge ring-1 ring-inset ${priorityStyles[priority]}`}>
      <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" />
      {priority}
    </span>
  );
}

export function StatusBadge({ status }: { status: EscalationStatus }) {
  return (
    <span className={`badge ${status === "open" ? "bg-emerald/10 text-emerald" : "bg-slate-100 text-slate-600"}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function SummaryBadge({ status }: { status: SummaryStatus }) {
  return (
    <span className="text-xs font-semibold text-sage">
      {status === "pending" ? "•••" : status === "ready" ? "✓" : "!"}
    </span>
  );
}

