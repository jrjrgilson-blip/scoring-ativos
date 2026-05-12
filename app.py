import { useState, useEffect } from "react";
import { Area, AreaChart, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const C = {
  bg: "#0a0d12", surface: "#111620", border: "#1e2736",
  accent: "#00d4ff", green: "#00e676", yellow: "#ffca28", red: "#ff5252",
  text: "#c8d8e8", muted: "#4a6080"
};
const mono = "'IBM Plex Mono', monospace";
const sans = "'IBM Plex Sans', sans-serif";

function ScoreBar({ value, max, color = C.accent, height = 6 }) {
  const [w, setW] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setW((value / max) * 100), 200);
    return () => clearTimeout(t);
  }, [value, max]);
  return (
    <div style={{ background: C.border, borderRadius: 4, height, overflow: "hidden" }}>
      <div style={{ width: `${w}%`, height: "100%", background: color, borderRadius: 4, transition: "width 1s ease" }} />
    </div>
  );
}

function extrairJSON(txt) {
  const ini = txt.indexOf("{");
  const fim = txt.lastIndexOf("}");
  if (ini === -1 || fim === -1) throw new Error("JSON não encontrado na resposta");
  return JSON.parse(txt.slice(ini, fim + 1));
}

export default function App() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function analisar() {
    const t = ticker.trim().toUpperCase();
    if (!t) return;
    setLoading(true); setError(""); setData(null);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1500,
          system: "Você é um analista de ações brasileiro. Responda SOMENTE com JSON válido, sem nenhum texto antes ou depois, sem markdown, sem blocos de código.",
          messages: [{
            role: "user",
            content: `Analise o ativo ${t} listado na B3 e retorne este JSON preenchido com dados reais ou plausíveis:
{"ticker":"${t}","empresa":"Nome","cotacao_atual":0.0,"variacao_pct":0.0,"pl_ratio":0.0,"roe_pct":0.0,"pvp":0.0,"historico_12m":[0,0,0,0,0,0,0,0,0,0,0,0],"meses_labels":["Jun/24","Jul/24","Ago/24","Set/24","Out/24","Nov/24","Dez/24","Jan/25","Fev/25","Mar/25","Abr/25","Mai/25"],"score_tecnico":{"total":0,"criterios":[{"nome":"Preço vs MM21","pontos":0,"max":15,"positivo":false,"descricao":""},{"nome":"Inclinação MM21","pontos":0,"max":15,"positivo":false,"descricao":""},{"nome":"Canal Donchian","pontos":0,"max":15,"positivo":false,"descricao":""},{"nome":"Volume vs Média","pontos":0,"max":15,"positivo":false,"descricao":""}]},"score_fundamentalista":{"total":0,"criterios":[{"nome":"P/L","pontos":0,"max":15,"positivo":false,"descricao":""},{"nome":"ROE","pontos":0,"max":15,"positivo":false,"descricao":""},{"nome":"P/VP","pontos":0,"max":10,"positivo":false,"descricao":""}]},"score_final":0,"status":"NEUTRA","narrativa":""}
Regras: status=COMPRA se >=75, NEUTRA se >=45, VENDA se <45. Retorne APENAS o JSON.`
          }]
        })
      });
      const raw = await res.json();
      if (!res.ok) throw new Error(raw.error?.message || `Erro ${res.status}`);
      const txt = (raw.content || []).map(b => b.text || "").join("");
      setData(extrairJSON(txt));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const sf = data?.score_final || 0;
  const statusColor = sf >= 75 ? C.green : sf >= 45 ? C.yellow : C.red;
  const badgeBg = sf >= 75 ? "rgba(0,230,118,0.12)" : sf >= 45 ? "rgba(255,202,40,0.12)" : "rgba(255,82,82,0.12)";
  const badgeBorder = sf >= 75 ? "rgba(0,230,118,0.3)" : sf >= 45 ? "rgba(255,202,40,0.3)" : "rgba(255,82,82,0.3)";
  const chartData = data ? data.historico_12m.map((v, i) => ({ mes: (data.meses_labels || [])[i] || `M${i+1}`, preco: v })) : [];
  const chartColor = data && data.historico_12m[11] >= data.historico_12m[0] ? C.green : C.red;

  const card = (children, mb = 16) => (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 18, marginBottom: mb }}>
      {children}
    </div>
  );
  const cardTitle = (t) => (
    <div style={{ fontFamily: mono, fontSize: 10, color: C.muted, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>{t}</div>
  );

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: sans, color: C.text }}>

      {/* HEADER */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "14px 18px", display: "flex", alignItems: "center", gap: 12, position: "sticky", top: 0, zIndex: 10 }}>
        <span style={{ fontSize: 20 }}>📊</span>
        <div>
          <div style={{ fontFamily: mono, fontSize: 14, fontWeight: 700, color: C.accent, letterSpacing: "0.06em" }}>SCORING DE ATIVOS</div>
          <div style={{ fontFamily: mono, fontSize: 10, color: C.muted, marginTop: 2 }}>Técnico 60% · Fundamentalista 40%</div>
        </div>
      </div>

      <div style={{ padding: "18px 16px", maxWidth: 600, margin: "0 auto" }}>

        {/* INPUT */}
        {card(<>
          <div style={{ fontFamily: mono, fontSize: 10, color: C.muted, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>Ticker do Ativo</div>
          <div style={{ display: "flex", gap: 10 }}>
            <input
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === "Enter" && !loading && analisar()}
              placeholder="Ex: PETR4, VALE3..."
              maxLength={10}
              style={{ flex: 1, background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: "11px 14px", fontFamily: mono, fontSize: 20, fontWeight: 700, color: C.accent, letterSpacing: "0.1em", outline: "none" }}
            />
            <button onClick={analisar} disabled={loading}
              style={{ background: loading ? C.muted : C.accent, color: "#000", border: "none", borderRadius: 6, padding: "11px 18px", fontFamily: mono, fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", cursor: loading ? "not-allowed" : "pointer", whiteSpace: "nowrap" }}>
              {loading ? "..." : "ANALISAR"}
            </button>
          </div>
          <div style={{ fontFamily: mono, fontSize: 10, color: C.muted, marginTop: 8 }}>B3 · Ex: ITUB4, BBAS3, WEGE3, VALE3, PETR4</div>
        </>, 18)}

        {/* SPINNER */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, padding: "40px 0" }}>
            <div style={{ width: 34, height: 34, border: `3px solid ${C.border}`, borderTop: `3px solid ${C.accent}`, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
            <div style={{ fontFamily: mono, fontSize: 12, color: C.muted }}>Calculando score...</div>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {/* ERRO */}
        {error && (
          <div style={{ background: "rgba(255,82,82,0.08)", border: `1px solid rgba(255,82,82,0.3)`, borderRadius: 10, padding: 16, marginBottom: 16, fontFamily: mono, fontSize: 12, color: C.red }}>
            ⚠️ {error}
          </div>
        )}

        {/* RESULTADO */}
        {data && (<>

          {/* Ticker Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
            <div>
              <div style={{ fontFamily: mono, fontSize: 26, fontWeight: 700, color: "#fff", letterSpacing: "0.06em" }}>{data.ticker}</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>{data.empresa}</div>
            </div>
            <div style={{ background: badgeBg, border: `1px solid ${badgeBorder}`, borderRadius: 20, padding: "6px 16px", fontFamily: mono, fontSize: 13, fontWeight: 700, color: statusColor, letterSpacing: "0.1em" }}>
              {data.status}
            </div>
          </div>

          {/* Métricas */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 16 }}>
            {[
              { label: "Cotação", value: `R$${(data.cotacao_atual||0).toFixed(2)}`, sub: `${(data.variacao_pct||0)>=0?"+":""}${(data.variacao_pct||0).toFixed(2)}%`, subColor: (data.variacao_pct||0)>=0 ? C.green : C.red, valColor: C.text },
              { label: "P/L", value: (data.pl_ratio||0)>0 ? `${(data.pl_ratio).toFixed(1)}x` : "N/D", sub: "Preço/Lucro", subColor: C.muted, valColor: data.pl_ratio>0&&data.pl_ratio<20 ? C.green : data.pl_ratio>=20 ? C.red : C.text },
              { label: "ROE", value: (data.roe_pct||0)>0 ? `${(data.roe_pct).toFixed(1)}%` : "N/D", sub: "Ret. s/ Equity", subColor: C.muted, valColor: data.roe_pct>10 ? C.green : C.text }
            ].map((m, i) => (
              <div key={i} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 12, textAlign: "center" }}>
                <div style={{ fontFamily: mono, fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>{m.label}</div>
                <div style={{ fontFamily: mono, fontSize: 16, fontWeight: 700, color: m.valColor }}>{m.value}</div>
                <div style={{ fontSize: 10, color: m.subColor, marginTop: 3, fontFamily: mono }}>{m.sub}</div>
              </div>
            ))}
          </div>

          {/* Score */}
          {card(<>
            {cardTitle("Pontuação Final")}
            <div style={{ fontFamily: mono, fontSize: 42, fontWeight: 700, textAlign: "center", color: statusColor, marginBottom: 4 }}>{sf}</div>
            <div style={{ fontFamily: mono, fontSize: 11, color: C.muted, textAlign: "center", marginBottom: 14 }}>de 100 pontos</div>
            <ScoreBar value={sf} max={100} color={statusColor} height={8} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 14 }}>
              {[
                { name: "📈 TÉCNICO", pts: data.score_tecnico?.total||0, max: 60 },
                { name: "🏢 FUNDAMENTOS", pts: data.score_fundamentalista?.total||0, max: 40 }
              ].map((b, i) => (
                <div key={i} style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div style={{ fontFamily: mono, fontSize: 9, color: C.muted }}>{b.name}</div>
                    <div style={{ fontFamily: mono, fontSize: 16, fontWeight: 700, color: C.accent }}>{b.pts}<span style={{ fontSize: 10, color: C.muted }}>/{b.max}</span></div>
                  </div>
                  <ScoreBar value={b.pts} max={b.max} height={4} />
                </div>
              ))}
            </div>
          </>)}

          {/* Critérios */}
          {card(<>
            {cardTitle("Detalhamento dos Critérios")}
            {[
              { title: "📈 Análise Técnica", items: data.score_tecnico?.criterios||[] },
              { title: "🏢 Análise Fundamentalista", items: data.score_fundamentalista?.criterios||[] }
            ].map((sec, si) => (
              <div key={si} style={{ marginBottom: si===0 ? 14 : 0 }}>
                <div style={{ fontFamily: mono, fontSize: 11, color: C.accent, marginBottom: 8 }}>{sec.title}</div>
                {sec.items.map((c, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "8px 0", borderBottom: i<sec.items.length-1 ? `1px solid ${C.border}` : "none", fontSize: 12, lineHeight: 1.4 }}>
                    <span style={{ flexShrink: 0 }}>{c.positivo ? "✅" : "❌"}</span>
                    <span>
                      <strong style={{ color: "#fff" }}>{c.nome}</strong>
                      <span style={{ color: C.muted }}> — {c.descricao}</span>
                      <span style={{ fontFamily: mono, fontSize: 10, color: c.positivo ? C.green : C.muted, marginLeft: 4 }}>+{c.pontos}/{c.max}pts</span>
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </>)}

          {/* Gráfico */}
          {card(<>
            {cardTitle("Evolução do Preço — 12 meses")}
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColor} stopOpacity={0.2} />
                    <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="mes" tick={{ fill: C.muted, fontSize: 9, fontFamily: mono }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: C.muted, fontSize: 9, fontFamily: mono }} tickLine={false} axisLine={false} tickFormatter={v => `R$${v}`} />
                <Tooltip
                  contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, fontFamily: mono, fontSize: 11 }}
                  labelStyle={{ color: C.text }} itemStyle={{ color: C.accent }}
                  formatter={v => [`R$ ${Number(v).toFixed(2)}`, "Preço"]}
                />
                <Area type="monotone" dataKey="preco" stroke={chartColor} strokeWidth={2} fill="url(#grad)" dot={{ r: 3, fill: chartColor }} />
              </AreaChart>
            </ResponsiveContainer>
          </>)}

          {/* Narrativa */}
          {card(<>
            {cardTitle("Análise do Assistente")}
            <div style={{ fontSize: 13, lineHeight: 1.7, color: C.text }}>{data.narrativa}</div>
          </>, 20)}

        </>)}

        <div style={{ textAlign: "center", fontFamily: mono, fontSize: 10, color: C.muted, paddingBottom: 30, lineHeight: 1.7 }}>
          Modelo educacional · Não constitui recomendação de investimento
        </div>
      </div>
    </div>
  );
}
