import { useLocation, NavLink, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useQueryClient } from '@tanstack/react-query';
import { logout } from '../store/authSlice';

const NAV_ADJUSTER = [
  { to: '/dashboard', label: 'Dashboard', icon: '▣' },
  { to: '/claims',    label: 'Claims',    icon: '📋' },
];

const NAV_MANAGER = [
  { to: '/dashboard',       label: 'Dashboard',     icon: '▣' },
  { to: '/claims',          label: 'Claims',         icon: '📋' },
  { to: '/policies/upload', label: 'Upload Policy',  icon: '📄' },
  { to: '/users',           label: 'Users',          icon: '👥' },
];

export default function AppShell({ title, children }) {
  const user = useSelector((state) => state.auth.user);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const isManager = user?.role === 'MANAGER';
  const navLinks = isManager ? NAV_MANAGER : NAV_ADJUSTER;

  const handleLogout = () => {
    dispatch(logout());
    queryClient.clear();
    navigate('/login', { replace: true });
  };

  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : '??';

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-title">Domain Copilot</div>
          <div className="sidebar-logo-sub">Claims Adjudication</div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Navigation</div>
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                'sidebar-link' + (isActive ? ' active' : '')
              }
            >
              <span>{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div>
              <div className="sidebar-user-name">
                {user?.username ?? '—'}
              </div>
              <div className="sidebar-user-role">
                {user?.role ?? 'Loading…'}
              </div>
            </div>
          </div>
          <button className="sidebar-logout-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main-content">
        {title && (
          <header className="main-header">
            <span className="main-header-title">{title}</span>
          </header>
        )}
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
