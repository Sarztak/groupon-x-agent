<script>
  export let mode = 'deal_drop'
  export let onRun

  const modes = [
    { id: 'deal_drop',    label: 'Deal drop' },
    { id: 'trend_hook',   label: 'Trend hook' },
    { id: 'mention_reply', label: 'Mention reply' },
  ]
</script>

<header>
  <div class="logo">
    <img src="/src/assets/groupon-logo.svg" alt="Groupon" height="28" />
  </div>

  <div class="mode-group">
    <span class="label">Mode</span>
    <div class="btn-group">
      {#each modes as m}
        <button
          class="mode-btn"
          class:active={mode === m.id}
          on:click={() => mode = m.id}
        >{m.label}</button>
      {/each}
    </div>
  </div>

  <button class="run-btn" on:click={onRun}>
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
      <polygon points="3,1 13,7 3,13"/>
    </svg>
    Run
  </button>
</header>

<style>
  header {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 0 20px;
    height: 56px;
    background: #16181c;
    border-bottom: 1px solid #2f3336;
    flex-shrink: 0;
    flex-wrap: wrap;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-right: 8px;
  }

  .logo-text {
    font-size: 15px;
    font-size: 35px;
    font-weight: 600;
    color: #22c55e;
    white-space: nowrap;
  }

  .mode-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .label {
    font-size: 12px;
    color: #71767b;
    white-space: nowrap;
  }

  .btn-group {
    display: flex;
    gap: 4px;
  }

  .mode-btn {
    font-size: 13px;
    padding: 5px 12px;
    border-radius: 20px;
    border: 1px solid #2f3336;
    background: transparent;
    color: #e7e9ea;
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
  }

  .mode-btn:hover { background: #1d1f23; }

  .mode-btn.active {
    background: #16a34a;
    border-color: #16a34a;
    color: white;
  }


  select {
    font-size: 13px;
    padding: 5px 10px;
    border-radius: 20px;
    border: 1px solid #2f3336;
    background: #16181c;
    color: #e7e9ea;
    cursor: pointer;
  }

  .run-btn {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    padding: 7px 18px;
    border-radius: 20px;
    border: none;
    background: #16a34a;
    color: white;
    cursor: pointer;
    white-space: nowrap;
  }

  .run-btn:hover { background: #15803d; }
</style>
