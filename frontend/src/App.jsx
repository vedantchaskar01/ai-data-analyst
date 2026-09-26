import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Database, UploadCloud, Send, Loader2, Sparkles, User, 
  BarChart3, Code2, Table2, Command, Search, Share2, Download,
  LayoutDashboard, Settings, Activity, FolderOpen
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import './index.css';

const API_BASE = 'http://localhost:8000/api';
const COLORS = ['#2DD4BF', '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label">{label}</div>
        {payload.map((entry, index) => (
          <div key={index} style={{ color: entry.color || '#fff', fontSize: '0.9rem' }}>
            {entry.name}: <span style={{fontWeight: 600}}>{entry.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

function App() {
  const [dbInfo, setDbInfo] = useState(null);
  const [schema, setSchema] = useState(null);
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDbInfo();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, isQuerying]);

  const fetchDbInfo = async () => {
    try {
      const res = await axios.get(`${API_BASE}/db-info`);
      setDbInfo(res.data.db_info);
      setSchema(res.data.schema);
    } catch (err) {
      console.error("Error fetching DB info:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const tableName = file.name.split('.')[0].replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('table_name', tableName);

    setIsUploading(true);
    try {
      await axios.post(`${API_BASE}/import`, formData);
      await fetchDbInfo();
    } catch (err) {
      alert("Error uploading file: " + err.message);
    } finally {
      setIsUploading(false);
      if(fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const currentQuery = query.trim();
    setQuery('');
    
    setHistory(prev => [...prev, { role: 'user', content: currentQuery }]);
    setIsQuerying(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, { query: currentQuery });
      setHistory(prev => [...prev, { 
        role: 'assistant', 
        result: res.data,
        question: currentQuery
      }]);
    } catch (err) {
      setHistory(prev => [...prev, { 
        role: 'assistant', 
        error: err.response?.data?.detail || err.message 
      }]);
    } finally {
      setIsQuerying(false);
    }
  };

  const exportCSV = (data) => {
    if(!data || !data.length) return;
    const header = Object.keys(data[0]).join(',');
    const rows = data.map(obj => Object.values(obj).map(v => `"${v}"`).join(','));
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'export.csv';
    a.click();
  };

  const renderChart = (result) => {
    const { data, analysis } = result;
    const { chart_type, x_col, y_col } = analysis;
    
    if (chart_type === 'Metric' || (data.length === 1 && Object.keys(data[0]).length === 1)) {
        const key = y_col || Object.keys(data[0])[0];
        const val = data[0][key];
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'radial-gradient(circle at center, rgba(45, 212, 191, 0.1) 0%, transparent 60%)' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '4rem', fontWeight: 700, color: '#fff', letterSpacing: '-0.03em', textShadow: '0 0 30px rgba(45, 212, 191, 0.5)' }}>
                      {typeof val === 'number' ? val.toLocaleString() : val}
                    </div>
                    <div style={{ fontSize: '1rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.15em', marginTop: 8 }}>
                        {analysis.title || key.replace(/_/g, ' ')}
                    </div>
                </div>
            </div>
        );
    }

    if (!x_col || !y_col || !data || data.length === 0) return null;

    if (chart_type === 'Line' && data.length > 5) {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <defs>
              <linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis dataKey={x_col} stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 11}} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 11}} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey={y_col} stroke="var(--accent-cyan)" strokeWidth={3} fillOpacity={1} fill="url(#colorY)" />
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    if (chart_type === 'Bar') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis dataKey={x_col} stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 11}} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 11}} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{fill: 'rgba(255,255,255,0.02)'}} />
            <Bar dataKey={y_col} fill="var(--accent-blue)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    if (chart_type === 'Pie') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey={y_col} nameKey={x_col} cx="50%" cy="50%" innerRadius={70} outerRadius={120} paddingAngle={2} stroke="none">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    return null;
  };

  const ResultBlock = ({ result }) => {
    const [activeTab, setActiveTab] = useState('chart');
    const { sql, data, analysis, time_taken } = result;

    return (
      <div className="widget-card">
        <div className="widget-header">
          <div className="widget-title">
            <div className="widget-icon">
              <Sparkles size={18} />
            </div>
            <div className="widget-insight">{analysis?.insight || "Query completed successfully"}</div>
          </div>
          <div className="widget-actions">
            <button className="action-btn" title="Export CSV" onClick={() => exportCSV(data)}><Download size={16}/></button>
            <button className="action-btn" title="Share"><Share2 size={16}/></button>
          </div>
        </div>

        {data && data.length > 0 && (
          <div className="widget-body">
            <div className="widget-tabs">
              <button className={`w-tab ${activeTab === 'chart' ? 'active' : ''}`} onClick={() => setActiveTab('chart')}>
                <BarChart3 size={16}/> Visualization
              </button>
              <button className={`w-tab ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>
                <Table2 size={16}/> Data ({data.length})
              </button>
              <button className={`w-tab ${activeTab === 'sql' ? 'active' : ''}`} onClick={() => setActiveTab('sql')}>
                <Code2 size={16}/> Query
              </button>
              <div style={{marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center'}}>
                 {time_taken}s execution time
              </div>
            </div>

            {activeTab === 'chart' && analysis?.chart_type !== 'None' && (
              <div style={{ height: 350, width: '100%' }}>
                {renderChart(result)}
              </div>
            )}
            
            {(activeTab === 'chart' && analysis?.chart_type === 'None') && (
               <div style={{ height: 250, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                   <BarChart3 size={40} opacity={0.2} />
                   <p style={{marginTop: 12}}>No visualization recommended for this data shape.</p>
                   <button className="w-tab" style={{marginTop: 16, border: '1px solid var(--border-subtle)', padding: '8px 16px', borderRadius: 8}} onClick={() => setActiveTab('data')}>View Raw Data</button>
               </div>
            )}

            {activeTab === 'data' && (
              <div className="modern-table-wrapper" style={{ maxHeight: 350, overflow: 'auto' }}>
                <table className="modern-table">
                  <thead>
                    <tr>
                      {Object.keys(data[0]).map(k => (
                        <th key={k} style={{position: 'sticky', top: 0, zIndex: 1}}>{k.replace(/_/g, ' ')}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.slice(0, 100).map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((v, j) => (
                          <td key={j}>{v !== null ? v.toString() : 'NULL'}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'sql' && (
              <pre style={{ 
                background: 'rgba(0,0,0,0.5)', 
                padding: '24px', 
                borderRadius: '12px', 
                overflowX: 'auto',
                color: '#34D399',
                fontFamily: 'JetBrains Mono',
                fontSize: '0.85rem',
                border: '1px solid var(--border-subtle)'
              }}>
                {sql}
              </pre>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <div className="ambient-bg">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      
      <div className="layout-container">
        <aside className="sidebar">
          <div className="brand-header">
            <div className="brand-logo"><Sparkles size={16} /></div>
            <div className="brand-text">OmniData.ai</div>
          </div>

          <div className="sidebar-scroll">
            <div className="nav-section">
              <div className="nav-label">Workspace</div>
              <div className="nav-item active"><LayoutDashboard size={16}/> Analytics Canvas</div>
              <div className="nav-item"><FolderOpen size={16}/> Saved Reports</div>
              <div className="nav-item"><Activity size={16}/> Activity Log</div>
            </div>

            <div className="nav-section">
              <div className="nav-label">Data Sources</div>
              <div className="premium-dropzone" onClick={() => fileInputRef.current?.click()}>
                <input 
                  type="file" 
                  accept=".csv" 
                  style={{ display: 'none' }} 
                  ref={fileInputRef}
                  onChange={handleFileUpload} 
                />
                <div className="drop-icon-wrapper">
                  {isUploading ? <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} /> : <UploadCloud size={24} />}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                  {isUploading ? 'Ingesting Data...' : 'Drop CSV here'}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Auto-indexes & infers schema
                </div>
              </div>
            </div>

            <div className="nav-section">
              <div className="nav-label">Active Database</div>
              {schema ? Object.entries(schema).map(([tableName, meta]) => (
                <div key={tableName} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12, marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', fontWeight: 600, color: '#fff', marginBottom: 12 }}>
                    <Database size={14} color="var(--accent-cyan)" />
                    {tableName}
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                      {dbInfo?.tables?.[tableName] || 0} rows
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {meta.columns.slice(0, 5).map((col, idx) => (
                      <div key={idx} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono', paddingLeft: 8, borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
                        {col}
                      </div>
                    ))}
                    {meta.columns.length > 5 && (
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', paddingLeft: 8 }}>+ {meta.columns.length - 5} more fields</div>
                    )}
                  </div>
                </div>
              )) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '0 8px' }}>No connected schemas</div>
              )}
            </div>
          </div>
        </aside>

        <div className="main-wrapper">
          <header className="topbar">
            <div className="breadcrumb">
              <Database size={16} />
              <span>PostgreSQL Cluster</span>
              <span style={{color:'var(--border-subtle)'}}>/</span>
              <span className="active">Production</span>
            </div>
            <div className="topbar-actions">
              <div className="cmd-hint">
                <Search size={14} /> Search
                <span className="cmd-key">⌘K</span>
              </div>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-pink))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 600, fontSize: '0.9rem' }}>
                V
              </div>
            </div>
          </header>

          <main className="workspace">
            {history.length === 0 ? (
              <div className="hero-state">
                <div className="hero-badge">AI Data Analyst</div>
                <h1 className="hero-title">Ask anything about<br/>your data.</h1>
                <p className="hero-subtitle">
                  Connect your databases or upload a CSV. OmniData writes highly optimized SQL, runs the query, and visualizes the results instantly.
                </p>
                
                <div className="suggestion-grid">
                  <div className="suggestion-card" onClick={() => setQuery("What is our monthly revenue trend for this year?")}>
                    <Activity className="sugg-icon" size={24} />
                    <div className="sugg-text">Monthly revenue trend</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("Show the top 5 performing categories")}>
                    <BarChart3 className="sugg-icon" size={24} />
                    <div className="sugg-text">Top 5 categories</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("How are sales distributed across regions?")}>
                    <PieChart className="sugg-icon" size={24} />
                    <div className="sugg-text">Regional distribution</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("List the 10 most recent high-value transactions")}>
                    <Table2 className="sugg-icon" size={24} />
                    <div className="sugg-text">Recent high-value rows</div>
                  </div>
                </div>
              </div>
            ) : (
              history.map((msg, idx) => (
                <React.Fragment key={idx}>
                  {msg.role === 'user' ? (
                    <div className="msg-user">
                      <div className="msg-user-content">
                        {msg.content}
                      </div>
                    </div>
                  ) : (
                    msg.error ? (
                      <div className="widget-card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.02)' }}>
                        <div className="widget-body" style={{ color: '#FCA5A5', display: 'flex', alignItems: 'center', gap: 12, fontWeight: 500 }}>
                          <Sparkles size={24} />
                          Failed to analyze: {msg.error}
                        </div>
                      </div>
                    ) : (
                      <ResultBlock result={msg.result} />
                    )
                  )}
                </React.Fragment>
              ))
            )}
            
            {isQuerying && (
              <div className="thinking-box">
                <div className="spinner"></div>
                Generating SQL execution plan and synthesizing insights...
              </div>
            )}
            <div ref={chatEndRef} />
          </main>

          <div className="input-dock">
            <form onSubmit={handleQuery} className="input-container">
              <input 
                type="text"
                className="magic-input"
                placeholder="Ask a question..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                disabled={isQuerying}
                autoFocus
              />
              <button type="submit" className="magic-submit" disabled={isQuerying || !query.trim()}>
                <Send size={18} />
              </button>
            </form>
            <div style={{ textAlign: 'center', marginTop: 12, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Powered by Gemini 3.1 Flash. Press Enter to send.
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
