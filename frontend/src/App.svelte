<script>
  import NavBar from './components/NavBar.svelte'
  import Controls from './components/Controls.svelte'
  import ChatView from './components/ChatView.svelte'
  import ReviewView from './components/ReviewView.svelte'
  import ImpactView from './components/ImpactView.svelte'
  import ArchitectureView from './components/ArchitectureView.svelte'
  import ContentView from './components/ContentView.svelte'

  let activeTab = 'demo'

  let theme = (typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null) ?? 'dark'
  if (typeof document !== 'undefined') document.documentElement.setAttribute('data-theme', theme)

  function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }

  let mode = 'deal_drop'

  let messages = []
  let reviewItems = []
  let nextId = 0

  function addMessage(text, direction, meta = null) {
    messages = [...messages, { type: 'message', text, direction, meta, id: nextId++ }]
  }

  function addPill(text, variant) {
    messages = [...messages, { type: 'pill', text, variant, id: nextId++ }]
  }

  async function handleRun() {
    if (mode === 'deal_drop') {
      addPill('Deal drop triggered', 'routing')

      let result
      try {
        const res = await fetch('/api/deal_drop', { method: 'POST' })
        result = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }

      if (result.status === 'posted') {
        addPill('Review passed', 'pass')
        addMessage(result.copy, 'outgoing', `Agent · deal drop · ${result.deal?.merchant_name ?? ''}`)
      } else if (result.status === 'paused') {
        addPill('Kill switch active', 'fail')
      } else {
        addPill('Failed — escalated', 'fail')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: 'Deal drop',
          reason: result.detail ?? 'Copy generation or output guard failed',
          guardReport: {},
          suggestion: '',
          createdAt: Date.now(),
        }]
      }
    }

    else if (mode === 'trend_hook') {
      addPill('Trend signal triggered', 'routing')

      let result
      try {
        const res = await fetch('/api/trend_drop', { method: 'POST' })
        result = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }

      if (result.status === 'posted') {
        addMessage(`${result.trend} is trending`, 'incoming', 'Trend signal')
        addPill('Deal matched', 'pass')
        addMessage(result.copy, 'outgoing', `Agent · trend hook · ${result.deal?.merchant_name ?? ''}`)
      } else if (result.status === 'paused') {
        addPill('Kill switch active', 'fail')
      } else if (result.status === 'no_match') {
        addMessage(`${result.trend} is trending`, 'incoming', 'Trend signal')
        addPill('No matching deal found', 'escalate')
      }
    }

    else if (mode === 'mention_reply') {
      let mention
      try {
        const res = await fetch('/api/random_mention')
        mention = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }
      await handleSend(mention.text, mention.username)
    }
  }

  async function handleSend(text, username = 'user') {
    if (mode === 'deal_drop') {
      addPill('Custom deal drop triggered', 'routing')
      addMessage(text, 'incoming', 'Custom URL')

      let result
      try {
        const res = await fetch('/api/custom_deal_drop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: text.trim() })
        })
        result = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }

      if (result.status === 'posted') {
        addPill('Review passed', 'pass')
        addMessage(result.copy, 'outgoing', `Agent · custom deal · ${result.deal?.merchant_name ?? ''}`)
      } else if (result.status === 'paused') {
        addPill('Kill switch active', 'fail')
      } else {
        addPill('Failed — escalated', 'fail')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: text,
          reason: result.detail ?? 'Copy generation or output guard failed',
          guardReport: {},
          suggestion: '',
          createdAt: Date.now(),
        }]
      }
    }

    else if (mode === 'mention_reply') {
      addMessage(text, 'incoming', '@' + username)
      addPill('Processing...', 'routing')

      let result
      try {
        const res = await fetch('/api/mention', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, username })
        })
        result = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }

      messages = messages.filter(m => !(m.type === 'pill' && m.text === 'Processing...'))

      if (result.status === 'posted') {
        addPill(`Route: ${result.route}`, 'pass')
        addMessage(result.reply, 'outgoing', 'Agent · mention reply')
        if (result.route === 'acknowledge') {
          reviewItems = [...reviewItems, {
            id: nextId++,
            input: text,
            reason: 'Complaint acknowledged — queued for human follow-up',
            guardReport: result.guard_report || {},
            suggestion: '',
            createdAt: Date.now(),
          }]
        }
      } else if (result.status === 'escalated') {
        addPill('Escalated to human review', 'escalate')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: text,
          reason: result.reason,
          guardReport: result.guard_report || {},
          suggestion: '',
          createdAt: Date.now(),
        }]
      } else if (result.status === 'paused') {
        addPill('Kill switch active', 'fail')
      }
    }

    else if (mode === 'trend_hook') {
      addMessage(text + ' is trending', 'incoming', 'Trend signal')
      addPill('Matching deal...', 'routing')

      let result
      try {
        const res = await fetch('/api/trend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trend: text })
        })
        result = await res.json()
      } catch (e) {
        addPill('API error', 'fail')
        return
      }

      messages = messages.filter(m => !(m.type === 'pill' && m.text === 'Matching deal...'))

      if (result.status === 'posted') {
        addPill('Deal matched', 'pass')
        addMessage(result.copy, 'outgoing', `Agent · trend hook · ${result.deal?.merchant_name ?? ''}`)
      } else if (result.status === 'no_match') {
        addPill('No matching deal found', 'escalate')
      }
    }
  }

  function handleApprove(item) {
    addMessage(item.suggestion, 'outgoing', 'Human approved · sent')
    reviewItems = reviewItems.filter(r => r.id !== item.id)
  }

  function handleDiscard(item) {
    reviewItems = reviewItems.filter(r => r.id !== item.id)
  }

  async function handleLoadHistory() {
    let data
    try {
      const res = await fetch('/api/two_week_plan')
      data = await res.json()
    } catch (e) {
      addPill('Could not load demo history', 'fail')
      return
    }
    if (!data.generated || !data.replies?.length) {
      addPill('No generated history — run generate_two_week_plan.py first', 'escalate')
      return
    }
    messages = []
    reviewItems = []

    for (const p of data.posts) {
      if (p.status !== 'ok') continue
      const merchant = p.type === 'trend_hook'
        ? (p.matched_deal?.merchant_name ?? p.trend)
        : p.deal?.merchant_name ?? ''
      const trendLabel = p.trend ? ` · ${p.trend}` : ''
      addPill(`${p.date} · ${p.type.replace('_', ' ')}${trendLabel}`, 'routing')
      addMessage(p.copy, 'outgoing', `Agent · ${p.type.replace('_', ' ')} · ${merchant}`)
    }

    for (const r of data.replies) {
      if (r.status !== 'ok') continue
      addMessage(r.text, 'incoming', `@${r.username}`)
      addPill(`Route: ${r.route}`, 'pass')
      addMessage(r.reply, 'outgoing', 'Agent · mention reply')
      if (r.route === 'acknowledge') {
        addPill('Queued for human follow-up', 'escalate')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: r.text,
          reason: 'Complaint acknowledged — queued for human follow-up',
          guardReport: r.guard_report || {},
          suggestion: r.reply,
          createdAt: Date.now(),
        }]
      }
    }

    addPill('Demo history loaded', 'pass')
  }
</script>

<div class="app">
  <NavBar active={activeTab} onTabChange={(t) => activeTab = t} {theme} {toggleTheme} />

  {#if activeTab === 'demo'}
    <Controls bind:mode onRun={handleRun} />
    <div class="body">
      <ChatView {messages} {mode} onSend={handleSend} onLoadHistory={handleLoadHistory} />
      <ReviewView items={reviewItems} onApprove={handleApprove} onDiscard={handleDiscard} />
    </div>

  {:else if activeTab === 'impact'}
    <ImpactView />

  {:else if activeTab === 'architecture'}
    <ArchitectureView />

  {:else if activeTab === 'content'}
    <ContentView />
  {/if}
</div>

<style>
  /* ── Color tokens ──────────────────────────────────────────────── */
  :global(:root) {
    /* Neutrals */
    --c-bg:      #000000;
    --c-panel:   #0e0f11;
    --c-tile:    #1d1f23;
    --c-row:     #16181c;
    --c-t1:      #e7e9ea;
    --c-t2:      #71767b;
    --c-t3:      #4b5563;
    --c-border:  #2f3336;
    --c-divider: #16181c;
    --c-input:   #1d1f23;
    /* Green */
    --c-green:   #22c55e;
    --c-green-s: #0d1f13;
    --c-green-b: #16a34a44;
    --c-btn:     #16a34a;
    --c-btn-hov: #15803d;
    /* Blue */
    --c-blue:    #60a5fa;
    --c-blue-s:  #0c1220;
    --c-blue-b:  #1e40af44;
    /* Yellow / amber */
    --c-yellow:  #f59e0b;
    --c-yellow-s:#1c1208;
    --c-yellow-b:#854d0e44;
    /* Purple */
    --c-purple:  #a78bfa;
    --c-purple-s:#120c20;
    --c-purple-b:#6d28d944;
    /* Red */
    --c-red:     #f4212e;
    --c-red-s:   #3a1a1a;
    --c-red-b:   #f4212e44;
    /* Cyan */
    --c-cyan:    #22d3ee;
    --c-cyan-s:  #061218;
    --c-cyan-b:  #0e749044;
    /* Orange */
    --c-orange:  #fb923c;
    --c-orange-s:#1a0e08;
    --c-orange-b:#9a341244;
    /* Light green */
    --c-lgreen:  #4ade80;
    --c-lgreen-s:#0a1a10;
    --c-lgreen-b:#16653444;
    /* Bright green (approve/live) */
    --c-ok:      #00b87a;
    --c-ok-s:    #1a3a2a;
    --c-ok-b:    #00b87a44;
    /* Warn / escalate */
    --c-warn:    #ffd400;
    --c-warn-s:  #3a2e1a;
    --c-warn-b:  #ffd40044;
    /* Link */
    --c-link:    #1d9bf0;
  }

  :global(:root[data-theme="light"]) {
    --c-bg:      #f4f6f8;
    --c-panel:   #ffffff;
    --c-tile:    #f0f2f5;
    --c-row:     #e8eaed;
    --c-t1:      #0f1419;
    --c-t2:      #536471;
    --c-t3:      #9ca3af;
    --c-border:  #cfd9de;
    --c-divider: #e8eaed;
    --c-input:   #ffffff;
    --c-green:   #16a34a;
    --c-green-s: #f0fdf4;
    --c-green-b: #16a34a44;
    --c-blue:    #2563eb;
    --c-blue-s:  #eff6ff;
    --c-blue-b:  #2563eb44;
    --c-yellow:  #d97706;
    --c-yellow-s:#fffbeb;
    --c-yellow-b:#d9770644;
    --c-purple:  #7c3aed;
    --c-purple-s:#f5f3ff;
    --c-purple-b:#7c3aed44;
    --c-red:     #dc2626;
    --c-red-s:   #fef2f2;
    --c-red-b:   #dc262644;
    --c-cyan:    #0891b2;
    --c-cyan-s:  #ecfeff;
    --c-cyan-b:  #0891b244;
    --c-orange:  #ea580c;
    --c-orange-s:#fff7ed;
    --c-orange-b:#ea580c44;
    --c-lgreen:  #16a34a;
    --c-lgreen-s:#f0fdf4;
    --c-lgreen-b:#16a34a44;
    --c-ok:      #059669;
    --c-ok-s:    #ecfdf5;
    --c-ok-b:    #05966944;
    --c-warn:    #ca8a04;
    --c-warn-s:  #fefce8;
    --c-warn-b:  #ca8a0444;
  }

  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }

  :global(body) {
    background: var(--c-bg);
    color: var(--c-t1);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    height: 100vh;
    overflow: hidden;
  }

  :global(#app) {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
</style>
