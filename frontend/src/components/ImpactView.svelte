<script>
  import { onMount } from 'svelte'

  let data = null
  let loading = true
  let error = false

  async function fetchMetrics() {
    loading = true
    error = false
    try {
      const res = await fetch('/api/metrics')
      data = await res.json()
    } catch (e) {
      error = true
    } finally {
      loading = false
    }
  }

  onMount(fetchMetrics)

  function fmt(n) { return n == null ? '—' : Number(n).toLocaleString() }
  function fmtPct(n) { return n == null ? '—' : (n * 100).toFixed(0) + '%' }
  function fmtUsd(n) { return n == null ? '—' : '$' + Number(n).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }
  function fmtUsd4(n) { return n == null ? '—' : '$' + Number(n).toFixed(4) }
</script>

<div class="impact">
  <div class="page-header">
    <div>
      <div class="page-title">Impact Model</div>
      <div class="page-sub">Monthly projection + session activity · Illustrative scenario — not live Groupon figures</div>
    </div>
    <button class="refresh-btn" on:click={fetchMetrics}>↻ Refresh</button>
  </div>

  {#if loading}
    <div class="loading">Loading…</div>
  {:else if error}
    <div class="loading err">Could not load metrics</div>
  {:else if data}

    <!-- SUMMARY ROW -->
    <div class="summary-row">
      <div class="summary-tile highlight">
        <div class="s-num green">{fmtUsd(data.projection?.payback?.total_monthly_benefit)}</div>
        <div class="s-lbl">Total monthly benefit</div>
        <div class="s-sub">labor value + conversion uplift</div>
      </div>
      <div class="summary-tile">
        <div class="s-num">{fmtUsd(data.projection?.cost_saved_usd)}</div>
        <div class="s-lbl">Labor savings/month</div>
        <div class="s-sub">execution time at $40/hr coordinator rate</div>
      </div>
      <div class="summary-tile">
        <div class="s-num">{fmtUsd(data.projection?.conversion_value_usd)}</div>
        <div class="s-lbl">Conversion uplift/month</div>
        <div class="s-sub">sessions × $4.50 (assumed)</div>
      </div>
      <div class="summary-tile">
        <div class="s-num red">{fmtUsd(data.projection?.payback?.monthly_run_cost_usd)}</div>
        <div class="s-lbl">API run cost/month</div>
        <div class="s-sub">Sonnet 4.6 with prompt caching</div>
      </div>
    </div>

    <!-- MAIN GRID -->
    <div class="main-grid">

      <!-- LEFT: PROJECTION -->
      <div class="panel">
        <div class="panel-title">Monthly Projection <span class="panel-badge">Capacity-based</span></div>

        <div class="spec-label">Posting cadence</div>
        <div class="spec-grid">
          <div class="spec-tile">
            <div class="sp-num">{fmt(data.projection?.proactive_posts_per_month)}</div>
            <div class="sp-lbl">Proactive posts/month</div>
            <div class="sp-sub">{fmt(data.projection?.deal_drops_per_month)} deal drops · {fmt(data.projection?.trend_hooks_per_month)} trend hooks</div>
          </div>
          <div class="spec-tile">
            <div class="sp-num">{fmt(data.projection?.agent_replies_per_month)}</div>
            <div class="sp-lbl">Replies/month</div>
            <div class="sp-sub">{fmtPct(data.projection?.assumptions?.agent_reply_rate)} of {fmt(data.projection?.inbound_mentions_per_month)} inbound mentions</div>
          </div>
        </div>

        <div class="spec-label">Traffic model</div>
        <div class="spec-grid">
          <div class="spec-tile">
            <div class="sp-num">{fmt(data.projection?.sessions_from_posts)}</div>
            <div class="sp-lbl">Sessions from posts</div>
            <div class="sp-sub">~{fmt(data.projection?.assumptions?.sessions_per_post)} sessions/post · linear baseline rate</div>
          </div>
          <div class="spec-tile">
            <div class="sp-num">{fmt(data.projection?.sessions_from_replies)}</div>
            <div class="sp-lbl">Sessions from replies</div>
            <div class="sp-sub">{fmt(data.projection?.deal_request_replies_per_month)} deal replies × {data.projection?.assumptions?.sessions_per_reply} · {fmtPct(data.projection?.assumptions?.deal_request_reply_fraction)} of replies carry a deal link</div>
          </div>
        </div>

        <div class="total-sessions">
          <span class="ts-label">Total new sessions/month</span>
          <span class="ts-num">{fmt(data.projection?.total_new_sessions)}</span>
          <span class="ts-value">× $4.50 = {fmtUsd(data.projection?.conversion_value_usd)}</span>
        </div>

        <div class="spec-label">Labor savings (execution only)</div>
        <div class="labor-table">
          <div class="labor-row">
            <span>{fmt(data.projection?.proactive_posts_per_month)} posts × 30 min</span>
            <span>{Math.round(data.projection?.proactive_posts_per_month * 0.5)}h</span>
          </div>
          <div class="labor-row">
            <span>{fmt(data.projection?.agent_replies_per_month)} replies × 5 min</span>
            <span>{Math.round(data.projection?.agent_replies_per_month * (5/60) * 10) / 10}h</span>
          </div>
          <div class="labor-row total-row">
            <span>Total · × $80/hr</span>
            <span class="green">{data.projection?.hours_saved}h · {fmtUsd(data.projection?.cost_saved_usd)}/mo @ $40/hr</span>
          </div>
        </div>

        <div class="spec-note">Covers drafting + posting execution only. Escalation handling load may increase — agent opens new coverage of previously ignored mentions.</div>
      </div>

      <!-- RIGHT: ACTIVITY + PAYBACK -->
      <div class="right-col">

        <!-- PAYBACK -->
        <div class="panel">
          <div class="panel-title">Payback Period</div>
          <div class="payback-grid">
            <div class="payback-scenario">
              <div class="pb-label">Conservative</div>
              <div class="pb-num">{data.projection?.payback?.conservative?.low_months}–{data.projection?.payback?.conservative?.high_months} months</div>
              <div class="pb-sub">Hours saved only · most confident figure</div>
            </div>
            <div class="payback-divider"></div>
            <div class="payback-scenario">
              <div class="pb-label">Full uplift</div>
              <div class="pb-num green">{data.projection?.payback?.full?.low_days}–{data.projection?.payback?.full?.high_days} days</div>
              <div class="pb-sub">Includes conversion uplift · dependent on unverified session→revenue assumption</div>
            </div>
          </div>
          <div class="build-cost-row">
            <div class="bc-item">
              <div class="bc-val">{fmtUsd(data.projection?.payback?.build_cost_low_usd)}–{fmtUsd(data.projection?.payback?.build_cost_high_usd)}</div>
              <div class="bc-lbl">Build cost (100–138 hrs × $80/hr)</div>
            </div>
            <div class="bc-item">
              <div class="bc-val red">{fmtUsd(data.projection?.payback?.monthly_run_cost_usd)}/mo</div>
              <div class="bc-lbl">Ongoing API cost</div>
            </div>
          </div>
        </div>

        <!-- ACTIVITY -->
        <div class="panel">
          <div class="panel-title">Session Activity <span class="panel-badge warn">Test telemetry</span></div>
          <div class="spec-note" style="margin-bottom:10px">Log counts from this demo session — in production reflects real agent output.</div>

          <div class="spec-grid">
            <div class="spec-tile">
              <div class="sp-num">{fmt(data.activity?.deal_drops_published)}</div>
              <div class="sp-lbl">Deal drops</div>
            </div>
            <div class="spec-tile">
              <div class="sp-num">{fmt(data.activity?.trend_hooks_published)}</div>
              <div class="sp-lbl">Trend hooks</div>
            </div>
            <div class="spec-tile">
              <div class="sp-num">{fmt(data.activity?.mention_replies_sent)}</div>
              <div class="sp-lbl">Replies sent</div>
            </div>
            <div class="spec-tile">
              <div class="sp-num">{fmt(data.activity?.total_escalated_to_human)}</div>
              <div class="sp-lbl">Escalated</div>
            </div>
          </div>

          {#if data.activity?.by_route && Object.keys(data.activity.by_route).length > 0}
            <div class="spec-label">By route</div>
            <div class="route-list">
              {#each Object.entries(data.activity.by_route) as [route, count]}
                <div class="route-row">
                  <span>{route.replace(/_/g, ' ')}</span>
                  <span class="route-count">{count}</span>
                </div>
              {/each}
            </div>
          {/if}

          <div class="spec-label" style="margin-top:10px">Derived from activity</div>
          <div class="labor-table">
            <div class="labor-row">
              <span>Sessions (posts + deal replies)</span>
              <span>{fmt(data.activity?.total_sessions)}</span>
            </div>
            <div class="labor-row">
              <span>Conversion value</span>
              <span class="green">{fmtUsd(data.activity?.conversion_value_usd)}</span>
            </div>
            <div class="labor-row">
              <span>API spend</span>
              <span class="red">{fmtUsd4(data.activity?.api_cost?.total_usd)}</span>
            </div>
            <div class="labor-row">
              <span>Labor saved (execution)</span>
              <span class="green">{fmtUsd(data.activity?.cost_saved_usd)}</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ASSUMPTIONS -->
    <div class="assumptions-bar">
      <span class="assump-title">Assumptions</span>
      {#if data.projection?.assumptions}
        {@const a = data.projection.assumptions}
        <span>{a.deal_drops_per_week} deal drops/wk</span>
        <span class="dot">·</span>
        <span>{a.trend_hooks_per_week} trend hooks/wk</span>
        <span class="dot">·</span>
        <span>{a.inbound_mentions_per_week} mentions/wk</span>
        <span class="dot">·</span>
        <span>{fmtPct(a.agent_reply_rate)} agent reply rate</span>
        <span class="dot">·</span>
        <span>{fmtPct(a.deal_request_reply_fraction)} deal_request mix</span>
        <span class="dot">·</span>
        <span>{a.reply_reach} reach × {fmtPct(a.reply_ctr)} CTR = {a.sessions_per_reply} sessions/reply</span>
        <span class="dot">·</span>
        <span>${a.value_per_session_usd}/session</span>
      {/if}
    </div>

  {/if}
</div>

<style>
  .impact {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
  }

  .page-title {
    font-size: 20px;
    font-weight: 700;
    color: #e7e9ea;
  }

  .page-sub {
    font-size: 12px;
    color: #71767b;
    margin-top: 4px;
  }

  .refresh-btn {
    background: #1d1f23;
    border: 1px solid #2f3336;
    color: #e7e9ea;
    font-size: 13px;
    padding: 6px 14px;
    border-radius: 20px;
    cursor: pointer;
  }
  .refresh-btn:hover { background: #2f3336; }

  .loading {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #71767b;
    font-size: 14px;
  }
  .loading.err { color: #f4212e; }

  /* Summary row */
  .summary-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }

  .summary-tile {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 12px;
    padding: 16px 18px;
  }
  .summary-tile.highlight { border-color: #16a34a44; background: #0d1f13; }

  .s-num {
    font-size: 28px;
    font-weight: 700;
    color: #e7e9ea;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }
  .s-num.green { color: #22c55e; }
  .s-num.red   { color: #f4212e; }

  .s-lbl { font-size: 12px; color: #e7e9ea; font-weight: 500; margin-top: 4px; }
  .s-sub { font-size: 11px; color: #71767b; margin-top: 2px; }

  /* Main grid */
  .main-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 16px;
    align-items: start;
  }

  .right-col {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* Panel */
  .panel {
    background: #0e0f11;
    border: 1px solid #2f3336;
    border-radius: 14px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .panel-title {
    font-size: 14px;
    font-weight: 600;
    color: #e7e9ea;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .panel-badge {
    font-size: 10px;
    font-weight: 500;
    background: #1d1f23;
    border: 1px solid #2f3336;
    color: #71767b;
    padding: 2px 8px;
    border-radius: 20px;
  }
  .panel-badge.warn { border-color: #854d0e44; background: #1c1208; color: #a16207; }

  .spec-label {
    font-size: 10px;
    color: #71767b;
    text-transform: uppercase;
    letter-spacing: 0.07em;
  }

  .spec-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .spec-tile {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    padding: 12px 14px;
  }

  .sp-num {
    font-size: 24px;
    font-weight: 700;
    color: #e7e9ea;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }

  .sp-lbl { font-size: 11px; color: #e7e9ea; font-weight: 500; margin-top: 3px; }
  .sp-sub { font-size: 10px; color: #71767b; margin-top: 2px; line-height: 1.4; }

  .total-sessions {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .ts-label { font-size: 12px; color: #71767b; flex: 1; }
  .ts-num { font-size: 20px; font-weight: 700; color: #e7e9ea; font-variant-numeric: tabular-nums; }
  .ts-value { font-size: 13px; color: #22c55e; font-weight: 600; }

  .labor-table {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    overflow: hidden;
  }

  .labor-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    font-size: 12px;
    color: #71767b;
    border-bottom: 1px solid #16181c;
  }
  .labor-row:last-child { border-bottom: none; }
  .labor-row.total-row { background: #16181c; color: #e7e9ea; font-weight: 500; }

  .green { color: #22c55e; }
  .red   { color: #f4212e; }

  .spec-note {
    font-size: 11px;
    color: #71767b;
    line-height: 1.5;
    font-style: italic;
  }

  /* Payback */
  .payback-grid {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }

  .payback-scenario { flex: 1; }
  .payback-divider { width: 1px; background: #2f3336; align-self: stretch; flex-shrink: 0; }

  .pb-label { font-size: 10px; color: #71767b; text-transform: uppercase; letter-spacing: 0.07em; }
  .pb-num { font-size: 22px; font-weight: 700; color: #e7e9ea; margin: 4px 0; }
  .pb-num.green { color: #22c55e; }
  .pb-sub { font-size: 10px; color: #71767b; line-height: 1.4; }

  .build-cost-row {
    display: flex;
    gap: 16px;
    border-top: 1px solid #2f3336;
    padding-top: 12px;
  }

  .bc-item { flex: 1; }
  .bc-val { font-size: 16px; font-weight: 700; color: #e7e9ea; }
  .bc-val.red { color: #f4212e; }
  .bc-lbl { font-size: 10px; color: #71767b; margin-top: 2px; }

  /* Route list */
  .route-list {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    overflow: hidden;
  }

  .route-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 12px;
    font-size: 11px;
    color: #71767b;
    border-bottom: 1px solid #16181c;
    text-transform: capitalize;
  }
  .route-row:last-child { border-bottom: none; }
  .route-count { font-weight: 600; color: #e7e9ea; font-variant-numeric: tabular-nums; }

  /* Assumptions bar */
  .assumptions-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 8px;
    align-items: center;
    font-size: 11px;
    color: #71767b;
    background: #0e0f11;
    border: 1px solid #2f3336;
    border-radius: 10px;
    padding: 10px 16px;
  }

  .assump-title { font-weight: 600; color: #e7e9ea; margin-right: 4px; }
  .dot { color: #2f3336; }
</style>
