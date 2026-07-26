<script>
  import { afterUpdate } from 'svelte'

  export let messages = []
  export let mode
  export let onSend
  export let onLoadHistory = null

  let input = ''
  let viewport

  afterUpdate(() => {
    if (viewport) viewport.scrollTop = viewport.scrollHeight
  })

  function handleSend() {
    if (!input.trim()) return
    onSend(input.trim())
    input = ''
  }

  function handleKey(e) {
    if (e.key === 'Enter') handleSend()
  }

  $: placeholder = mode === 'deal_drop'
    ? 'Paste a Groupon deal URL for a custom drop, or click Run for random'
    : mode === 'trend_hook'
    ? 'No input needed — trends are auto-selected'
    : 'Type a custom mention...'

  function parseSegments(text) {
    const parts = []
    const re = /(https?:\/\/\S+)/g
    let last = 0, m
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push({ type: 'text', value: text.slice(last, m.index) })
      parts.push({ type: m[1].includes('/deals/') ? 'deal_url' : 'url', value: m[1] })
      last = m.index + m[1].length
    }
    if (last < text.length) parts.push({ type: 'text', value: text.slice(last) })
    return parts
  }
</script>

<div class="chat">
  <div class="messages" bind:this={viewport}>
    {#if messages.length === 0}
      <div class="empty">
        <div class="empty-inner">
          <div class="empty-text">Select a mode and click Run to start</div>
          {#if onLoadHistory}
            <button class="load-history-btn" on:click={onLoadHistory}>Load demo history</button>
          {/if}
        </div>
      </div>
    {/if}

    {#each messages as msg}
      {#if msg.type === 'pill'}
        <div class="pill {msg.variant}">{msg.text}</div>
      {:else}
        {@const segs = parseSegments(msg.text)}
        <div class="msg {msg.direction}">
          {#if msg.meta}
            <div class="meta">{msg.meta}</div>
          {/if}
          <div class="bubble">
            {#each segs as seg}
              {#if seg.type === 'text'}
                {seg.value}
              {:else if seg.type === 'deal_url'}
                <a class="deal-link inline-deal" href={seg.value} target="_blank" rel="noopener noreferrer">View deal →</a>
              {:else}
                {@const label = (() => { try { const u = new URL(seg.value); return (u.pathname && u.pathname !== '/') ? u.pathname.replace(/^\//, '') : u.hostname.replace('www.', '') } catch { return 'groupon.com' } })()}
                <a class="inline-link" href={seg.value} target="_blank" rel="noopener noreferrer">{label}</a>
              {/if}
            {/each}
          </div>
        </div>
      {/if}
    {/each}
  </div>

  <div class="input-row">
    <input
      type="text"
      bind:value={input}
      {placeholder}
      on:keydown={handleKey}
      disabled={mode === 'trend_hook'}
    />
    <button on:click={handleSend} disabled={mode === 'trend_hook'}>Send</button>
  </div>
</div>

<style>
  .chat {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
    min-width: 0;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem;
  }

  .empty-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
  }

  .empty-text {
    color: #71767b;
    font-size: 14px;
    text-align: center;
  }

  .load-history-btn {
    font-size: 12px;
    padding: 6px 16px;
    border-radius: 20px;
    border: 1px solid #2f3336;
    background: transparent;
    color: #71767b;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .load-history-btn:hover {
    color: #e7e9ea;
    border-color: #4b5563;
    background: transparent;
  }

  .msg {
    display: flex;
    flex-direction: column;
    gap: 3px;
    max-width: 55%;
  }

  .msg.incoming { align-self: flex-start; }
  .msg.outgoing { align-self: flex-end; align-items: flex-end; }

  .meta {
    font-size: 11px;
    color: #71767b;
    padding: 0 4px;
  }

  .bubble {
    padding: 10px 14px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.5;
  }

  .deal-link {
    display: block;
    margin-top: 8px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    opacity: 0.85;
  }

  .deal-link.inline-deal {
    display: inline;
    margin-top: 0;
    font-size: inherit;
  }

  .msg.outgoing .deal-link {
    color: rgba(255,255,255,0.9);
    border-top: 1px solid rgba(255,255,255,0.2);
    padding-top: 6px;
  }

  .msg.incoming .deal-link {
    color: #1d9bf0;
    border-top: 1px solid #2f3336;
    padding-top: 6px;
  }

  .deal-link:hover { opacity: 1; text-decoration: underline; }

  .inline-link {
    color: #1d9bf0;
    text-decoration: underline;
    font-size: inherit;
  }

  .msg.outgoing .inline-link { color: rgba(255,255,255,0.85); }

  .msg.incoming .bubble {
    background: #1d1f23;
    border: 1px solid #2f3336;
    color: #e7e9ea;
    border-bottom-left-radius: 4px;
  }

  .msg.outgoing .bubble {
    background: #16a34a;
    color: white;
    border-bottom-right-radius: 4px;
  }

  .pill {
    align-self: center;
    font-size: 11px;
    padding: 3px 12px;
    border-radius: 20px;
  }

  .pill.pass { background: #1a3a2a; color: #00b87a; border: 1px solid #00b87a44; }
  .pill.fail { background: #3a1a1a; color: #f4212e; border: 1px solid #f4212e44; }
  .pill.escalate { background: #3a2e1a; color: #ffd400; border: 1px solid #ffd40044; }
  .pill.routing { background: #1d1f23; color: #71767b; border: 1px solid #2f3336; }

  .input-row {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid #2f3336;
  }

  input {
    flex: 1;
    font-size: 14px;
    padding: 9px 14px;
    border-radius: 20px;
    border: 1px solid #2f3336;
    background: #1d1f23;
    color: #e7e9ea;
  }

  input::placeholder { color: #71767b; }
  input:disabled { opacity: 0.4; cursor: not-allowed; }

  button {
    font-size: 14px;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: 20px;
    border: none;
    background: #16a34a;
    color: white;
    cursor: pointer;
  }

  button:hover { background: #15803d; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
