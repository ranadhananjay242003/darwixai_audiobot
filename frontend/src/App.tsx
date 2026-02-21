import React, { useState } from 'react';
import './styles/global.css';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import CallAnalysis from './components/CallAnalysis';

const App: React.FC = () => {
    const [activeCallId, setActiveCallId] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('dashboard');

    const handleSelectCall = (id: string) => {
        setActiveCallId(id);
    };

    const handleNav = (tab: string) => {
        setActiveTab(tab);
        setActiveCallId(null);
    };

    return (
        <div className="app-container">
            <Sidebar activeTab={activeTab} onSelectTab={handleNav} />

            <main style={{ padding: '2rem', overflowY: 'auto', height: '100vh', width: '100%' }}>
                {activeCallId ? (
                    <CallAnalysis callId={activeCallId} onBack={() => setActiveCallId(null)} />
                ) : activeTab === 'dashboard' ? (
                    <Dashboard onSelectCall={handleSelectCall} />
                ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>{activeTab.toUpperCase()}</h2>
                        <p>This module is coming soon in the next update.</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default App;
