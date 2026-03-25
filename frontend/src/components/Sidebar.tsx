'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/analyze', label: 'Analyze', icon: '🔍' },
  { href: '/incidents', label: 'Incidents', icon: '🚨' },
  { href: '/logs', label: 'Logs', icon: '📋' },
  { href: '/live', label: 'Live Demo', icon: '⚡' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="shield-icon">🛡️</div>
        <div>
          <h1>AI Secure Log<br />Analyzer</h1>
          <span>Security Operations</span>
        </div>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
