import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileAudio, Play, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import axios from 'axios';

interface Call {
    call_id: string;
    agent_id: string;
    customer_id: string;
    status: string;
    created_at: string;
}

interface DashboardProps {
    onSelectCall: (id: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onSelectCall }) => {
    const [isUploading, setIsUploading] = useState(false);
    const [recentCalls, setRecentCalls] = useState<Call[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const fetchCalls = async () => {
        try {
            const response = await axios.get('/api/calls');
            setRecentCalls(response.data);
        } catch (error) {
            console.error('Failed to fetch calls:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCalls();
    }, []);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('audio', file);
        formData.append('agent_id', 'Sales Agent'); // Default for demo
        formData.append('customer_id', 'Lead Client'); // Default for demo

        try {
            const response = await axios.post('/api/transcribe', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            onSelectCall(response.data.call_id);
        } catch (error: any) {
            console.error('Upload failed:', error);
            const detail = error.response?.data?.detail || error.message;
            alert(`Upload or processing failed: ${detail}`);
        } finally {
            setIsUploading(false);
        }
    };

    const triggerFileSelect = () => {
        fileInputRef.current?.click();
    };

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <header style={{ marginBottom: '3rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Welcome back, Agent</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Upload a new call recording to start AI analysis.</p>
            </header>

            {/* Hidden File Input */}
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                accept="audio/*"
            />

            {/* Upload Zone */}
            <section className="glass-panel" style={{
                padding: '4rem 2rem', textAlign: 'center', marginBottom: '3rem',
                border: '2px dashed var(--border-glass)', position: 'relative',
                overflow: 'hidden'
            }}>
                <div style={{ position: 'relative', zIndex: 1 }}>
                    <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        backgroundColor: 'rgba(0, 245, 255, 0.1)', display: 'inline-flex',
                        alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem'
                    }}>
                        {isUploading ? <Loader2 className="animate-spin" color="var(--accent-primary)" size={32} /> : <Upload color="var(--accent-primary)" size={32} />}
                    </div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
                        {isUploading ? 'AI is analyzing your call...' : 'Drop call recording here'}
                    </h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
                        {isUploading ? 'This may take a minute depending on call length.' : 'Supports MP3, WAV (Max 50MB)'}
                    </p>
                    <button
                        disabled={isUploading}
                        onClick={triggerFileSelect}
                        style={{
                            padding: '0.75rem 2rem', borderRadius: '8px', border: 'none',
                            background: isUploading ? 'var(--text-muted)' : 'var(--accent-primary)',
                            color: '#000', fontWeight: 600,
                            cursor: isUploading ? 'wait' : 'pointer', transition: 'var(--transition-smooth)'
                        }}>
                        {isUploading ? 'Processing...' : 'Select File'}
                    </button>
                </div>
            </section>

            {/* Recent Activity */}
            <section>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Recent Analysis</h3>
                    <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', cursor: 'pointer' }} onClick={fetchCalls}>Refresh</span>
                </div>

                {isLoading ? (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading history...</div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                        {recentCalls.map((call) => (
                            <div
                                key={call.call_id}
                                className="glass-panel"
                                onClick={() => onSelectCall(call.call_id)}
                                style={{
                                    padding: '1.5rem', cursor: 'pointer', transition: 'var(--transition-smooth)',
                                    display: 'flex', alignItems: 'flex-start', gap: '1rem'
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-4px)')}
                                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
                            >
                                <div style={{
                                    padding: '0.75rem', borderRadius: '10px', backgroundColor: 'rgba(255,255,255,0.05)'
                                }}>
                                    <FileAudio size={24} color="var(--text-secondary)" />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <h4 style={{ fontSize: '1rem', marginBottom: '0.25rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {call.call_id.substring(0, 12)}...
                                    </h4>
                                    <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                        <span>{new Date(call.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <div style={{
                                    padding: '0.4rem', borderRadius: '50%',
                                    backgroundColor: call.status === 'completed' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)'
                                }}>
                                    <CheckCircle2 size={16} color={call.status === 'completed' ? 'var(--accent-success)' : 'var(--accent-error)'} />
                                </div>
                            </div>
                        ))}
                        {recentCalls.length === 0 && (
                            <div className="glass-panel" style={{ padding: '2rem', gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-muted)' }}>
                                No calls analyzed yet. Upload your first one above!
                            </div>
                        )}
                    </div>
                )}
            </section>

            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
        </div>
    );
};

export default Dashboard;
