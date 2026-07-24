<script>
  export let items = []
  export let onApprove
  export let onDiscard
</script>

<aside>
  <div class="header">
    <span class="title">Human review</span>
    {#if items.length > 0}
      <span class="badge">{items.length}</span>
    {/if}
  </div>

  <div class="body">
    {#if items.length === 0}
      <div class="empty">No pending items</div>
    {:else}
      {#each items as item (item.id)}
        <div class="card">
          <div class="section">
            <div class="label">Incoming</div>
            <div class="content">{item.input}</div>
          </div>

          <div class="section">
            <div class="label">Reason</div>
            <div class="content">{item.reason}</div>
          </div>

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
    gap: 8px;
    flex-shrink: 0;
  }

  .title {
    font-size: 15px;
    font-weight: 600;
    color: #e7e9ea;
  }

  .badge {
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 20px;
    background: #ffd40022;
    color: #ffd400;
    border: 1px solid #ffd40044;
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
    color: #71767b;
    font-size: 13px;
    text-align: center;
    padding: 2rem;
  }

  .card {
    background: #1d1f23;
    border: 1px solid #2f3336;
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .section { display: flex; flex-direction: column; gap: 4px; }

  .label {
    font-size: 10px;
    color: #71767b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .content {
    font-size: 13px;
    color: #e7e9ea;
    background: #16181c;
    border: 1px solid #2f3336;
    border-radius: 8px;
    padding: 8px 10px;
    line-height: 1.5;
  }

  .actions { display: flex; gap: 6px; }

  .approve {
    flex: 1;
    padding: 7px;
    border-radius: 20px;
    border: 1px solid #00b87a44;
    background: #1a3a2a;
    color: #00b87a;
    font-size: 12px;
    cursor: pointer;
  }

  .approve:hover { background: #1f4a34; }

  .discard {
    flex: 1;
    padding: 7px;
    border-radius: 20px;
    border: 1px solid #f4212e44;
    background: #3a1a1a;
    color: #f4212e;
    font-size: 12px;
    cursor: pointer;
  }

  .discard:hover { background: #4a2020; }
</style>
