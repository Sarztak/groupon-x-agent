<script>
  import Controls from './components/Controls.svelte'
  import ChatView from './components/ChatView.svelte'
  import ReviewView from './components/ReviewView.svelte'

  let mode = 'deal_drop'
  let segment = 'spontaneous_locals'
  let variations = 1

  let messages = []
  let reviewItems = []
  let nextId = 0

  function addMessage(text, direction, meta = null) {
    messages = [...messages, { type: 'message', text, direction, meta, id: nextId++ }]
  }

  function addPill(text, variant) {
    messages = [...messages, { type: 'pill', text, variant, id: nextId++ }]
  }

  function delay(ms) {
    return new Promise(r => setTimeout(r, ms))
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
      } else {
        addPill('Failed — escalated', 'fail')
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
      } else if (result.status === 'no_match') {
        addMessage(`${result.trend} is trending`, 'incoming', 'Trend signal')
        addPill('No matching deal found', 'escalate')
      }
    }

    else if (mode === 'mention_reply') {
      addPill('Type a mention in the input below', 'routing')
    }
  }

  async function handleSend(text) {
    if (mode === 'mention_reply') {
      addMessage(text, 'incoming', 'Custom mention')
      addPill('Processing...', 'routing')

      let result
      try {
        const res = await fetch('/api/mention', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, username: 'user' })
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
            suggestion: ''
          }]
        }
      } else if (result.status === 'escalated') {
        addPill('Escalated to human review', 'escalate')
        reviewItems = [...reviewItems, {
          id: nextId++,
          input: text,
          reason: result.reason,
          guardReport: result.guard_report || {},
          suggestion: ''
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
</script>

<div class="app">
  <Controls
    bind:mode
    bind:segment
    bind:variations
    onRun={handleRun}
  />

  <div class="body">
    <ChatView
      {messages}
      {mode}
      onSend={handleSend}
    />

    <ReviewView
      items={reviewItems}
      onApprove={handleApprove}
      onDiscard={handleDiscard}
    />
  </div>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }

  :global(body) {
    background: #000000;
    color: #e7e9ea;
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
