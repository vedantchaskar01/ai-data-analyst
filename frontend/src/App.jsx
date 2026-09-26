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

const API_BASE = 'https://ai-data-analyst-do3u.onrender.com/api';
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
  const [activeResult, setActiveResult] = useState(null);
  
  const chatEndRef = useRef(null);
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

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const currentQuery = query.trim();
    setQuery('');
    
    setHistory(prev => [...prev, { role: 'user', content: currentQuery }]);
    setIsQuerying(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, { query: currentQuery });
      const newMsg = { 
        role: 'assistant', 
        result: res.data,
        question: currentQuery,
        id: Date.now()
      };
      setHistory(prev => [...prev, newMsg]);
      setActiveResult(res.data);
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


        <div className="chat-panel" style={{ width: '400px', display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.2)' }}>
          <div className="brand-header" style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} color="var(--accent-cyan)" />
            <span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'Outfit', color: '#fff' }}>Vedzzinsights</span>
          </div>
          <main className="workspace" style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
            {history.map((msg, idx) => (
              <React.Fragment key={idx}>
                {msg.role === 'user' ? (
                  <div className="msg-user" style={{ maxWidth: '100%', marginBottom: '16px', textAlign: 'right' }}>
                    <div className="msg-user-content" style={{ display: 'inline-block', fontSize: '1rem', padding: '12px 16px', borderRadius: '16px 16px 4px 16px', background: 'var(--accent-blue)' }}>
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  msg.error ? (
                    <div className="msg-assistant" style={{ maxWidth: '100%', marginBottom: '16px' }}>
                      <div className="msg-assistant-content" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', padding: '12px 16px', borderRadius: '16px 16px 16px 4px', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#FCA5A5' }}>
                        <Sparkles size={16} /> Failed: {msg.error}
                      </div>
                    </div>
                  ) : (
                    <div className="msg-assistant" style={{ maxWidth: '100%', marginBottom: '16px', cursor: 'pointer' }} onClick={() => setActiveResult(msg.result)}>
                      <div className="msg-assistant-content" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', padding: '12px 16px', borderRadius: '16px 16px 16px 4px', background: 'rgba(10, 10, 11, 0.6)', border: '1px solid var(--border-subtle)', backdropFilter: 'blur(12px)', transition: 'all 0.2s', boxShadow: msg.result === activeResult ? '0 0 0 1px var(--accent-cyan)' : 'none' }}>
                        <Sparkles size={16} color="var(--accent-cyan)" /> 
                        {msg.result.analysis?.insight ? (msg.result.analysis.insight.length > 30 ? msg.result.analysis.insight.substring(0,30) + '...' : msg.result.analysis.insight) : "Query complete"}
                      </div>
                    </div>
                  )
                )}
              </React.Fragment>
            ))}
            
            {isQuerying && (
              <div className="thinking-box" style={{ fontSize: '0.85rem' }}>
                <div className="spinner"></div>
                Analyzing data...
              </div>
            )}
            <div ref={chatEndRef} />
          </main>

          <div className="input-dock" style={{ padding: '20px', position: 'relative', background: 'transparent' }}>
            <form onSubmit={handleQuery} className="input-container" style={{ borderRadius: '12px', padding: 0 }}>
              <input 
                type="text"
                className="magic-input"
                placeholder="Ask..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                disabled={isQuerying}
                autoFocus
                style={{ padding: '16px', fontSize: '0.95rem' }}
              />
              <button type="submit" className="magic-submit" disabled={isQuerying || !query.trim()} style={{ width: '36px', height: '36px', right: '8px', bottom: '8px', borderRadius: '10px' }}>
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>

        <div className="preview-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px', overflowY: 'auto', position: 'relative' }}>
          {activeResult ? (
            <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '40px' }}>
              <ResultBlock key={activeResult.sql || Date.now()} result={activeResult} />
              <div style={{ width: '100%' }}>
                <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '16px', fontFamily: 'Outfit' }}>More questions to try:</h3>
                <div className="suggestion-grid">
                  <div className="suggestion-card" onClick={() => setQuery("Show the total revenue trend by date.")}>
                    <Activity className="sugg-icon" size={24} />
                    <div className="sugg-text">Analyze revenue trends</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("Compare the total sales across our top 5 performing product categories.")}>
                    <BarChart3 className="sugg-icon" size={24} />
                    <div className="sugg-text">Compare product sales</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("What is the percentage breakdown of our total revenue by region?")}>
                    <LayoutDashboard className="sugg-icon" size={24} />
                    <div className="sugg-text">View regional breakdown</div>
                  </div>
                  <div className="suggestion-card" onClick={() => setQuery("Calculate the total sum of all revenue.")}>
                    <Sparkles className="sugg-icon" size={24} />
                    <div className="sugg-text">Calculate total revenue</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="hero-state">
              <div className="hero-badge">Vedzzinsights</div>
              <h1 className="hero-title">Turning raw data into<br/>instant clarity.</h1>
              <p className="hero-subtitle">
                Stop writing complex SQL. Just chat with your database in plain English and let Vedzzinsights generate accurate, interactive visualizations on the fly.
              </p>
              
              <div className="suggestion-grid">
                <div className="suggestion-card" onClick={() => setQuery("Show the total revenue trend by date.")}>
                  <Activity className="sugg-icon" size={24} />
                  <div className="sugg-text">Analyze revenue trends</div>
                </div>
                <div className="suggestion-card" onClick={() => setQuery("Compare the total sales across our top 5 performing product categories.")}>
                  <BarChart3 className="sugg-icon" size={24} />
                  <div className="sugg-text">Compare product sales</div>
                </div>
                <div className="suggestion-card" onClick={() => setQuery("What is the percentage breakdown of our total revenue by region?")}>
                  <LayoutDashboard className="sugg-icon" size={24} />
                  <div className="sugg-text">View regional breakdown</div>
                </div>
                <div className="suggestion-card" onClick={() => setQuery("Calculate the total sum of all revenue.")}>
                  <Sparkles className="sugg-icon" size={24} />
                  <div className="sugg-text">Calculate total revenue</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;
