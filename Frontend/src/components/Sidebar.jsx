import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", section: "Overview" },
  { to: "/vehicles", label: "Vehicle Registry", section: "Fleet" },
  { to: "/drivers", label: "Drivers", section: "Fleet" },
  { to: "/maintenance", label: "Maintenance", section: "Fleet" },
  { to: "/trips", label: "Trips", section: "Operations" },
  { to: "/fuel-expenses", label: "Fuel & Expenses", section: "Operations" },
  { to: "/reports", label: "Reports & Analytics", section: "Insights" },
];

function initials(name) {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  let lastSection = null;

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="mark">TO</div>
        <div className="name">TransitOps</div>
      </div>

      <nav>
        {NAV_ITEMS.map((item) => {
          const showSection = item.section !== lastSection;
          lastSection = item.section;
          return (
            <React.Fragment key={item.to}>
              {showSection && <div className="nav-section-label">{item.section}</div>}
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              >
                <span className="dot" />
                {item.label}
              </NavLink>
            </React.Fragment>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        {user && (
          <div className="user-chip">
            <div className="avatar">{initials(user.name)}</div>
            <div>
              <div className="u-name">{user.name}</div>
              <div className="u-role">{user.role}</div>
            </div>
          </div>
        )}
        <button className="logout-btn" onClick={logout}>Sign out</button>
      </div>
    </aside>
  );
}