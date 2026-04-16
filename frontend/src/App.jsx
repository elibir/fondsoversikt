import { useState, useEffect } from 'react'

const API = '/api'

const SCORE_HIGH = 65
const SCORE_MID = 40

function ScoreBar({ value, max = 100 }) {
  const pct = Math.round((value / max) * 100)
  const color = value >= SCORE_HIGH ? 'var(--score-high)' : value >= SCORE_MID ? 'var(--score-mid)' : 'var(--score-low)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 5, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  )
}

function ScorePill({ label, value }) {
  const color = value >= SCORE_HIGH ? 'var(--score-high)' : value >= SCORE_MID ? 'var(--score-mid)' : 'var(--score-low)'
  const bg = value >= SCORE_HIGH ? 'rgba(93,189,122,0.1)' : value >= SCORE_MID ? 'rgba(232,169,74,0.1)' : 'rgba(224,92,92,0.1)'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: bg, border: `1px solid ${color}30`, borderRadius: 8, padding: '6px 12px', minWidth: 72 }}>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 600, color }}>{value}</span>
    </div>
  )
}

function MetricCell({ label, value, unit = '' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 500, color: value != null ? 'var(--text)' : 'var(--text-dim)' }}>
        {value != null ? `${value}${unit}` : '—'}
      </span>
    </div>
  )
}

function Badge({ text }) {
  return (
    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'var(--accent-dim)', color: 'var(--accent)', fontWeight: 500, whiteSpace: 'nowrap' }}>
      {text}
    </span>
  )
}

const FACTOR_LABELS = {
  return: 'Avkastning',
  risk: 'Risiko',
  cost: 'Kostnad',
  diversification: 'Diversifisering',
}
const CORE_FACTORS = ['return', 'risk']

function FundCard({ item, expanded, onToggle }) {
  const { rank, fund, metrics, total_score, score_breakdown, missing_factors } = item
  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${expanded ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 'var(--radius)',
        marginBottom: 10,
        overflow: 'hidden',
        transition: 'border-color 0.2s',
        cursor: 'pointer',
      }}
      onClick={onToggle}
    >
      {/* Main row */}
      <div style={{ display: 'grid', gridTemplateColumns: '44px 1fr auto auto', gap: 16, alignItems: 'center', padding: '14px 18px' }}>
        {/* Rank */}
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 20, fontFamily: 'var(--font-display)', color: rank <= 3 ? 'var(--accent)' : 'var(--text-dim)' }}>
            {rank}
          </span>
        </div>

        {/* Name + badges */}
        <div>
          <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 4 }}>{fund.fund_name}</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Badge text={fund.asset_class} />
            <Badge text={fund.category} />
          </div>
        </div>

        {/* Score */}
        <div style={{ textAlign: 'right', minWidth: 80 }}>
          <div style={{ fontSize: 24, fontFamily: 'var(--font-display)', color: total_score >= SCORE_HIGH ? 'var(--score-high)' : total_score >= SCORE_MID ? 'var(--score-mid)' : 'var(--score-low)' }}>
            {total_score}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: -2 }}>totalscore</div>
        </div>

        {/* Expand toggle */}
        <div style={{ color: 'var(--text-muted)', fontSize: 18, userSelect: 'none' }}>
          {expanded ? '↑' : '↓'}
        </div>
      </div>

      {/* Score bar preview (always visible) */}
      <div style={{ padding: '0 18px 14px', paddingLeft: 78 }}>
        <ScoreBar value={total_score} />
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '16px 18px', background: 'var(--bg-hover)' }}
          onClick={e => e.stopPropagation()}>

          {/* Score breakdown */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Scoreforklaring</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <ScorePill label="Avkastning" value={score_breakdown.return_score} />
              <ScorePill label="Risiko" value={score_breakdown.risk_score} />
              <ScorePill label="Kostnad" value={score_breakdown.cost_score} />
              <ScorePill label="Diversifisering" value={score_breakdown.diversification_score} />
            </div>
            <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.7 }}>
              {missing_factors.some(f => CORE_FACTORS.includes(f)) && <div>ℹ️ <strong>Totalscore kunne ikke beregnes</strong> – avkastning eller volatilitet mangler</div>}

              {score_breakdown.return_score >= SCORE_HIGH && <div>✅ <strong>Høy historisk avkastning</strong></div>}
              {score_breakdown.return_score != null && score_breakdown.return_score < SCORE_MID && <div>⚠️ <strong>Lav historisk avkastning</strong></div>}

              {score_breakdown.risk_score >= SCORE_HIGH && <div>✅ <strong>Lav volatilitet</strong></div>}
              {score_breakdown.risk_score != null && score_breakdown.risk_score < SCORE_MID && <div>⚠️ <strong>Høy volatilitet</strong></div>}

              {score_breakdown.cost_score >= SCORE_HIGH && <div>✅ <strong>Lav kostnad</strong></div>}
              {score_breakdown.cost_score != null && score_breakdown.cost_score < SCORE_MID && <div>⚠️ <strong>Høy kostnad</strong></div>}
              {score_breakdown.cost_score == null && <div>ℹ️ <strong>Kostnad</strong> – mangler data, ikke inkludert i score</div>}

              {score_breakdown.diversification_score >= SCORE_HIGH && <div>✅ <strong>Bred diversifisering</strong></div>}
              {score_breakdown.diversification_score != null && score_breakdown.diversification_score < SCORE_MID && <div>⚠️ <strong>Konsentrert portefølje</strong></div>}
              {score_breakdown.diversification_score == null && <div>ℹ️ <strong>Diversifisering</strong> – mangler data, ikke inkludert i score</div>}
            </div>
          </div>

          {/* Metrics */}
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Nøkkeltall</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 }}>
            <MetricCell label="Avkastning YTD" value={metrics.ytd_return_pct} unit="%" />
            <MetricCell label="Avkastning 1 år" value={metrics.return_1y_pct} unit="%" />
            <MetricCell label="Avkastning 3 år" value={metrics.return_3y_ann_pct} unit="%" />
            <MetricCell label="Volatilitet 1 år" value={metrics.volatility_1y_pct} unit="%" />
            <MetricCell label="Maks drawdown" value={metrics.max_drawdown_1y_pct} unit="%" />
            <MetricCell label="Forvaltningsgebyr" value={metrics.expense_ratio_pct} unit="%" />
            <MetricCell label="AUM (mrd. USD)" value={metrics.aum_usd_bn} />
            <MetricCell label="Direkteavkastning" value={metrics.dividend_yield_pct} unit="%" />
            <MetricCell label="Sharpe ratio (1 år)" value={metrics.sharpe_ratio_1y} />
          </div>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [funds, setFunds] = useState([])
  const [filters, setFilters] = useState({ asset_classes: [], categories: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(null)

  const [assetClass, setAssetClass] = useState('')
  const [category, setCategory] = useState('')
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    fetch(`${API}/filters`)
      .then(r => r.json())
      .then(setFilters)
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (assetClass) params.set('asset_class', assetClass)
    if (category) params.set('category', category)
    if (sortBy) params.set('sort_by', sortBy)
    params.set('sort_dir', sortDir)

    fetch(`${API}/funds?${params}`)
      .then(r => r.json())
      .then(data => { setFunds(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [assetClass, category, sortBy, sortDir])

  const selectStyle = {
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    color: 'var(--text)',
    borderRadius: 6,
    padding: '6px 10px',
    fontSize: 13,
    cursor: 'pointer',
    outline: 'none',
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '32px 20px' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 6 }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 400, color: 'var(--text)' }}>
            Fondsoversikt
          </h1>
          <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 500 }}>for kapitalforvaltere</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Rangert etter samlet score basert på historisk avkastning, risiko og kostnad.
        </p>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20, alignItems: 'center' }}>
        <select style={selectStyle} value={assetClass} onChange={e => setAssetClass(e.target.value)}>
          <option value="">Alle aktivaklasser</option>
          {filters.asset_classes.map(ac => <option key={ac} value={ac}>{ac}</option>)}
        </select>

        <select style={selectStyle} value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">Alle kategorier</option>
          {filters.categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <select style={selectStyle} value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option value="">Sorter etter: Score</option>
          <option value="return">Avkastning</option>
          <option value="risk">Risiko</option>
          <option value="cost">Kostnad</option>
          <option value="diversification">Diversifisering</option>
          <option value="name">Navn</option>
        </select>

        <button
          style={{ ...selectStyle, background: sortDir === 'asc' ? 'var(--accent-dim)' : 'var(--bg-card)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
          onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
        >
          {sortDir === 'desc' ? '↓ Synkende' : '↑ Stigende'}
        </button>

        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
          {funds.length} fond
        </span>
      </div>

      {/* Fund list */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>Laster fond…</div>
      )}
      {error && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--danger)' }}>
          Klarte ikke å laste data. Er backenden kjørende på port 8000?
        </div>
      )}
      {!loading && !error && funds.map(item => (
        <FundCard
          key={item.fund.ticker}
          item={item}
          expanded={expanded === item.fund.ticker}
          onToggle={() => setExpanded(prev => prev === item.fund.ticker ? null : item.fund.ticker)}
        />
      ))}
    </div>
  )
}
