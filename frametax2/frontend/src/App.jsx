import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import Production from "./screens/Production";
import PackageIntelligence from "./screens/PackageIntelligence";
import Recommendations from "./screens/Recommendations";
import Scenarios from "./screens/Scenarios";
import Evidence from "./screens/Evidence";

const NAV = [
  { to: "/", label: "Production", exact: true },
  { to: "/package", label: "Package Intelligence" },
  { to: "/recommendations", label: "Recommendations" },
  { to: "/scenarios", label: "Scenarios & Structures" },
  { to: "/evidence", label: "Evidence & Legal" },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header>
          <h1 className="brand">CineGlobe</h1>
          <nav>
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.exact}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Production />} />
            <Route path="/package" element={<PackageIntelligence />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/scenarios" element={<Scenarios />} />
            <Route path="/evidence" element={<Evidence />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
