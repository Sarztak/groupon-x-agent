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
      await delay(1000)
      addPill('Review passed', 'pass')
      addMessage(
        'Pittsburgh, your shoulders called. Honor Your Body Wellness has been waiting. Up to 52% off personalized therapeutic massages — deep tissue, Swedish, or couples. Book on Groupon.',
        'outgoing', 'Agent · deal drop'
      )
    }

    else if (mode === 'trend_hook') {
      addMessage('#SelfCareSunday is trending · 85,000 tweets', 'incoming', 'Trend signal')
      await delay(900)
      addPill('Matched: King Spa Chicago', 'routing')
      await delay(900)
      addPill('Review passed', 'pass')
      addMessage(
        "It's Sunday. King Spa Chicago has heated pools, sauna rooms, and a plunge. Open 24/7. All-day admission on Groupon.",
        'outgoing', 'Agent · trend hook'
      )
    }

    else if (mode === 'mention_reply') {
      addMessage('@Groupon any good spa deals in Chicago this weekend?', 'incoming', '@sarah_chicago')
      await delay(700)
      addPill('Guard passed', 'pass')
      await delay(800)
      addPill('Review passed', 'pass')
      addMessage(
        '@sarah_chicago King Spa Chicago — heated pools, sauna rooms, scrubs. All day, any time. On Groupon right now.',
        'outgoing', 'Agent · mention reply'
      )
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
      addMessage(text + ' is trending', 'incoming', 'Custom trend')
      await delay(600)
      addPill('Matching deal...', 'routing')
      await delay(900)
      addPill('Review passed', 'pass')
      addMessage(
        'Something worth leaving the house for is happening in your city. Find it on Groupon.',
        'outgoing', 'Agent · trend hook'
      )
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
