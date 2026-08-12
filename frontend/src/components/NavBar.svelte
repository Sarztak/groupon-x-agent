<script>
  export let active = 'demo'
  export let onTabChange = () => {}
  export let theme = 'dark'
  export let toggleTheme = () => {}

  const tabs = [
    { id: 'demo',         label: 'Demo' },
    { id: 'impact',       label: 'Impact' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'content',      label: 'Content' },
  ]
</script>

<nav class="navbar">
  <div class="brand">Groupon X Agent</div>
  <div class="tabs">
    {#each tabs as tab}
      <button
        class="tab"
        class:active={active === tab.id}
        on:click={() => onTabChange(tab.id)}
      >
        {tab.label}
      </button>
    {/each}
  </div>
  <button class="theme-btn" on:click={toggleTheme} title="Toggle theme">
    {theme === 'dark' ? '☀' : '☾'}
  </button>
</nav>

<style>
  .navbar {
    display: flex;
    align-items: center;
    padding: 0 20px;
    border-bottom: 1px solid var(--c-border);
    height: 48px;
    flex-shrink: 0;
    gap: 32px;
    background: var(--c-bg);
  }

  .brand {
    font-size: 13px;
    font-weight: 700;
    color: var(--c-t1);
    letter-spacing: -0.01em;
    white-space: nowrap;
  }

  .tabs {
    display: flex;
    height: 100%;
    flex: 1;
  }

  .tab {
    background: none;
    border: none;
    color: var(--c-t2);
    font-size: 14px;
    padding: 0 16px;
    height: 100%;
    cursor: pointer;
    position: relative;
    transition: color 0.15s;
    white-space: nowrap;
  }

  .tab:hover { color: var(--c-t1); }

  .tab.active {
    color: var(--c-t1);
    font-weight: 500;
  }

  .tab.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 16px;
    right: 16px;
    height: 2px;
    background: var(--c-green);
    border-radius: 2px 2px 0 0;
  }

  .theme-btn {
    margin-left: auto;
    background: none;
    border: 1px solid var(--c-border);
    color: var(--c-t2);
    font-size: 15px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s, border-color 0.15s;
    flex-shrink: 0;
    line-height: 1;
  }

  .theme-btn:hover {
    color: var(--c-t1);
    border-color: var(--c-t2);
  }
</style>
