import { useState, useMemo } from 'react';
import { Search, Music, TrendingUp, AlertCircle, Database } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './index.css';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      // In dev, use Vite proxy or full URL. We'll assume the API runs on port 8000
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000/api/query' : '/api/query';
      
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: "Failed to connect to the server." });
    } finally {
      setLoading(false);
    }
  };

  const renderTable = (data) => {
    if (!data || data.length === 0) return <p>No results found.</p>;
    const columns = Object.keys(data[0]);
    
    return (
      <div className="table-container">
        <table>
          <thead>
            <tr>
              {columns.map(col => <th key={col}>{col.replace(/_/g, ' ').toUpperCase()}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr key={i}>
                {columns.map(col => <td key={col}>{row[col]}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 50 && <p style={{ color: '#94a3b8', marginTop: '1rem', textAlign: 'center' }}>Showing first 50 results</p>}
      </div>
    );
  };

  const chartData = useMemo(() => {
    if (!result?.history) return null;
    const history = result.history;
    const processed = [];
    for (let i = 0; i < history.length; i++) {
      processed.push(history[i]);
      if (i < history.length - 1) {
        const currentDate = new Date(history[i].from_date);
        const nextDate = new Date(history[i + 1].from_date);
        const diffDays = Math.ceil(Math.abs(nextDate - currentDate) / (1000 * 60 * 60 * 24));
        
        // If gap is more than 10 days, insert a null point to break the line
        if (diffDays > 10) {
          processed.push({
            from_date: `gap-${i}`, // unique key that won't show a real date
            position: null
          });
        }
      }
    }
    return processed;
  }, [result?.history]);

  // Custom tick formatter to hide the gap labels
  const formatXAxis = (tickItem) => {
    if (typeof tickItem === 'string' && tickItem.startsWith('gap-')) return '';
    return tickItem;
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Music Chart Explorer</h1>
        <p>Ask anything about UK Singles Chart history using natural language</p>
      </header>

      <form onSubmit={handleSearch} className="search-container">
        <Search className="search-icon" size={24} />
        <input 
          type="text" 
          className="search-input"
          placeholder="e.g., 'What are the top 5 longest running number ones?'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="search-button" disabled={loading || !query.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {result?.error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{result.error}</span>
        </div>
      )}

      {result?.data && (
        <div className="results-grid">
          <div className="main-content">
            <div className="card glass-panel" style={{ marginBottom: '2rem' }}>
              <h2 className="card-title"><Database size={20} /> Query Results</h2>
              {renderTable(result.data)}
            </div>

            {chartData && (
              <div className="card glass-panel">
                <h2 className="card-title"><TrendingUp size={20} /> Chart History</h2>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e3dccf" />
                      <XAxis dataKey="from_date" stroke="#8c7d70" tickFormatter={formatXAxis} />
                      <YAxis reversed stroke="#8c7d70" domain={[1, 100]} />
                      <Tooltip 
                        contentStyle={{ background: '#fdfbf7', border: '1px solid #e3dccf', borderRadius: '8px', color: '#4a3b32', fontFamily: "'Outfit', sans-serif", boxShadow: '0 4px 15px rgba(74, 59, 50, 0.05)' }}
                        labelFormatter={formatXAxis}
                      />
                      <Line type="monotone" dataKey="position" stroke="#d97757" strokeWidth={3} dot={{ r: 4, fill: '#fdfbf7', stroke: '#d97757', strokeWidth: 2 }} activeDot={{ r: 6, fill: '#d97757', stroke: '#fdfbf7' }} connectNulls={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          <div className="sidebar">
            {result.metrics && (
              <div className="card glass-panel" style={{ marginBottom: '2rem' }}>
                <h2 className="card-title"><Music size={20} /> Song Details</h2>
                <div className="metrics-grid">
                  <div className="metric-box">
                    <div className="metric-value">#{result.metrics.peak}</div>
                    <div className="metric-label">Peak Position</div>
                  </div>
                  <div className="metric-box">
                    <div className="metric-value">{result.metrics.weeks}</div>
                    <div className="metric-label">Weeks on Chart</div>
                  </div>
                </div>
                <div className="metric-box" style={{ gridColumn: 'span 2' }}>
                  <div className="metric-value" style={{ fontSize: '1.25rem' }}>{result.metrics.debut}</div>
                  <div className="metric-label">Debut Date</div>
                </div>
              </div>
            )}

            {result.artwork_url && (
              <div className="card glass-panel">
                <h2 className="card-title">Album Artwork</h2>
                <div className="artwork-container">
                  <img src={result.artwork_url} alt="Album Art" className="artwork-img" />
                </div>
              </div>
            )}
            
            {result.sql && (
              <div className="card glass-panel" style={{ marginTop: '2rem' }}>
                <h2 className="card-title">Generated SQL</h2>
                <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', overflowX: 'auto', fontSize: '0.875rem', color: '#60a5fa' }}>
                  <code>{result.sql}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
