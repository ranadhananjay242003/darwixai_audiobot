import React from 'react';
import { LayoutDashboard, Mic, Settings, History, BarChart3, TrendingUp } from 'lucide-react';

interface SidebarProps {
    activeTab: string;
    onSelectTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
    return (
        <aside className="glass-panel" style={{ margin: '1rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                    width: '32px', height: '32px',
                    background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                    borderRadius: '8px'
                }} />
                <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.025em' }}>DARWIX</h1>
            </div>

            <nav style={{ padding: '0 1rem', flex: 1 }}>
                <ul style={{ listStyle: 'none' }}>
                    <SidebarLink icon={<LayoutDashboard size={20} />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => onSelectTab('dashboard')} />
                    <SidebarLink icon={<History size={20} />} label="History" active={activeTab === 'history'} onClick={() => onSelectTab('history')} />
                    <SidebarLink icon={<Mic size={20} />} label="Real-time" active={activeTab === 'realtime'} onClick={() => onSelectTab('realtime')} />
                    <SidebarLink icon={<BarChart3 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => onSelectTab('analytics')} />
                </ul>
            </nav>

            <div style={{ padding: '1rem', borderTop: '1px solid var(--border-glass)' }}>
                <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <TrendingUp size={16} color="var(--accent-success)" />
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Accuracy Mode</span>
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Whisper Base v3 active</p>
                </div>
            </div>
        </aside>
    );
};

const SidebarLink: React.FC<{ icon: any, label: string, active?: boolean, onClick?: () => void }> = ({ icon, label, active, onClick }) => (
    <li
        onClick={onClick}
        style={{
            display: 'flex', alignItems: 'center', gap: '1rem',
            padding: '0.75rem 1rem', borderRadius: '8px',
            cursor: 'pointer', marginBottom: '0.5rem',
            backgroundColor: active ? 'rgba(0, 245, 255, 0.1)' : 'transparent',
            color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
            transition: 'var(--transition-smooth)'
        }}
        onMouseEnter={(e) => !active && (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)')}
        onMouseLeave={(e) => !active && (e.currentTarget.style.backgroundColor = 'transparent')}
    >
        {icon}
        <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{label}</span>
    </li>
);

export default Sidebar;
