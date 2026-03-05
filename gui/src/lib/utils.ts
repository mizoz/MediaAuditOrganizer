import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export function formatDate(date: Date | string): string {
  try {
    const d = typeof date === "string" ? new Date(date) : date;
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(date);
  }
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "success":
    case "verified":
    case "completed":
      return "bg-status-success";
    case "processing":
    case "active":
    case "running":
      return "bg-status-processing";
    case "pending":
      return "bg-status-idle";
    case "error":
    case "failed":
      return "bg-status-error";
    case "cancelled":
      return "bg-slate-600";
    default:
      return "bg-slate-600";
  }
}
