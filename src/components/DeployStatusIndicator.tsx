import React, { useState, useEffect } from 'react';

interface WorkflowRun {
  id: number;
  status: 'queued' | 'in_progress' | 'completed' | string;
  conclusion: 'success' | 'failure' | 'cancelled' | string | null;
  html_url: string;
  updated_at: string;
}

export function DeployStatusIndicator() {
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await fetch(
        'https://api.github.com/repos/meng10730/meng10730.github.io/actions/runs?per_page=1&t=' + Date.now()
      );
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      if (data.workflow_runs && data.workflow_runs.length > 0) {
        setRun(data.workflow_runs[0]);
      }
    } catch (e) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      fetchStatus();
    }, run?.status === 'in_progress' || run?.status === 'queued' ? 10000 : 60000);
    return () => clearInterval(interval);
  }, [run?.status]);

  const getStatusBadge = () => {
    if (error) {
      return {
        color: '#8c8c8c',
        borderColor: 'rgba(140, 140, 140, 0.25)',
        text: '狀態暫無法取得',
        icon: '⚪',
      };
    }
    if (!run) {
      return {
        color: '#8c8c8c',
        borderColor: 'rgba(140, 140, 140, 0.25)',
        text: '檢查部署狀態...',
        icon: '⏳',
      };
    }
    if (run.status === 'in_progress' || run.status === 'queued') {
      return {
        color: '#d97706',
        borderColor: 'rgba(217, 119, 6, 0.35)',
        text: '網站發布構建中…',
        icon: '🟡',
      };
    }
    if (run.status === 'completed' && run.conclusion === 'success') {
      return {
        color: '#16a34a',
        borderColor: 'rgba(22, 163, 74, 0.35)',
        text: '線上網站已最新',
        icon: '🟢',
      };
    }
    if (run.status === 'completed' && run.conclusion === 'failure') {
      return {
        color: '#dc2626',
        borderColor: 'rgba(220, 38, 38, 0.35)',
        text: '部署構建失敗',
        icon: '🔴',
      };
    }
    return {
      color: '#4b5563',
      borderColor: 'rgba(75, 85, 99, 0.25)',
      text: run.status,
      icon: '🔵',
    };
  };

  const badge = getStatusBadge();

  return (
    <div
      style={{
        position: 'fixed',
        top: '1.25rem',
        right: '1.5rem',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.4rem 0.85rem',
        borderRadius: '9999px',
        backgroundColor: 'rgba(253, 252, 247, 0.95)',
        border: '1px solid ' + badge.borderColor,
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
        fontSize: '0.8rem',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        color: badge.color,
      }}
    >
      <span style={{ fontSize: '0.75rem' }}>{badge.icon}</span>
      <span style={{ fontWeight: 600 }}>{badge.text}</span>
      <button
        onClick={fetchStatus}
        title="手動重新整理部署狀態"
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0 0.2rem',
          fontSize: '0.75rem',
          color: badge.color,
          opacity: loading ? 0.4 : 0.8,
        }}
      >
        🔄
      </button>
    </div>
  );
}
