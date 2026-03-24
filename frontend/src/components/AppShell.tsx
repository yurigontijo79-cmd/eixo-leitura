import { NavLink, Outlet } from 'react-router-dom';

const navigationItems = [
  { to: '/', label: 'Início' },
  { to: '/current', label: 'Leitura atual' },
  { to: '/completed', label: 'Concluídos' },
];

export function AppShell() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <p className="brand-mark">EIXO</p>
          <p className="eyebrow">Leitura</p>
          <h1>Leitura guiada com percurso.</h1>
          <p className="sidebar-copy">
            Um espaço para escolher com calma, iniciar com intenção e manter memória do caminho.
          </p>
        </div>

        <nav className="nav">
          {navigationItems.map((item, index) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'nav-link nav-link-active' : 'nav-link'
              }
            >
              <span className="nav-index">{String(index + 1).padStart(2, '0')}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
