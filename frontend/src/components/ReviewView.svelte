<script>
  import { onMount, onDestroy } from 'svelte'

  export let items = []
  export let onApprove
  export let onDiscard

  let now = Date.now()
  let ticker
  let killActive = false

  onMount(async () => {
    ticker = setInterval(() => { now = Date.now() }, 30000)
    const res = await fetch('/api/kill_switch')
    const data = await res.json()
    killActive = data.active
  })
  onDestroy(() => clearInterval(ticker))

  async function toggleKill() {
    const res = await fetch('/api/kill_switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !killActive })
    })
    const data = await res.json()
    killActive = data.active
  }

  function fmtAge(mins) {
    if (mins < 1)  return 'just now'
    if (mins < 60) return `${mins}m ago`
    return `${Math.floor(mins / 60)}h ${mins % 60}m ago`
  }
</script>

<aside>
  <div class="header">
    <span class="title">Human review</span>
    {#if items.length > 0}
      <span class="badge">{items.length}</span>
    {/if}
    <button class="kill-btn {killActive ? 'kill-active' : ''}" on:click={toggleKill}>
      {killActive ? '⏹ Paused' : '▶ Live'}
    </button>
  </div>

  <div class="body">
    {#if items.length === 0}
      <div class="empty">No pending items</div>
    {:else}
      {#each items as item (item.id)}
        <div class="card">
          {#if item.createdAt}
            {@const mins = Math.floor((now - item.createdAt) / 60000)}
            <div class="age {mins >= 240 ? 'overdue' : mins >= 60 ? 'warn' : ''}">⏱ {fmtAge(mins)}</div>
          {/if}
          <div class="section">
            <div class="label">Incoming</div>
            <div class="content">{item.input}</div>
          </div>

          <div class="section">
            <div class="label">Reason</div>
            <div class="content">{item.reason}</div>
          </div>

          {#if item.guardReport?.assessment}
            <div class="section">
              <div class="label">Guard assessment</div>
              <div class="content">{item.guardReport.assessment}</div>
            </div>
          {/if}

          {#if item.guardReport?.flags}
            {@const activeFlags = Object.entries(item.guardReport.flags).filter(([, v]) => v).map(([k]) => k)}
            {#if activeFlags.length > 0}
              <div class="section">
                <div class="label">Flags</div>
                <div class="flags">
                  {#each activeFlags as flag}
                    <span class="flag">{flag.replace(/_/g, ' ')}</span>
                  {/each}
                </div>
              </div>
            {/if}
          {/if}

          <div class="section">
            <div class="label">Suggested response</div>
            <div class="content">{item.suggestion}</div>
          </div>

          <div class="actions">
            <button class="approve" on:click={() => onApprove(item)}>Approve and send</button>
            <button class="discard" on:click={() => onDiscard(item)}>Discard</button>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</aside>

<style>
  aside {
    width: 300px;
    flex-shrink: 0;
    border-left: 1px solid var(--c-border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .header {
    padding: 14px 16px;
    border-bottom: 1px solid var(--c-border);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .title {
    font-size: 15px;
    font-weight: 600;
    color: var(--c-t1);
  }

  .kill-btn {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid var(--c-ok-b);
    background: var(--c-ok-s);
    color: var(--c-ok);
    cursor: pointer;
    letter-spacing: 0.03em;
  }

  .kill-btn.kill-active {
    border-color: var(--c-red-b);
    background: var(--c-red-s);
    color: var(--c-red);
  }

  .kill-btn:hover { opacity: 0.85; }

  .badge {
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 20px;
    background: var(--c-warn-s);
    color: var(--c-warn);
    border: 1px solid var(--c-warn-b);
    font-weight: 600;
  }

  .body {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--c-t2);
    font-size: 13px;
    text-align: center;
    padding: 2rem;
  }

  .card {
    background: var(--c-tile);
    border: 1px solid var(--c-border);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .section { display: flex; flex-direction: column; gap: 4px; }

  .label {
    font-size: 10px;
    color: var(--c-t2);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .content {
    font-size: 13px;
    color: var(--c-t1);
    background: var(--c-row);
    border: 1px solid var(--c-border);
    border-radius: 8px;
    padding: 8px 10px;
    line-height: 1.5;
  }

  .flags { display: flex; flex-wrap: wrap; gap: 4px; }

  .flag {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    background: var(--c-red-s);
    color: var(--c-red);
    border: 1px solid var(--c-red-b);
    text-transform: capitalize;
  }

  .actions { display: flex; gap: 6px; }

  .approve {
    flex: 1;
    padding: 7px;
    border-radius: 20px;
    border: 1px solid var(--c-ok-b);
    background: var(--c-ok-s);
    color: var(--c-ok);
    font-size: 12px;
    cursor: pointer;
  }

  .approve:hover { opacity: 0.8; }

  .discard {
    flex: 1;
    padding: 7px;
    border-radius: 20px;
    border: 1px solid var(--c-red-b);
    background: var(--c-red-s);
    color: var(--c-red);
    font-size: 12px;
    cursor: pointer;
  }

  .discard:hover { opacity: 0.8; }

  .age {
    font-size: 10px;
    font-weight: 600;
    color: var(--c-t2);
    letter-spacing: 0.04em;
  }
  .age.warn    { color: var(--c-warn); }
  .age.overdue { color: var(--c-red); }
</style>
