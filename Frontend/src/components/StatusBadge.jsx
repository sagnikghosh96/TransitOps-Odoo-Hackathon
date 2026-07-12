import React from "react";

const COLOR_MAP = {
  Available: "badge-teal",
  "On Trip": "badge-accent",
  "In Shop": "badge-yellow",
  Retired: "badge-grey",
  "Off Duty": "badge-grey",
  Suspended: "badge-red",
  Draft: "badge-grey",
  Dispatched: "badge-accent",
  Completed: "badge-teal",
  Cancelled: "badge-red",
  Active: "badge-yellow",
  Closed: "badge-teal",
};

export default function StatusBadge({ status }) {
  const cls = COLOR_MAP[status] || "badge-grey";
  return <span className={`badge ${cls}`}>{status}</span>;
}