import React, { useState, useEffect } from 'react';
import { ArrowLeft, Play, Download, Share2, Info, MessageSquare, AlertCircle, TrendingUp, Loader2 } from 'lucide-react';
import axios from 'axios';

interface Segment {
    speaker: string;
    text: string;
    start_time: number;
    end_time: number;
    sentiment?: string;
    is_coachable: boolean;
    coachable_type?: string;
}

interface CallDetail {
    call_id: string;
    status: string;
    transcript: string;
    segments: Segment[];
    created_at: string;
}

interface CallAnalysisProps {
    callId: string;
    onBack: () => void;
}

const CallAnalysis: React.FC<CallAnalysisProps> = ({ callId, onBack }) => {
    const [callData, setCallData] = useState<CallDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isReplaying, setIsReplaying] = useState(false);

    useEffect(() => {
        const fetchCallDetail = async () => {
            try {
                const response = await axios.get(`/api/calls/${callId}`);
                setCallData(response.data);
            } catch (error) {
                console.error('Failed to fetch call details:', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchCallDetail();
    }, [callId]);

    const handleReplay = async () => {
        setIsReplaying(true);
        try {
            const response = await axios.post('/api/replay', { call_id: callId }, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('audio');
            link.src = url;
            link.play();
        } catch (error) {
            console.error('Replay failed:', error);
            alert('No coachable moments found to replay, or generation failed.');
        } finally {
            setIsReplaying(false);
        }
    };

    if (isLoading) {
        return (
            <div style={{ height: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)' }}>
                <Loader2 className="animate-spin" size={48} />
            </div>
        );
    }

    if (!callData) return <div style={{ color: 'var(--accent-error)' }}>Error loading call data.</div>;

    const coachableMoments = callData.segments.filter(s => s.is_coachable);

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <button
                onClick={onBack}
                style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none',
                    border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', marginBottom: '2rem',
                    fontSize: '0.9rem', padding: '0.5rem 0'
                }}
            >
                <ArrowLeft size={16} /> Back to Dashboard
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '2rem' }}>
                {/* Main Transcript Content */}
                <div>
                    <header className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>Call Analysis</h2>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>ID: {callData.call_id}</p>
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem' }}>
                            <button className="action-btn"><Share2 size={18} /></button>
                            <button className="action-btn" onClick={() => window.print()}><Download size={18} /></button>
                            <button
                                disabled={isReplaying}
                                onClick={handleReplay}
                                style={{
                                    padding: '0.6rem 1.25rem', borderRadius: '8px', border: 'none',
                                    background: 'var(--accent-primary)', color: '#000', fontWeight: 600,
                                    display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: isReplaying ? 'wait' : 'pointer'
                                }}>
                                {isReplaying ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} fill="currentColor" />}
                                Play Replay
                            </button>
                        </div>
                    </header>

                    <section className="glass-panel" style={{ padding: '2rem', maxHeight: '600px', overflowY: 'auto' }}>
                        <h3 style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '1.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Transcript</h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            {callData.segments.map((item, idx) => (
                                <div key={idx} style={{
                                    display: 'flex', gap: '1rem',
                                    padding: item.is_coachable ? '1rem' : '0',
                                    borderRadius: '8px',
                                    border: item.is_coachable ? '1px solid rgba(168, 85, 247, 0.2)' : 'none',
                                    background: item.is_coachable ? 'rgba(168, 85, 247, 0.05)' : 'none'
                                }}>
                                    <div style={{
                                        width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0,
                                        backgroundColor: item.speaker === 'speaker_0' ? 'rgba(0, 245, 255, 0.1)' : 'rgba(168, 85, 247, 0.1)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '0.75rem', fontWeight: 700,
                                        color: item.speaker === 'speaker_0' ? 'var(--accent-primary)' : 'var(--accent-secondary)'
                                    }}>
                                        {item.speaker === 'speaker_0' ? 'A' : 'C'}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                                            <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                                                {item.speaker === 'speaker_0' ? 'Sales Agent' : 'Customer'}
                                                {item.sentiment && <span style={{ marginLeft: '1rem', color: item.sentiment === 'POSITIVE' ? 'var(--accent-success)' : item.sentiment === 'NEGATIVE' ? 'var(--accent-error)' : 'var(--text-muted)', fontSize: '0.7rem' }}>• {item.sentiment}</span>}
                                            </p>
                                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{Math.floor(item.start_time / 60)}:{Math.floor(item.start_time % 60).toString().padStart(2, '0')}</span>
                                        </div>
                                        <p style={{ fontSize: '1rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>{item.text}</p>
                                        {item.is_coachable && (
                                            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                                                <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-secondary)', color: '#fff' }}>
                                                    {item.coachable_type?.replace('_', ' ')}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                </div>

                {/* Sidebar Insights */}
                <aside style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* Coachable Moments */}
                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <AlertCircle size={16} color="var(--accent-secondary)" /> Coachable Moments
                        </h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {coachableMoments.length > 0 ? coachableMoments.map((moment, idx) => (
                                <div key={idx} style={{
                                    padding: '1rem', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.03)',
                                    borderLeft: `3px solid ${moment.coachable_type === 'objection' ? 'var(--accent-error)' : 'var(--accent-success)'}`
                                }}>
                                    <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem', color: moment.coachable_type === 'objection' ? 'var(--accent-error)' : 'var(--accent-success)' }}>
                                        {moment.coachable_type?.replace('_', ' ')}
                                    </p>
                                    <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-primary)' }}>"{moment.text.substring(0, 60)}..."</p>
                                </div>
                            )) : (
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No coachable moments identified in this call.</p>
                            )}
                        </div>
                    </div>

                    <div className="glass-panel" style={{ padding: '1.5rem' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Info size={16} color="var(--accent-primary)" /> AI Insights
                        </h3>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            Total Segments: {callData.segments.length}<br />
                            Detected Speaker Switch: {new Set(callData.segments.map(s => s.speaker)).size}
                        </p>
                    </div>
                </aside>
            </div>

            <style>{`
        .action-btn {
          width: 42px; height: 42px; border-radius: 8px; border: 1px solid var(--border-glass);
          background: rgba(255,255,255,0.03); color: var(--text-secondary);
          display: flex; alignItems: center; justifyContent: center; cursor: pointer;
          transition: var(--transition-smooth);
        }
        .action-btn:hover {
          background: rgba(255,255,255,0.1); color: var(--text-primary);
        }
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

export default CallAnalysis;
