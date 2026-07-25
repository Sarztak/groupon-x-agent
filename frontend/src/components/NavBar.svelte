<script>
  export let active = 'demo'
  export let onTabChange = () => {}

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
</nav>

<style>
  .navbar {
    display: flex;
    align-items: center;
    padding: 0 20px;
    border-bottom: 1px solid #2f3336;
    height: 48px;
    flex-shrink: 0;
    gap: 32px;
    background: #000;
  }

  .brand {
    font-size: 13px;
    font-weight: 700;
    color: #e7e9ea;
    letter-spacing: -0.01em;
    white-space: nowrap;
  }

  .tabs {
    display: flex;
    height: 100%;
  }

  .tab {
    background: none;
    border: none;
    color: #71767b;
    font-size: 14px;
    padding: 0 16px;
    height: 100%;
    cursor: pointer;
    position: relative;
    transition: color 0.15s;
    white-space: nowrap;
  }

  .tab:hover { color: #e7e9ea; }

  .tab.active {
    color: #e7e9ea;
    font-weight: 500;
  }

  .tab.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 16px;
    right: 16px;
    height: 2px;
    background: #22c55e;
    border-radius: 2px 2px 0 0;
  }
</style>
