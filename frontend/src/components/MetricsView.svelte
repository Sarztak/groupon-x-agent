<script>
  import { onMount } from 'svelte'

  export let refreshTrigger = 0

  let data = null
  let loading = true
  let error = false

  $: if (refreshTrigger >= 0) fetchMetrics()

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

<aside class="metrics">
  <div class="header">
    <span class="title">Agent Impact</span>
    <button class="refresh" on:click={fetchMetrics} title="Refresh">↻</button>
  </div>

  {#if loading}
    <div class="empty">Loading…</div>
  {:else if error}
    <div class="empty err">Could not load metrics</div>
  {:else if data}
    <div class="body">

      <!-- PROJECTION -->
      <div class="section-header">Monthly Projection</div>
      <div class="section-note">Capacity-based forecast — assumes agent runs at full cadence</div>

      <div class="section-label">Posting cadence</div>
      <div class="grid">
        <div class="tile">
          <div class="num">{fmt(data.projection?.proactive_posts_per_month)}</div>
          <div class="lbl">Proactive posts/month</div>
          <div class="sub">{fmt(data.projection?.deal_drops_per_month)} deal drops · {fmt(data.projection?.trend_hooks_per_month)} trend hooks</div>
        </div>
        <div class="tile">
          <div class="num">{fmt(data.projection?.agent_replies_per_month)}</div>
          <div class="lbl">Replies/month</div>
          <div class="sub">{fmt(data.projection?.deal_request_replies_per_month)} deal_request · rest carry no link</div>
        </div>
      </div>

      <div class="section-label">Projected traffic</div>
      <div class="grid">
        <div class="tile">
          <div class="num">{fmt(data.projection?.sessions_from_posts)}</div>
          <div class="lbl">Sessions from posts</div>
          <div class="sub">~{fmt(data.projection?.assumptions?.sessions_per_post)} sessions/post</div>
        </div>
        <div class="tile">
          <div class="num">{fmt(data.projection?.sessions_from_replies)}</div>
          <div class="lbl">Sessions from replies</div>
          <div class="sub">{fmt(data.projection?.deal_request_replies_per_month)} deal replies × {data.projection?.assumptions?.sessions_per_reply} sessions/reply — acknowledge/positive carry no link</div>
        </div>
      </div>

      <div class="grid single">
        <div class="tile highlight">
          <div class="num green">{fmtUsd(data.projection?.conversion_value_usd)}<span class="per-month">/mo</span></div>
          <div class="lbl">Est. assisted conversion value</div>
          <div class="sub">{fmt(data.projection?.total_new_sessions)} sessions × ${data.baselines?.baseline_conversion_value_usd / data.baselines?.baseline_sessions_per_month}/session</div>
        </div>
      </div>

      <div class="section-label">Projected labor savings (execution only)</div>
      <div class="grid">
        <div class="tile">
          <div class="num">{data.projection?.hours_saved}h</div>
          <div class="lbl">Coordinator hours freed</div>
          <div class="sub">Drafting + posting time only — escalation load may increase</div>
        </div>
        <div class="tile">
          <div class="num green">{fmtUsd(data.projection?.cost_saved_usd)}<span class="per-month">/mo</span></div>
          <div class="lbl">Cost saved</div>
          <div class="sub">@ $40/hr loaded rate</div>
        </div>
      </div>

      <div class="section-label">Payback period</div>
      {#if data.projection?.payback}
        {@const pb = data.projection.payback}
        <div class="tile payback-tile">
          <div class="payback-row">
            <div class="payback-col">
              <div class="num">{pb.conservative.low_months}–{pb.conservative.high_months}<span class="per-month"> mo</span></div>
              <div class="lbl">Conservative</div>
              <div class="sub">{pb.conservative.basis}</div>
            </div>
            <div class="payback-divider"></div>
            <div class="payback-col">
              <div class="num green">{pb.full.low_days}–{pb.full.high_days}<span class="per-month"> days</span></div>
              <div class="lbl">Full uplift</div>
              <div class="sub">{pb.full.basis}</div>
            </div>
          </div>
          <div class="sub" style="margin-top:8px">Build cost {fmtUsd(pb.build_cost_low_usd)}–{fmtUsd(pb.build_cost_high_usd)} · run cost {fmtUsd(pb.monthly_run_cost_usd)}/mo</div>
        </div>
      {/if}

      <!-- ACTIVITY -->
      <div class="divider"></div>
      <div class="section-header">Session Activity</div>
      <div class="section-note">{data.activity?.note}</div>

      <div class="section-label">Posts published</div>
      <div class="grid">
        <div class="tile">
          <div class="num">{fmt(data.activity?.deal_drops_published)}</div>
          <div class="lbl">Deal drops</div>
        </div>
        <div class="tile">
          <div class="num">{fmt(data.activity?.trend_hooks_published)}</div>
          <div class="lbl">Trend hooks</div>
        </div>
      </div>

      <div class="section-label">Mentions</div>
      <div class="grid">
        <div class="tile">
          <div class="num">{fmt(data.activity?.mention_replies_sent)}</div>
          <div class="lbl">Replies sent</div>
          <div class="sub">{fmt(data.activity?.total_escalated_to_human)} escalated to human</div>
        </div>
        <div class="tile">
          <div class="num">{fmtPct(data.activity?.reply_rate)}</div>
          <div class="lbl">Reply rate</div>
          <div class="sub">vs {fmtPct(data.activity?.reply_rate_baseline)} baseline</div>
        </div>
      </div>

      {#if data.activity?.by_route && Object.keys(data.activity.by_route).length > 0}
        <div class="section-label">By route</div>
        <div class="route-list">
          {#each Object.entries(data.activity.by_route) as [route, count]}
            <div class="route-row">
              <span class="route-name">{route.replace(/_/g, ' ')}</span>
              <span class="route-count">{count}</span>
            </div>
          {/each}
        </div>
      {/if}

      <div class="section-label">Derived impact</div>
      <div class="grid single">
        <div class="tile">
          <div class="num">{fmt(data.activity?.total_sessions)}</div>
          <div class="lbl">Est. sessions this session</div>
          <div class="sub">{fmt(data.activity?.sessions_from_posts)} from posts · {fmt(data.activity?.sessions_from_replies)} from replies</div>
        </div>
      </div>

      <div class="section-label">API cost</div>
      <div class="grid">
        <div class="tile">
          <div class="num red">{fmtUsd4(data.activity?.api_cost?.total_usd)}</div>
          <div class="lbl">Est. API spend</div>
          <div class="sub">{fmtUsd4(data.activity?.api_cost?.posts_usd)} posts · {fmtUsd4(data.activity?.api_cost?.escalations_usd)} escalations</div>
        </div>
        <div class="tile">
          <div class="num green">{fmtUsd(data.activity?.cost_saved_usd)}</div>
          <div class="lbl">Labor saved (execution)</div>
          <div class="sub">{data.activity?.hours_saved}h @ $40/hr</div>
        </div>
      </div>

      <div class="disclaimer">
        Illustrative scenario data — not live Groupon figures
      </div>

    </div>
  {/if}
</aside>

<style>
  .metrics {
    width: 300px;
    flex-shrink: 0;
    border-left: 1px solid #2f3336;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .header {
    padding: 14px 16px;
    border-bottom: 1px solid #2f3336;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }

  .title {
    font-size: 15px;
    font-weight: 600;
    color: #e7e9ea;
  }

  .refresh {
    background: none;
    border: none;
    color: #71767b;
    font-size: 16px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
    line-height: 1;
  }
  .refresh:hover { color: #e7e9ea; background: #1d1f23; }

  .body {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #71767b;
    font-size: 13px;
  }
  .empty.err { color: #f4212e; }

  .section-header {
    font-size: 13px;
    font-weight: 600;
    color: #e7e9ea;
    padding: 4px 0 0;
  }

  .section-note {
    font-size: 10px;
    color: #71767b;
    line-height: 1.4;
    margin-top: -4px;
  }

  .section-label {
    font-size: 10px;
    color: #71767b;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 4px 0 2px;
  }

  .divider {
    border-top: 1px solid #2f3336;
    margin: 4px 0;
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
  .grid.single { grid-template-columns: 1fr; }

  .tile {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .tile.highlight { border-color: #16a34a44; background: #0d1f13; }

  .num {
    font-size: 22px;
    font-weight: 700;
    color: #e7e9ea;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }
  .num.green { color: #22c55e; }
  .num.red   { color: #f4212e; }

  .per-month {
    font-size: 12px;
    font-weight: 400;
    color: #71767b;
  }

  .lbl {
    font-size: 11px;
    color: #e7e9ea;
    font-weight: 500;
    margin-top: 2px;
  }

  .sub {
    font-size: 10px;
    color: #71767b;
    line-height: 1.4;
    margin-top: 2px;
  }

  .route-list {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 10px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .route-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .route-name {
    font-size: 11px;
    color: #71767b;
    text-transform: capitalize;
  }

  .route-count {
    font-size: 11px;
    font-weight: 600;
    color: #e7e9ea;
    font-variant-numeric: tabular-nums;
  }

  .payback-tile {
    grid-column: 1 / -1;
  }

  .payback-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }

  .payback-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .payback-divider {
    width: 1px;
    background: #2f3336;
    align-self: stretch;
    flex-shrink: 0;
  }

  .disclaimer {
    font-size: 10px;
    color: #71767b;
    text-align: center;
    padding: 6px 0 2px;
    font-style: italic;
  }
</style>
