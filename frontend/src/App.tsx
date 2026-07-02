import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  BookOpen,
  Check,
  ChevronDown,
  CircleDollarSign,
  Download,
  ExternalLink,
  FileCheck2,
  Globe2,
  Languages,
  LoaderCircle,
  Moon,
  Scale,
  Search,
  Share2,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Users,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  analyzeAsset,
  type DataSourceConfig,
  type MarketDataProvider,
  searchAssets,
} from "./api";
import { type Language, useCopy } from "./i18n";
import type {
  AgentResult,
  AnalysisReport,
  FinancialPeriod,
  SearchResult,
  ValuationScenario,
} from "./types";

type Theme = "light" | "dark";
type SectionIcon = typeof BookOpen;
type StoredDataSource = DataSourceConfig & { saved: boolean };

const quickSymbols = [
  "AAPL",
  "MU",
  "AAOI",
  "600519.SS",
  "0700.HK",
  "7203.T",
  "SAP",
];

const providers: { value: MarketDataProvider; label: string }[] = [
  { value: "fixture", label: "Fixture demo" },
  { value: "twelvedata", label: "Twelve Data" },
  { value: "finnhub", label: "Finnhub" },
];

function loadDataSource(): StoredDataSource {
  return {
    provider:
      (localStorage.getItem("gec.marketDataProvider") as MarketDataProvider) ??
      "fixture",
    apiKey: localStorage.getItem("gec.marketDataApiKey") ?? "",
    saved: true,
  };
}

function formatNumber(value: number, maximumFractionDigits = 1) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(
    value,
  );
}

function formatDate(value: string, language: Language) {
  return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export function App() {
  const [language, setLanguage] = useState<Language>("zh");
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light",
  );
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState<SearchResult | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [searching, setSearching] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [shareOpen, setShareOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [dataSource, setDataSource] =
    useState<StoredDataSource>(loadDataSource);
  const initialized = useRef(false);
  const t = useCopy(language);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  }, [theme, language]);

  const runAnalysis = useCallback(
    async (asset: SearchResult, currency = baseCurrency) => {
      setSelected(asset);
      setQuery(asset.asset.provider_symbols.yahoo ?? asset.asset.symbol);
      setSearchOpen(false);
      setAnalyzing(true);
      setError("");
      try {
        const next = await analyzeAsset(
          asset.asset_id,
          currency,
          language === "zh" ? "zh-CN" : "en-US",
          {
            provider: dataSource.provider,
            apiKey: dataSource.apiKey,
          },
        );
        setReport(next);
        window.history.replaceState(
          null,
          "",
          `?asset=${encodeURIComponent(asset.asset_id)}`,
        );
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unknown error");
      } finally {
        setAnalyzing(false);
      }
    },
    [baseCurrency, dataSource.apiKey, dataSource.provider, language],
  );

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    const preferred = new URLSearchParams(window.location.search).get("asset");
    const initialQuery = preferred?.split(":")[1] ?? "AAPL";
    searchAssets(initialQuery)
      .then((items) => {
        const asset = preferred
          ? items.find((item) => item.asset_id === preferred)
          : items.find((item) => item.asset_id === "XNAS:AAPL");
        if (asset) void runAnalysis(asset);
      })
      .catch((caught: unknown) => {
        setError(
          caught instanceof Error ? caught.message : "Unable to load demo",
        );
      });
  }, [runAnalysis]);

  useEffect(() => {
    if (
      !query.trim() ||
      selected?.asset.provider_symbols.yahoo === query.trim()
    ) {
      setResults([]);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setSearching(true);
      try {
        const items = await searchAssets(query, controller.signal);
        setResults(items);
        setSearchOpen(true);
      } catch (caught) {
        if (!(caught instanceof DOMException && caught.name === "AbortError")) {
          setError(caught instanceof Error ? caught.message : "Search failed");
        }
      } finally {
        setSearching(false);
      }
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query, selected]);

  const selectQuick = async (symbol: string) => {
    setQuery(symbol);
    setSelected(null);
    setSearching(true);
    try {
      const items = await searchAssets(symbol);
      setResults(items);
      if (items.length === 1) {
        await runAnalysis(items[0]);
      } else {
        setSearchOpen(true);
      }
    } finally {
      setSearching(false);
    }
  };

  const runQuery = async () => {
    if (selected) {
      await runAnalysis(selected);
      return;
    }
    const trimmed = query.trim();
    if (!trimmed) return;
    setSearching(true);
    setError("");
    try {
      const items = await searchAssets(trimmed);
      setResults(items);
      if (items.length === 1) {
        await runAnalysis(items[0]);
      } else if (items.length > 1) {
        setSearchOpen(true);
      } else {
        setSearchOpen(true);
        setError(t.noSearchResults);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

  const changeCurrency = async (currency: string) => {
    setBaseCurrency(currency);
    if (selected) await runAnalysis(selected, currency);
  };

  const saveDataSource = () => {
    localStorage.setItem("gec.marketDataProvider", dataSource.provider);
    localStorage.setItem("gec.marketDataApiKey", dataSource.apiKey);
    setDataSource((current) => ({ ...current, saved: true }));
    if (selected) void runAnalysis(selected);
  };

  return (
    <div className="app-shell">
      <Header
        language={language}
        theme={theme}
        onLanguage={() => setLanguage(language === "zh" ? "en" : "zh")}
        onTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      />
      <main id="main">
        <section className="hero">
          <div className="hero-grid">
            <div className="hero-copy">
              <div className="eyebrow">
                <span className="live-dot" aria-hidden="true" />
                {t.demoNotice}
              </div>
              <h1>
                {language === "zh" ? (
                  <>
                    让观点交锋，
                    <br />让<span>证据</span>定锚。
                  </>
                ) : (
                  <>
                    Let viewpoints collide.
                    <br />
                    Let <span>evidence</span> anchor.
                  </>
                )}
              </h1>
              <p>{t.strapline}</p>
            </div>
            <CouncilOrb analyzing={analyzing} score={report?.consensus_score} />
          </div>
          <div className="search-panel">
            <label htmlFor="asset-search">{t.searchLabel}</label>
            <div className="search-row">
              <div className="search-field">
                <Search size={20} aria-hidden="true" />
                <input
                  id="asset-search"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setSelected(null);
                  }}
                  onFocus={() => results.length && setSearchOpen(true)}
                  placeholder={t.searchPlaceholder}
                  autoComplete="off"
                />
                {searching && (
                  <LoaderCircle
                    className="spin"
                    size={18}
                    aria-label="Searching"
                  />
                )}
              </div>
              <button
                className="primary-button"
                disabled={!query.trim() || searching || analyzing}
                onClick={() => void runQuery()}
              >
                {analyzing ? (
                  <LoaderCircle className="spin" size={18} />
                ) : (
                  <Sparkles size={18} />
                )}
                {analyzing ? t.analyzing : t.analyze}
              </button>
            </div>
            <div className="data-source-bar">
              <button
                type="button"
                className="link-button"
                onClick={() => setSettingsOpen((open) => !open)}
              >
                <SlidersHorizontal size={16} />
                {t.dataSource}:{" "}
                {providers.find((item) => item.value === dataSource.provider)
                  ?.label ?? dataSource.provider}
              </button>
              <span>
                {dataSource.provider === "fixture"
                  ? t.fixtureMode
                  : dataSource.apiKey.trim()
                    ? t.apiKeyLocal
                    : t.apiKeyMissing}
              </span>
            </div>
            {settingsOpen && (
              <div className="data-source-panel">
                <label>
                  {t.provider}
                  <select
                    value={dataSource.provider}
                    onChange={(event) =>
                      setDataSource({
                        ...dataSource,
                        provider: event.target.value as MarketDataProvider,
                        saved: false,
                      })
                    }
                  >
                    {providers.map((provider) => (
                      <option key={provider.value} value={provider.value}>
                        {provider.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {t.apiKey}
                  <input
                    type="password"
                    value={dataSource.apiKey}
                    onChange={(event) =>
                      setDataSource({
                        ...dataSource,
                        apiKey: event.target.value,
                        saved: false,
                      })
                    }
                    disabled={dataSource.provider === "fixture"}
                    placeholder={t.apiKeyPlaceholder}
                    autoComplete="off"
                  />
                </label>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={saveDataSource}
                >
                  <Check size={16} />
                  {t.saveSettings}
                </button>
                <p>{t.apiKeyHelp}</p>
              </div>
            )}
            {searchOpen && (
              <SearchResults
                results={results}
                language={language}
                onSelect={(asset) => void runAnalysis(asset)}
                onClose={() => setSearchOpen(false)}
              />
            )}
            <div className="quick-list" aria-label="Example securities">
              {quickSymbols.map((symbol) => (
                <button key={symbol} onClick={() => void selectQuick(symbol)}>
                  {symbol}
                </button>
              ))}
            </div>
          </div>
        </section>

        {error && (
          <div className="error-banner" role="alert">
            <AlertTriangle size={20} />
            <div>
              <strong>{t.errorTitle}</strong>
              <span>{error}</span>
            </div>
            <button onClick={() => selected && void runAnalysis(selected)}>
              {t.retry}
            </button>
          </div>
        )}

        {analyzing && !report ? <ReportSkeleton /> : null}
        {report ? (
          <ReportView
            report={report}
            language={language}
            baseCurrency={baseCurrency}
            onCurrency={changeCurrency}
            onShare={() => setShareOpen(true)}
          />
        ) : null}
      </main>
      <footer>
        <span>GEC / {new Date().getFullYear()}</span>
        <span>{t.footer}</span>
        <a href="/api/docs">API</a>
      </footer>
      {shareOpen && report && (
        <ShareDialog
          report={report}
          language={language}
          onClose={() => setShareOpen(false)}
        />
      )}
    </div>
  );
}

function Header({
  language,
  theme,
  onLanguage,
  onTheme,
}: {
  language: Language;
  theme: Theme;
  onLanguage: () => void;
  onTheme: () => void;
}) {
  const t = useCopy(language);
  return (
    <header className="topbar">
      <a className="brand" href="/" aria-label="Global Equity Council home">
        <span className="brand-mark">
          <Scale size={20} />
        </span>
        <span>
          <strong>GLOBAL EQUITY</strong>
          <small>COUNCIL</small>
        </span>
      </a>
      <nav aria-label="Display settings">
        <button onClick={onLanguage} aria-label={t.language} title={t.language}>
          <Languages size={18} />
          <span>{language === "zh" ? "EN" : "中"}</span>
        </button>
        <button
          onClick={onTheme}
          aria-label={theme === "dark" ? t.light : t.dark}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </nav>
    </header>
  );
}

function CouncilOrb({
  analyzing,
  score,
}: {
  analyzing: boolean;
  score?: number;
}) {
  return (
    <div
      className={`council-orb ${analyzing ? "is-analyzing" : ""}`}
      aria-hidden="true"
    >
      <div className="orbit orbit-one">
        <span />
        <span />
        <span />
      </div>
      <div className="orbit orbit-two">
        <span />
        <span />
        <span />
      </div>
      <div className="orb-center">
        <Users size={25} />
        <strong>{score ?? 6}</strong>
        <small>{score ? "SCORE" : "VOICES"}</small>
      </div>
    </div>
  );
}

function SearchResults({
  results,
  language,
  onSelect,
  onClose,
}: {
  results: SearchResult[];
  language: Language;
  onSelect: (result: SearchResult) => void;
  onClose: () => void;
}) {
  const t = useCopy(language);
  return (
    <div className="search-results" role="dialog" aria-label={t.chooseListing}>
      <div className="results-heading">
        <span>
          {results.length > 1 ? t.chooseListing : `${results.length} result`}
        </span>
        <button onClick={onClose} aria-label={t.close}>
          <X size={18} />
        </button>
      </div>
      {results.length === 0 ? (
        <p className="empty-state">{t.noSearchResults}</p>
      ) : (
        results.map((result) => (
          <button
            className="result-item"
            key={result.asset_id}
            onClick={() => onSelect(result)}
          >
            <span className="symbol-tile">
              {result.asset.symbol.slice(0, 2)}
            </span>
            <span className="result-main">
              <strong>
                {result.asset.symbol} · {result.asset.display_name}
              </strong>
              <small>
                {result.asset.exchange} · {result.asset.mic} ·{" "}
                {result.asset.country}
              </small>
            </span>
            <span className="result-meta">
              <b>{result.asset.trading_currency}</b>
              <small>{result.asset.primary_listing ? "Primary" : "ADR"}</small>
            </span>
            <ArrowUpRight size={17} />
          </button>
        ))
      )}
    </div>
  );
}

function ReportView({
  report,
  language,
  baseCurrency,
  onCurrency,
  onShare,
}: {
  report: AnalysisReport;
  language: Language;
  baseCurrency: string;
  onCurrency: (currency: string) => Promise<void>;
  onShare: () => void;
}) {
  const t = useCopy(language);
  return (
    <article
      className="report"
      aria-label={`${report.asset.display_name} research report`}
    >
      <section className="report-head">
        <div className="asset-title">
          <span className="asset-monogram">
            {report.asset.symbol.slice(0, 2)}
          </span>
          <div>
            <div className="report-kicker">
              {report.asset.exchange} <span>/</span> {report.asset.mic}
            </div>
            <h2>{report.asset.display_name}</h2>
            <p>
              {report.asset.symbol} · {report.asset.country} ·{" "}
              {report.asset.security_type}
            </p>
          </div>
        </div>
        <div className="report-actions">
          <label>
            {t.baseCurrency}
            <span className="select-wrap">
              <select
                value={baseCurrency}
                onChange={(event) => void onCurrency(event.target.value)}
                aria-label={t.baseCurrency}
              >
                <option>USD</option>
                <option>CNY</option>
                <option>EUR</option>
                <option>JPY</option>
                <option>HKD</option>
              </select>
              <ChevronDown size={14} />
            </span>
          </label>
          <button className="secondary-button" onClick={onShare}>
            <Share2 size={17} /> {t.share}
          </button>
        </div>
        <div className="asset-badges">
          <Badge kind="mode" text={`${t.mode}: ${report.data_mode}`} />
          <Badge
            text={`${report.asset.trading_currency} / ${report.asset.reporting_currency}`}
          />
          <Badge text={report.asset.timezone} />
          <Badge text={`LLM: ${report.llm_provider}`} />
          <Badge text={`${t.asOf}: ${formatDate(report.as_of, language)}`} />
        </div>
      </section>

      <div className="stat-grid">
        <Stat
          label={
            report.market_price.provenance.data_mode === "live"
              ? t.livePrice
              : t.price
          }
          value={`${formatNumber(report.market_price.value, 2)} ${report.market_price.unit}`}
          detail={`${t.snapshotDate}: ${report.market_price.period}`}
          icon={CircleDollarSign}
        />
        <Stat
          label={t.consensus}
          value={`${report.consensus_score} / 100`}
          detail={report.consensus}
          icon={Scale}
          accent
        />
        <Stat
          label="ROIC"
          value={`${report.financials.at(-1)?.roic.toFixed(1)}%`}
          detail={report.financials.at(-1)?.period ?? ""}
          icon={BarChart3}
        />
        <Stat
          label={t.sources}
          value={`${report.evidence.length}`}
          detail={report.data_mode.toUpperCase()}
          icon={FileCheck2}
        />
      </div>

      {report.market_price.provenance.data_mode === "fixture" && (
        <div className="freshness-notice" role="note">
          <AlertTriangle size={18} />
          <div>
            <strong>{t.snapshotNoticeTitle}</strong>
            <p>{t.snapshotNoticeBody}</p>
            <small>
              {t.snapshotDate}: {report.market_price.period} ·{" "}
              {t.latestFilingDate}:{" "}
              {formatDate(
                report.evidence[0]?.published_at ?? report.as_of,
                language,
              )}
            </small>
          </div>
        </div>
      )}

      <Section title={t.overview} eyebrow="01 / MEMO" icon={BookOpen}>
        <div className="memo-grid">
          <div className="memo-lead">
            <p>{report.company_summary}</p>
            <p>{report.industry_summary}</p>
          </div>
          <aside className="accounting-note">
            <strong>{t.accounting}</strong>
            <p>{report.accounting_note}</p>
          </aside>
        </div>
        <div className="consensus-strip">
          <div
            className="score-ring"
            style={{ "--score": report.consensus_score } as React.CSSProperties}
          >
            <strong>{report.consensus_score}</strong>
          </div>
          <div>
            <span>{t.consensus}</span>
            <h3>{report.consensus}</h3>
            <p>{report.chair_synthesis}</p>
          </div>
          <div className="vote-bars">
            {report.agents.slice(0, 6).map((agent) => (
              <div key={agent.agent_id}>
                <span>{agent.agent_id}</span>
                <i>
                  <b style={{ width: `${agent.score}%` }} />
                </i>
                <strong>{agent.score}</strong>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title={t.valuation} eyebrow="02 / RANGE" icon={Scale}>
        <ScenarioGrid
          scenarios={report.scenarios}
          converted={report.converted_scenarios}
          language={language}
        />
        {report.fx_rate && (
          <p className="fx-note">
            <Globe2 size={15} /> 1 {report.fx_rate.base} ={" "}
            {report.fx_rate.rate.toFixed(4)} {report.fx_rate.quote} ·{" "}
            {report.fx_rate.as_of} · {report.fx_rate.source_name} ·{" "}
            {report.fx_rate.data_mode}
          </p>
        )}
      </Section>

      <Section
        title={t.financials}
        eyebrow="03 / FUNDAMENTALS"
        icon={BarChart3}
      >
        <FinancialChart financials={report.financials} language={language} />
        <FinancialTable financials={report.financials} language={language} />
      </Section>

      <Section title={t.council} eyebrow="04 / AGENTS" icon={Users}>
        <AgentGrid agents={report.agents} language={language} />
      </Section>

      <Section title={t.debate} eyebrow="05 / DELIBERATION" icon={Sparkles}>
        <div className="debate-timeline">
          {report.debate.map((turn) => (
            <div className="debate-turn" key={turn.sequence}>
              <span className="timeline-index">
                {String(turn.sequence).padStart(2, "0")}
              </span>
              <div className="turn-body">
                <div>
                  <strong>{turn.agent_name}</strong>
                  <Badge text={turn.kind} />
                </div>
                <p>{turn.statement}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <div className="two-column-sections">
        <Section title={t.evidence} eyebrow="06 / PROVENANCE" icon={FileCheck2}>
          <div className="evidence-list">
            {report.evidence.map((item) => (
              <a
                key={item.source_url}
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
              >
                <span>
                  <FileCheck2 size={18} />
                </span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.claim}</p>
                  <small>
                    {formatDate(item.published_at, language)} · {item.data_mode}
                  </small>
                </div>
                <ExternalLink size={16} />
              </a>
            ))}
            <a
              href={report.market_price.provenance.source_url}
              target="_blank"
              rel="noreferrer"
            >
              <span>
                <CircleDollarSign size={18} />
              </span>
              <div>
                <strong>{report.market_price.provenance.source_name}</strong>
                <p>{report.market_price.provenance.provenance}</p>
                <small>
                  {report.market_price.provenance.reported_currency} ·{" "}
                  {formatDate(
                    report.market_price.provenance.retrieved_at,
                    language,
                  )}{" "}
                  · {report.market_price.provenance.data_mode}
                </small>
              </div>
              <ExternalLink size={16} />
            </a>
          </div>
        </Section>
        <Section title={t.risk} eyebrow="07 / RED TEAM" icon={ShieldAlert}>
          <RiskPanel report={report} language={language} />
        </Section>
      </div>
      <div className="disclaimer">
        <AlertTriangle size={18} />
        <p>{report.disclaimer}</p>
      </div>
    </article>
  );
}

function Section({
  title,
  eyebrow,
  icon: Icon,
  children,
}: {
  title: string;
  eyebrow: string;
  icon: SectionIcon;
  children: React.ReactNode;
}) {
  return (
    <section className="report-section">
      <div className="section-heading">
        <span className="section-icon">
          <Icon size={18} />
        </span>
        <div>
          <small>{eyebrow}</small>
          <h2>{title}</h2>
        </div>
      </div>
      {children}
    </section>
  );
}

function Badge({ text, kind }: { text: string; kind?: "mode" }) {
  return (
    <span className={`badge ${kind === "mode" ? "mode-badge" : ""}`}>
      {kind === "mode" && <Check size={12} />} {text}
    </span>
  );
}

function Stat({
  label,
  value,
  detail,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  detail: string;
  icon: SectionIcon;
  accent?: boolean;
}) {
  return (
    <div className={`stat-card ${accent ? "stat-accent" : ""}`}>
      <div>
        <span>{label}</span>
        <Icon size={18} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function ScenarioGrid({
  scenarios,
  converted,
  language,
}: {
  scenarios: ValuationScenario[];
  converted: ValuationScenario[];
  language: Language;
}) {
  const t = useCopy(language);
  return (
    <div className="scenario-grid">
      {scenarios.map((scenario, index) => (
        <article
          className={`scenario scenario-${scenario.name.toLowerCase()}`}
          key={scenario.name}
        >
          <div className="scenario-head">
            <span>{scenario.name}</span>
            <small>{Math.round(scenario.probability * 100)}%</small>
          </div>
          <strong>
            {formatNumber(scenario.value_per_share, 2)}
            <small>{scenario.currency}</small>
          </strong>
          {converted[index] &&
            converted[index].currency !== scenario.currency && (
              <p className="converted">
                {t.converted}:{" "}
                {formatNumber(converted[index].value_per_share, 2)}{" "}
                {converted[index].currency}
              </p>
            )}
          <p>{scenario.rationale}</p>
          <dl>
            <div>
              <dt>Growth</dt>
              <dd>{scenario.growth_rate.toFixed(1)}%</dd>
            </div>
            <div>
              <dt>Margin</dt>
              <dd>{scenario.operating_margin.toFixed(1)}%</dd>
            </div>
            <div>
              <dt>Discount</dt>
              <dd>{scenario.discount_rate.toFixed(1)}%</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

function FinancialChart({
  financials,
  language,
}: {
  financials: FinancialPeriod[];
  language: Language;
}) {
  const t = useCopy(language);
  const maxRevenue = Math.max(...financials.map((period) => period.revenue));
  const points = financials
    .map((period, index) => {
      const x = 70 + index * 180;
      const y = 135 - (period.roic / 40) * 90;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <div
      className="financial-chart"
      role="img"
      aria-label={`Revenue bars and ROIC trend for ${financials.map((item) => item.period).join(", ")}`}
    >
      <div className="chart-legend">
        <span>
          <i className="legend-bar" /> {t.revenue}
        </span>
        <span>
          <i className="legend-line" /> ROIC
        </span>
      </div>
      <svg viewBox="0 0 500 180" aria-hidden="true">
        {[40, 80, 120, 160].map((y) => (
          <line key={y} x1="35" x2="475" y1={y} y2={y} className="gridline" />
        ))}
        {financials.map((period, index) => {
          const height = (period.revenue / maxRevenue) * 112;
          return (
            <g key={period.period}>
              <rect
                x={48 + index * 180}
                y={154 - height}
                width="44"
                height={height}
                rx="4"
              />
              <text x={70 + index * 180} y="174" textAnchor="middle">
                {period.period}
              </text>
            </g>
          );
        })}
        <polyline points={points} className="roic-line" />
        {financials.map((period, index) => (
          <g key={`roic-${period.period}`}>
            <circle
              cx={70 + index * 180}
              cy={135 - (period.roic / 40) * 90}
              r="5"
            />
            <text
              className="point-label"
              x={70 + index * 180}
              y={125 - (period.roic / 40) * 90}
              textAnchor="middle"
            >
              {period.roic.toFixed(1)}%
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function FinancialTable({
  financials,
  language,
}: {
  financials: FinancialPeriod[];
  language: Language;
}) {
  const t = useCopy(language);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Period</th>
            <th>{t.revenue}</th>
            <th>{t.operatingIncome}</th>
            <th>{t.fcf}</th>
            <th>ROIC</th>
          </tr>
        </thead>
        <tbody>
          {financials.map((period) => (
            <tr key={period.period}>
              <th>{period.period}</th>
              <td>{formatNumber(period.revenue)}</td>
              <td>{formatNumber(period.operating_income)}</td>
              <td>{formatNumber(period.free_cash_flow)}</td>
              <td>{period.roic.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="table-note">
        {financials[0]?.currency} · {financials[0]?.unit} ·{" "}
        {financials[0]?.accounting_standard} · FY end{" "}
        {financials[0]?.fiscal_year_end}
      </p>
    </div>
  );
}

function AgentGrid({
  agents,
  language,
}: {
  agents: AgentResult[];
  language: Language;
}) {
  const [expanded, setExpanded] = useState<string | null>(
    agents[0]?.agent_id ?? null,
  );
  const t = useCopy(language);
  return (
    <div className="agent-grid">
      {agents.map((agent, index) => {
        const isExpanded = expanded === agent.agent_id;
        return (
          <article
            className={`agent-card ${isExpanded ? "expanded" : ""}`}
            key={agent.agent_id}
          >
            <button
              className="agent-summary"
              onClick={() => setExpanded(isExpanded ? null : agent.agent_id)}
              aria-expanded={isExpanded}
            >
              <span className="agent-index">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="agent-name">
                <strong>{agent.display_name}</strong>
                <small>{agent.verdict}</small>
              </span>
              <span className="agent-score">{agent.score}</span>
              <ChevronDown size={18} />
            </button>
            {isExpanded && (
              <div className="agent-detail">
                <p className="agent-method">
                  <strong>{t.methodology}</strong>
                  {agent.methodology}
                </p>
                <blockquote>{agent.thesis}</blockquote>
                <div className="claim-columns">
                  <ClaimList
                    title={t.facts}
                    items={agent.facts}
                    className="fact"
                  />
                  <ClaimList
                    title={t.inferences}
                    items={agent.inferences}
                    className="inference"
                  />
                  <ClaimList
                    title={t.opinions}
                    items={agent.opinions}
                    className="opinion"
                  />
                </div>
                <small>
                  {t.confidence}: {Math.round(agent.confidence * 100)}%
                </small>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

function ClaimList({
  title,
  items,
  className,
}: {
  title: string;
  items: string[];
  className: string;
}) {
  return (
    <div className={`claim-list ${className}`}>
      <strong>{title}</strong>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function RiskPanel({
  report,
  language,
}: {
  report: AnalysisReport;
  language: Language;
}) {
  const t = useCopy(language);
  return (
    <div className="risk-panel">
      <ClaimList title={t.risk} items={report.risks} className="risk" />
      <ClaimList
        title={t.invalidation}
        items={report.invalidation_conditions}
        className="invalidation"
      />
      <ClaimList
        title={t.missing}
        items={report.missing_data}
        className="missing"
      />
    </div>
  );
}

function ShareDialog({
  report,
  language,
  onClose,
}: {
  report: AnalysisReport;
  language: Language;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDivElement>(null);
  const t = useCopy(language);
  useEffect(() => {
    dialog.current?.focus();
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const title =
    report.asset.symbol === "0700"
      ? "6 Investor Agents Debate Tencent"
      : `Why the AI Committee Disagrees on ${report.asset.display_name}`;

  const download = () => {
    const svg = buildShareSvg(report, title);
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `global-equity-council-${report.asset.symbol}.svg`;
    link.click();
    URL.revokeObjectURL(link.href);
  };
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="share-dialog"
        role="dialog"
        aria-modal="true"
        aria-label={t.share}
        tabIndex={-1}
        ref={dialog}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="dialog-heading">
          <div>
            <small>SHARE CARD / 1200 × 630</small>
            <h2>{t.share}</h2>
          </div>
          <button onClick={onClose} aria-label={t.close}>
            <X size={20} />
          </button>
        </div>
        <div className="share-card">
          <div className="share-brand">
            <Scale size={20} />
            GLOBAL EQUITY COUNCIL
          </div>
          <span className="share-kicker">AI COMMITTEE RESEARCH</span>
          <h3>{title}</h3>
          <div className="share-score">
            <strong>{report.consensus_score}</strong>
            <span>
              {report.consensus}
              <small>COUNCIL SCORE / 100</small>
            </span>
          </div>
          <div className="share-meta">
            <span>{report.asset.exchange}</span>
            <span>{report.asset.symbol}</span>
            <span>{report.analysis_date}</span>
            <span>{report.data_mode}</span>
          </div>
          <p>Research & education only · Not investment advice</p>
        </div>
        <button className="primary-button download-button" onClick={download}>
          <Download size={18} /> {t.download}
        </button>
      </div>
    </div>
  );
}

function buildShareSvg(report: AnalysisReport, title: string) {
  const escapedTitle = title.replaceAll("&", "&amp;").replaceAll("<", "&lt;");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#071b1d"/>
  <circle cx="1040" cy="80" r="250" fill="none" stroke="#1ca58f" stroke-width="1" opacity=".35"/>
  <circle cx="1040" cy="80" r="180" fill="none" stroke="#d5a94f" stroke-width="1" opacity=".3"/>
  <text x="72" y="75" fill="#8bd6c8" font-family="Arial" font-size="22" font-weight="700" letter-spacing="3">GLOBAL EQUITY COUNCIL</text>
  <text x="72" y="155" fill="#d5a94f" font-family="Arial" font-size="18" font-weight="700" letter-spacing="4">AI COMMITTEE RESEARCH</text>
  <foreignObject x="72" y="185" width="860" height="180"><div xmlns="http://www.w3.org/1999/xhtml" style="font:700 52px/1.12 Arial;color:#f4f7f4">${escapedTitle}</div></foreignObject>
  <text x="72" y="465" fill="#f4f7f4" font-family="Arial" font-size="86" font-weight="700">${report.consensus_score}</text>
  <text x="210" y="430" fill="#f4f7f4" font-family="Arial" font-size="28" font-weight="700">${report.consensus}</text>
  <text x="210" y="462" fill="#8aa5a2" font-family="Arial" font-size="16" letter-spacing="2">COUNCIL SCORE / 100</text>
  <line x1="72" x2="1128" y1="510" y2="510" stroke="#31504f"/>
  <text x="72" y="553" fill="#a9bfbc" font-family="Arial" font-size="18">${report.asset.exchange}  ·  ${report.asset.symbol}  ·  ${report.analysis_date}  ·  ${report.data_mode}</text>
  <text x="72" y="590" fill="#718d89" font-family="Arial" font-size="15">Research &amp; education only · Not investment advice</text>
</svg>`;
}

function ReportSkeleton() {
  return (
    <div
      className="report skeleton-report"
      aria-label="Loading report"
      aria-live="polite"
    >
      <div className="skeleton wide" />
      <div className="stat-grid">
        {[1, 2, 3, 4].map((item) => (
          <div className="skeleton card" key={item} />
        ))}
      </div>
      <div className="skeleton block" />
    </div>
  );
}
