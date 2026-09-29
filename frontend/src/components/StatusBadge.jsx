import { Clock, CheckCircle2, AlertTriangle, Phone, Calendar, ArrowRightLeft, XCircle, MessageSquare, CircleDot } from 'lucide-react';

const STATUS_MAP = {
  DUE:         { label: 'Due',          color: 'bg-blue-50 text-blue-700 ring-blue-200',         icon: Clock },
  CONTACTED:   { label: 'Contacted',    color: 'bg-sky-50 text-sky-700 ring-sky-200',            icon: Phone },
  RESPONDED:   { label: 'Responded',    color: 'bg-indigo-50 text-indigo-700 ring-indigo-200',   icon: MessageSquare },
  BOOKED:      { label: 'Booked',       color: 'bg-emerald-50 text-emerald-700 ring-emerald-200', icon: Calendar },
  RESCHEDULED: { label: 'Rescheduled',  color: 'bg-amber-50 text-amber-700 ring-amber-200',      icon: ArrowRightLeft },
  OVERDUE:     { label: 'Overdue',      color: 'bg-red-50 text-red-700 ring-red-200',            icon: AlertTriangle },
  ESCALATED:   { label: 'Escalated',    color: 'bg-orange-50 text-orange-700 ring-orange-200',   icon: AlertTriangle },
  NO_RESPONSE: { label: 'No Response',  color: 'bg-slate-100 text-slate-500 ring-slate-200',     icon: XCircle },
  COMPLETED:   { label: 'Completed',    color: 'bg-green-50 text-green-700 ring-green-200',      icon: CheckCircle2 },
};

const PRIORITY_MAP = {
  LOW:    'bg-slate-100 text-slate-600',
  MEDIUM: 'bg-blue-50 text-blue-600',
  HIGH:   'bg-orange-50 text-orange-600',
  URGENT: 'bg-red-50 text-red-600',
};

export function StatusBadge({ status }) {
  const s = STATUS_MAP[status] || STATUS_MAP.DUE;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ring-1 ring-inset ${s.color}`}>
      <Icon className="w-3 h-3" />
      {s.label}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-semibold ${PRIORITY_MAP[priority] || PRIORITY_MAP.MEDIUM}`}>
      {priority}
    </span>
  );
}

export function timeAgo(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}
